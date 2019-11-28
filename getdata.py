import json
from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory

client = API(access_token='82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43')
instrument, granularity = "EUR_USD", "S30"
_from = "2019-10-31T00:00:00Z"
params = {
   "from": _from,
   "granularity": granularity,
   "count": 5000,
   "price":"BA"
}
with open(r'C:\Users\vcucu\Documents\KTH_Q1\II2202 Research Methodology and Scientific Writing\tmp\{}_{}.json'.format(instrument, granularity), "w") as OUT:
    # The factory returns a generator generating consecutive
    # requests to retrieve full history from date 'from' till 'to'
    for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
         client.request(r)
         OUT.write(json.dumps(r.response.get('candles'), indent=2))
