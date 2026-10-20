from collections.abc import Callable
from typing import ParamSpec, Protocol, TypeVar, cast

from slowapi import Limiter
from slowapi.util import get_remote_address

P = ParamSpec("P")
R = TypeVar("R")


class TypedLimiter(Protocol):
    def limit(self, limit_value: str) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


limiter = Limiter(key_func=get_remote_address)


def rate_limit(
    limit_value: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    typed_limiter = cast(TypedLimiter, limiter)
    return typed_limiter.limit(limit_value)
