import logging
import pandas as pd
import numpy as np #needed for NaN handling
import math #ceil and floor are useful for rounding
from datetime import datetime, timedelta
from itertools import cycle
from get_stock_data import pipeliner as pipe
from friartuck.api import OrderType


stock_boi = pipe()
stock_frame = stock_boi.import_data()
print (stock_frame.head(20), stock_frame.info())