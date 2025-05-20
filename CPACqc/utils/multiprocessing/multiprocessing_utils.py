from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from colorama import Fore, Style
from typing import Callable, Iterable, Any, List

from CPACqc.services.multiprocessing_service import MultiprocessingService
from CPACqc.core.logger import logger

class Multiprocess(MultiprocessingService):
    def __init__(self, func, args, n_procs):
        self.func = func
        self.args = args
        self.n_procs = n_procs
        self.not_plotted = []

    def run(self) -> List[Any]:
        with ProcessPoolExecutor(max_workers=self.n_procs) as executor:
            futures = {executor.submit(self.func, arg): arg for arg in self.args}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing ..."):
                try:
                    result = future.result()
                    logger.info(f"Successfully processed {futures[future]}: {result}")
                except Exception as e:
                    if "terminated abruptly" in str(e):
                        print(Fore.RED + f"Error processing {futures[future]}: {e}\n Try with lower number of processes" + Style.RESET_ALL)
                    self.not_plotted.append(futures[future])
        return self.not_plotted