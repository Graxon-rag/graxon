import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Uuid, JSON, TIMESTAMP, Integer
import datetime


class Base(DeclarativeBase):
    pass