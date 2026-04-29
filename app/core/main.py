import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .load_imp_env import load_imp_env
from fastapi.openapi.docs import get_swagger_ui_html
import asyncio


# Routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    yield


app = FastAPI(title="Graxon API", version="1.0", lifespan=lifespan, docs_url=None, redoc_url=None)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

load_dotenv()
load_imp_env()

# CORS middleware
# CLIENTS = os.getenv("CLIENTS", "").split(",")
# CLIENTS = [url.strip() for url in CLIENTS if url.strip()]

# print("CLIENTS: ", CLIENTS)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=CLIENTS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


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


@app.get("/")
def index():
    return {"Graxon server is running, you can go to /docs for the documentation"}
