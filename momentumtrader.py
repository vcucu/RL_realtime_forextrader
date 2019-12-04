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


class MomentumTrader(pricing.PricingStream):
    def __init__(self, momentum, *args, **kwargs):
        pricing.PricingStream.__init__(self, *args, **kwargs)
        self.ticks = 0
        self.position = 0
        self.df = pd.DataFrame()
        self.momentum = momentum
        self.units = 1000
    def create_order(self, side, units):
        #negative side  = selling, positive = buying
        if side == "sell":
            units = units*-1
        mo = MarketOrderRequest(instrument="EUR_USD", units=units)
        r = orders.OrderCreate(accountID, data=mo.data)
        print("making trade")
        client.request(r)
        print(r.response)

    def on_success(self, data):  # 36
        #print(self.df.to_string())
        self.ticks += 1  # 37
        print(self.ticks, end=', ')
        print(pd.DataFrame(data,index=[data['time']]).to_string())
        # appends the new tick data to the DataFrame object
        self.df = self.df.append(pd.DataFrame(data,
                                 index=[data['time']]))  # 38
        # transforms the time information to a DatetimeIndex object
        self.df.index = pd.DatetimeIndex(self.df['time'])  # 39
        # resamples the data set to a new, homogeneous interval, as in aggregates info to every 15 sec
        dfr = self.df.resample('10s').pad()  # 40#.last()
        print("df", self.df.to_string())
        print("dfr", dfr.to_string())
        # calculates the log returns
        dfr['closeoutAsk'] = dfr['closeoutAsk'].astype('float')
        dfr['returns'] = np.log(dfr['closeoutAsk'] / dfr['closeoutAsk'].shift(1))  # 41
        # derives the positioning according to the momentum strategy
        print("mom", self.momentum, "roll", dfr['returns'].rolling(10).mean().to_string())
        #print("to be signed:", str(dfr['returns'].rolling(
        #                              self.momentum).mean()))
        #print(type(dfr['returns'].rolling(
        #                              self.momentum).mean()))
        print()
        dfr['position'] = np.sign(dfr['returns'].rolling(
                                      self.momentum).mean())  # 42
        #print(dfr[-1].to_string())
        print("positions ", dfr['position'].iloc[-1], self.position)
        if dfr['position'].iloc[-1] == 1:  # 43
            # go long
            if self.position == 0:  # 44
                self.create_order('buy', self.units)  # 45
            elif self.position == -1:  # 46
                self.create_order('buy', self.units * 2)  # 47
            self.position = 1  # 48
        elif dfr['position'].iloc[-1] == -1:  # 49
            # go short
            if self.position == 0:  # 50
                self.create_order('sell', self.units)  # 51
            elif self.position == 1: # 52
                self.create_order('sell', self.units * 2)  # 53
            self.position = -1  # 54
        if self.ticks == 2500:  # 55
            # close out the position
            if self.position == 1:  # 56
                self.create_order('sell', self.units)  # 57
            elif self.position == -1:  # 58
                self.create_order('buy', self.units)  # 59
            #self.disconnect()  # 60
            self.terminate()

# setup the stream request

params = {"instruments": "EUR_USD", "timeout": "5"}
#r = pricing.PricingStream(accountID=accountID, params=params)
#rv = client.request(r)
#maxrecs = 100
#for ticks in r:
#    print json.dumps(R, indent=4),","
#        r.terminate('maxrecs records received')

mt = MomentumTrader(momentum=12,accountID=accountID, params=params)
rv = client.request(mt)
for tick in rv:
    #print("tick")
    if tick["type"] == "PRICE":
        mt.on_success(tick)

#mt.rates(account_id=config['oanda']['account_id'],
#         instruments=['DE30_EUR'], ignore_heartbeat=True)
#mt.rates(account_id=config['oanda']['account_id'],
#         instruments=['DE30_EUR'], ignore_heartbeat=True)
