from typing import Callable, Iterable, Any, List

class MultiprocessingPort:
    def run(self, func: Callable, args: Iterable, n_procs: int) -> List[Any]:
        raise NotImplementedError