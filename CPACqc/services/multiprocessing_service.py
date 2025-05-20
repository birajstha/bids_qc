from typing import Callable, Iterable, Any, List

class MultiprocessingService:
    def run(self, func: Callable, args: Iterable, n_procs: int) -> List[Any]:
        raise NotImplementedError