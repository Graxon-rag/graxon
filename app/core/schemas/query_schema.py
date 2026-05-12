from enum import Enum


class QueryType(str, Enum):
    QUICK = "quick"
    SMART = "smart"
    EXPERT = "expert"
