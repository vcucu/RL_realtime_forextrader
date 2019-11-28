import oandapyV20 as opy
class MomentumTrader(opy.Streamer):  # 25
    def __init__(self, momentum, *args, **kwargs):  # 26
        opy.Streamer.__init__(self, *args, **kwargs)  # 27
        self.ticks = 0  # 28
        self.position = 0  # 29
        self.df = pd.DataFrame()  # 30
        self.momentum = momentum  # 31
        self.units = 100000  # 32
    def create_order(self, side, units):  # 33
        order = oanda.create_order(config['oanda']['account_id'],
            instrument='EUR_USD', units=units, side=side,
            type='market')  # 34
        print('\n', order)  # 35
    def on_success(self, data):  # 36
        self.ticks += 1  # 37
        # print(self.ticks, end=', ')
        # appends the new tick data to the DataFrame object
        self.df = self.df.append(pd.DataFrame(data['tick'],
                                 index=[data['tick']['time']]))  # 38
        # transforms the time information to a DatetimeIndex object
        self.df.index = pd.DatetimeIndex(self.df['time'])  # 39
        # resamples the data set to a new, homogeneous interval
        dfr = self.df.resample('5s').last()  # 40
        # calculates the log returns
        dfr['returns'] = np.log(dfr['ask'] / dfr['ask'].shift(1))  # 41
        # derives the positioning according to the momentum strategy
        dfr['position'] = np.sign(dfr['returns'].rolling(
                                      self.momentum).mean())  # 42
        if dfr['position'].ix[-1] == 1:  # 43
            # go long
            if self.position == 0:  # 44
                self.create_order('buy', self.units)  # 45
            elif self.position == -1:  # 46
                self.create_order('buy', self.units * 2)  # 47
            self.position = 1  # 48
        elif dfr['position'].ix[-1] == -1:  # 49
            # go short
            if self.position == 0:  # 50
                self.create_order('sell', self.units)  # 51
            elif self.position == 1: # 52
                self.create_order('sell', self.units * 2)  # 53
            self.position = -1  # 54
        if self.ticks == 250:  # 55
            # close out the position
            if self.position == 1:  # 56
                self.create_order('sell', self.units)  # 57
            elif self.position == -1:  # 58
                self.create_order('buy', self.units)  # 59
            self.disconnect()  # 60


mt = MomentumTrader(momentum=12, environment='practice',
                    access_token=config['oanda']['access_token'])
mt.rates(account_id=config['oanda']['account_id'],
         instruments=['DE30_EUR'], ignore_heartbeat=True)
