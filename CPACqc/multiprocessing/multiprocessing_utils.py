from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from colorama import Fore, Style

from CPACqc.logging.log import logger

def run_multiprocessing(func, args, n_procs):
    not_plotted = []
    with ProcessPoolExecutor(max_workers=n_procs) as executor:
        futures = {executor.submit(func, arg): arg for arg in args}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing ..."):
            try:
                result = future.result()
                logger.info(f"Successfully processed {futures[future]}: {result}")
            except Exception as e:
                if "terminated abruptly" in str(e):
                    print(Fore.RED + f"Error processing {futures[future]}: {e}\n Try with lower number of processes" + Style.RESET_ALL)
                logger.error(f"Error processing {futures[future]}: {e}, Try with a lower number of processes")
                not_plotted.append(futures[future])
    return not_plotted