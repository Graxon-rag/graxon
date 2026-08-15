from pydantic import BaseModel


class PaginationSchema(BaseModel):
    total_pages: int
    current_page: int
    current_limit: int
