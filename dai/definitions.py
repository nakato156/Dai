import typing as t

RESET = "\033[0m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"

T = t.TypeVar('T', bound=t.Callable[[t.Dict[str, t.Any], t.List[int]], t.Awaitable[None]])
