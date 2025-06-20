from typing import Callable, TypeVar, Optional, Iterable

T = TypeVar('T')

def find(filter_fn: Callable[[T], bool], collection: Iterable[T]) -> Optional[T]:
    try:
        return next(filter(filter_fn, collection))
    except StopIteration:
        return None


def response_example(example: T) -> dict[int, dict]:
    return {
        200: {
            "content": {
                "application/json": {
                    "example": example
                }
            }
        }
    }