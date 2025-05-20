import bids2table as b2t
import pandas as pd

base_dir = "/ocean/projects/med250004p/shared/regression_outputs_v1.8.7/default/site-1/sub-A00040524/output/pipeline_cpac-default-pipeline"
subjects = []
tab = b2t.index_dataset(root=base_dir, include_subjects=subjects, show_progress=True)
df = tab.to_pandas(types_mapper=pd.ArrowDtype)
print(df.columns)
df.to_csv("index.csv", index=False)