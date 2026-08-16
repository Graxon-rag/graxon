from .rabbitmq.consumer import GMQDocumentConsumer, GMQWebhookConsumer
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .databases.postgresql.client import GPostgresqlClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .databases.qdrant.client import GQdrantClient
from .databases.minio.client import GMinioClient
from .databases.redis.client import GRedisClient
from .databases.neo4j.client import GNeo4jClient
from slowapi.errors import RateLimitExceeded
from .rabbitmq.client import GRabbitMQClient
from slowapi.util import get_remote_address
from .test_something import test_something
from contextlib import asynccontextmanager
from .load_imp_env import load_imp_env
from .seed import SeedDefaultData
from dotenv import load_dotenv
import asyncio
import json
import os


# Routes
from .routes.reranker_route import router as reranker_router
from .routes.sparse_text_model_route import router as sparse_text_model_router
from .routes.model_provider_route import router as model_provider_router
from .routes.model_credential_route import router as model_credential_router
from .routes.llm_model_route import router as llm_model_router
from .routes.embedding_model_route import router as embedding_model_router
from .routes.org_route import router as org_router
from .routes.project_route import router as project_router
from .routes.document_route import router as document_router
from .routes.query_route import router as query_router
from .routes.graph_route import router as graph_router
from .routes.audio_model_route import router as audio_model_router
from .routes.video_model_route import router as video_model_router
from .routes.ocr_model_route import router as ocr_model_router
from .routes.webhook_route import router as webhook_router
from .routes.project_config_route import router as project_config_router


load_dotenv()
load_imp_env()

DOCUMENT_CONSUMER_COUNT = int(os.getenv("DOCUMENT_CONSUMER_COUNT", 5))
print("DOCUMENT_CONSUMER_COUNT: ", DOCUMENT_CONSUMER_COUNT)

WEBHOOK_CONSUMER_COUNT = int(os.getenv("WEBHOOK_CONSUMER_COUNT", 2))
print("WEBHOOK_CONSUMER_COUNT: ", WEBHOOK_CONSUMER_COUNT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---

    await asyncio.gather(
        GMinioClient.init(),
        GPostgresqlClient.init(),
        GRedisClient.init(),
        GNeo4jClient.init(),
        GQdrantClient.init(),
        GRabbitMQClient.init()
    )
    doc_consumers = [GMQDocumentConsumer() for _ in range(DOCUMENT_CONSUMER_COUNT)]
    tasks = [asyncio.create_task(c.consume_document_processing_queue()) for c in doc_consumers]

    # Start One Consumer for Document Status
    tasks.append(asyncio.create_task(GMQDocumentConsumer().consume_document_status_queue()))

    webhook_consumers = [GMQWebhookConsumer() for _ in range(WEBHOOK_CONSUMER_COUNT)]
    tasks.extend([asyncio.create_task(c.consume_webhook_queue()) for c in webhook_consumers])

    await SeedDefaultData().seed()

    yield

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    await asyncio.gather(
        GRedisClient.close(),
        GNeo4jClient.close(),
        GQdrantClient.close(),
        GRabbitMQClient.close()
    )


app = FastAPI(title="Graxon API", version="1.0", lifespan=lifespan, docs_url=None, redoc_url=None)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


# CORS middleware
CLIENTS = os.getenv("CLIENTS", "").split(",")
CLIENTS = [url.strip() for url in CLIENTS if url.strip()]

print("CLIENTS: ", CLIENTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CLIENTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


security = HTTPBasic()
docs_username = os.getenv("DOCS_USERNAME")
docs_password = os.getenv("DOCS_PASSWORD")


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != docs_username or credentials.password != docs_password:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Use fastapi_app instead of app to access openapi_url
    return get_swagger_ui_html(openapi_url=str(app.openapi_url), title="docs")


# Routes
app.include_router(reranker_router, prefix="/api/rerankers")
app.include_router(sparse_text_model_router, prefix="/api/sparse-text-models")
app.include_router(model_provider_router, prefix="/api/model-providers")
app.include_router(model_credential_router, prefix="/api/model-credentials")
app.include_router(llm_model_router, prefix="/api/llm-models")
app.include_router(embedding_model_router, prefix="/api/embedding-models")
app.include_router(org_router, prefix="/api/orgs")
app.include_router(project_router, prefix="/api/projects")
app.include_router(document_router, prefix="/api/documents")
app.include_router(query_router, prefix="/api/query")
app.include_router(graph_router, prefix="/api/graphs")
app.include_router(audio_model_router, prefix="/api/audio-models")
app.include_router(video_model_router, prefix="/api/video-models")
app.include_router(ocr_model_router, prefix="/api/ocr-models")
app.include_router(webhook_router, prefix="/api/webhooks")
app.include_router(project_config_router, prefix="/api/project-configs")


@app.get("/")
def index():
    return {"Graxon server is running, you can go to /docs for the documentation"}


@app.post("/test")
async def test():
    return await test_something()


@app.post("/openapi-docs")
async def make_docs():
    # Get the OpenAPI schema
    openapi_schema = app.openapi()

    # Define the target directory and file path
    docs_dir = "docs"
    file_path = os.path.join(docs_dir, "openapi.json")

    # Create the directory if it does not exist
    os.makedirs(docs_dir, exist_ok=True)

    # Save the schema to the file
    with open(file_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"{file_path} generated successfully!")
    return {"message": f"{file_path} generated successfully!"}
