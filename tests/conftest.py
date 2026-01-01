import sys
from pathlib import Path
import pandas as pd

# look in this directory first when importing modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pd.set_option("display.width", None)