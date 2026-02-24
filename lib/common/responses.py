# lib/common/response.py

from dataclasses import dataclass
from typing import Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar("T")


@dataclass
class Response(Generic[T]):
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: str = datetime.utcnow().isoformat()

    @staticmethod
    def ok(data: T = None, message: str = "Success"):
        return Response(success=True, message=message, data=data, error=None)

    @staticmethod
    def fail(error: str, message: str = "Failed"):
        return Response(success=False, message=message, data=None, error=error)
