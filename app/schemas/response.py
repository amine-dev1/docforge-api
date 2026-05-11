from pydantic import BaseModel
from typing import Generic, TypeVar, Any

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    status: int = 200
    data: T
