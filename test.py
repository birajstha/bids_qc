import bids2table as b2t
import pandas as pd

base_dir = "/ocean/projects/med220004p/shared/data_raw"
subjects = ["sub-PA001", "sub-PA002"]
tab = b2t.index_dataset(root=base_dir, include_subjects=subjects, show_progress=True)
df = tab.to_pandas(types_mapper=pd.ArrowDtype)
print(df.columns)