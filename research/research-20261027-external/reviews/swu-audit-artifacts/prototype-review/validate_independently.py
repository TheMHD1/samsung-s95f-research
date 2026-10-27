import importlib.util
from pathlib import Path
p=Path('${S95F_EVIDENCE_ROOT}/research-20261027-external/sources/minimal-swu-helper/offline_validate.py')
s=importlib.util.spec_from_file_location('prototype_validation',p)
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
# Inputs resolve from the original module's pinned research root; execute only
# this review's separately built host mock, with all outputs confined here.
v.HERE=Path(__file__).resolve().parent
v.main()
