import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import MarketOrderRequest
import pandas as pd
import numpy as np

access_token = '82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43'
accountID = "101-004-12401398-001"
client = oandapyV20.API(access_token=access_token)
