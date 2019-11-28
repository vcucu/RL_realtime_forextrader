#import configparser  # 1
#import oandapy as opy  # 2
#from oandapy import APIv20
#from oandapy.exceptions import OandaError

#import oandapyV20
import json
from oandapyV20 import API
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.instruments as instruments

#config = configparser.ConfigParser()  # 3
#config.read('oanda.cfg')  # 4

accountID = '101-004-12401398-001'
api = oandapyV20.API(environment='practice',
                access_token='82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43')  # 5


r = trades.TradesList(accountID)
# show the endpoint as it is constructed for this call
print("REQUEST:{}".format(r))
rv = api.request(r)
print("RESPONSE:\n{}".format(json.dumps(rv, indent=2)))

import pandas as pd  # 6

#data = oanda.get_history(instrument='EUR_USD',  # our instrument
#                         start='2016-12-08',  # start data
#                         end='2016-12-10',  # end date
#                         granularity='M1')  # minute bars  # 7

#df = pd.DataFrame(data['candles']).set_index('time')  # 8

#df.index = pd.DatetimeIndex(df.index)  # 9

#df.info() # 10

"""params = {
  #"count": 5,
  "granularity": "M1",
  "from": "2017-06-23T12:00:00Z",
  "to":"2017-06-25T12:00:00Z"
}
r = instruments.InstrumentsCandles(instrument="EUR_USD", params=params)
oanda.request(r)
print(json.dumps(r.response, indent=2))"""


"""
try:
    result = con.account.get_accounts()
 # In case of http status 400
except OandaError as exc:
     print(str(exc))

 # Use the result as object
print(result.as_obj())
MyModel(accounts=[NamelessModel(tags=[], id='101-004-12401398-002')])

 # Use the result as dict
print(result.as_dict())
{'accounts': [{'id': '101-004-12401398-002', 'tags': []}]}
"""
