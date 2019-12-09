import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from numpy.random import randint
import itertools
#oanda
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.orders as orders

class TradingEnv(gym.Env):

    def __init__(self, train_data, init_invest=1000):
        # data
        self.stock_price_history = np.around(train_data, decimals = 4)
        #self.n_stock, self.n_step = self.stock_price_history.shape
        # instance attributes
        self.init_invest = init_invest #initial balance
        self.cur_step = None
        self.stock_owned = None
        self.balance = None #== position value
        self.volume = None
        self.bid_close = None
        self.ask_close = None
        self.bid_close_p1 = None
        self.ask_close_p1 = None
        self.volume_p1 = None
        self.bid_close_p2 = None
        self.ask_close_p2 = None
        self.volume_p2 = None
        self.bid_close_p3 = None
        self.ask_close_p3 = None
        self.volume_p3 = None


        # action space
        self.action_space = spaces.Discrete(3)

        # observation space: give estimates in order to sample and build scaler
        balance_range = np.array((-init_invest * 2, init_invest * 2))
        stock_range = np.array((0, init_invest * 2 // self.stock_price_history['a_c'].max())) #stock owned
        bid_range = np.array((0, self.stock_price_history['a_c'].max()))
        ask_range = np.array((0,self.stock_price_history['a_c'].max()))
        volume_range = np.array((0, self.stock_price_history['volume'].max()))
        ask_p1_range = ask_range
        bid_p1_range = bid_range
        volume_p1_range = volume_range
        ask_p2_range = ask_range
        bid_p2_range = bid_range
        volume_p2_range = volume_range
        ask_p3_range = ask_range
        bid_p3_range = bid_range
        volume_p3_range = volume_range
        self.observation_space = spaces.Box(low = np.array((balance_range[0]
        ,stock_range[0], bid_range[0], ask_range[0], volume_range[0],
        ask_p1_range[0], bid_p1_range[0], volume_p1_range[0],
        ask_p2_range[0], bid_p2_range[0], volume_p2_range[0],
        ask_p3_range[0], bid_p3_range[0], volume_p3_range[0])),
        high = np.array((balance_range[1],stock_range[1], bid_range[1], ask_range[1],
         volume_range[1], ask_p1_range[1], bid_p1_range[1],
         volume_p1_range[1], ask_p2_range[1], bid_p2_range[1],
         volume_p2_range[1], ask_p3_range[1], bid_p3_range[1],
         volume_p3_range[1])))

        # seed and start
        self._seed()
        self._reset()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _reset(self):
        self.cur_step = randint(0,len(self.stock_price_history)-1)
        self.stock_owned = 0 #If more forex pairs were traded: [0] * self.n_stock
        self.balance = self.init_invest
        #update all prices and volume
        self.bid_close = self.stock_price_history.iloc[self.cur_step]['b_c']
        self.ask_close = self.stock_price_history.iloc[self.cur_step]['a_c']
        self.volume = self.stock_price_history.iloc[self.cur_step]['volume']
        if self.cur_step > 2 : #if there is an observation before this one
            self.bid_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['b_c']
            self.ask_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['a_c']
            self.volume_p1 = self.stock_price_history.iloc[self.cur_step-1]['volume']
            self.bid_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['b_c']
            self.ask_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['a_c']
            self.volume_p2 = self.stock_price_history.iloc[self.cur_step-2]['volume']
            self.bid_close_p3 = self.stock_price_history.iloc[self.cur_step-2]['b_c']
            self.ask_close_p3 = self.stock_price_history.iloc[self.cur_step-2]['a_c']
            self.volume_p3 = self.stock_price_history.iloc[self.cur_step-2]['volume']
        else: #just pretend nothing changed since the last observation till this one
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.volume_p1 = self.volume
            self.bid_close_p2 = self.bid_close
            self.ask_close_p2 = self.ask_close
            self.volume_p2 = self.volume
            self.bid_close_p3 = self.bid_close
            self.ask_close_p3 = self.ask_close
            self.volume_p3 = self.volume
        #self.nav = None #==balance + (b_c * position_val) if long and (a_c * position_val) if short
        return self._get_obs()

    def _step(self, action):
        assert self.action_space.contains(action)
        prev_val = self._get_val()
        self.cur_step += 1
        self.bid_close = self.stock_price_history.iloc[self.cur_step]['b_c']
        self.ask_close = self.stock_price_history.iloc[self.cur_step]['a_c']
        self.volume = self.stock_price_history.iloc[self.cur_step]['volume']
        if self.cur_step > 1 : #if there is an observation before this one
            self.bid_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['b_c']
            self.ask_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['a_c']
            self.volume_p1 = self.stock_price_history.iloc[self.cur_step-1]['volume']
            self.bid_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['b_c']
            self.ask_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['a_c']
            self.volume_p2 = self.stock_price_history.iloc[self.cur_step-2]['volume']
            self.bid_close_p3 = self.stock_price_history.iloc[self.cur_step-3]['b_c']
            self.ask_close_p3 = self.stock_price_history.iloc[self.cur_step-3]['a_c']
            self.volume_p3 = self.stock_price_history.iloc[self.cur_step-3]['volume']
        else: #just pretend nothing changed since the last observation till this one
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.volume_p1 = self.volume
            self.bid_close_p2 = self.bid_close
            self.ask_close_p2 = self.ask_close
            self.volume_p2 = self.volume
            self.bid_close_p3 = self.bid_close
            self.ask_close_p3 = self.ask_close
            self.volume_p3 = self.volume
        self._trade(action)
        cur_val = self._get_val()
        reward = cur_val - prev_val + self.balance
        done = (self.cur_step == len(self.stock_price_history) - 1)
        info = {'cur_val': cur_val}
        return self._get_obs(), reward, done, info

    def _get_obs(self):
        obs = []
        obs.append(self.stock_owned) #use extend if there are multiple
        obs.append(self.balance)
        obs.append(self.bid_close)
        obs.append(self.ask_close)
        obs.append(self.volume)
        obs.append(self.bid_close_p1)
        obs.append(self.ask_close_p1)
        obs.append(self.volume_p1)
        obs.append(self.bid_close_p2)
        obs.append(self.ask_close_p2)
        obs.append(self.volume_p2)
        obs.append(self.bid_close_p3)
        obs.append(self.ask_close_p3)
        obs.append(self.volume_p3)
        return obs

    def _get_val(self): #reward function
        return (self.stock_owned * self.bid_close) + self.balance


    def _trade(self, action):
        if action == 0:
            self.balance += self.bid_close * self.stock_owned
            self.stock_owned = 0
        elif action == 2:
            can_buy = True #not sure how this is going to be used yet
            if self.balance > (self.ask_close * 100): #if we can buy at least 100 shares
                self.stock_owned += 100
                self.balance -= self.ask_close *100
            else:
                can_buy =False

    def _step(self, action):
        assert self.action_space.contains(action)
        prev_val = self._get_val()
        self.cur_step += 1
        self.bid_close = self.stock_price_history.iloc[self.cur_step]['b_c']
        self.ask_close = self.stock_price_history.iloc[self.cur_step]['a_c']
        self.volume = self.stock_price_history.iloc[self.cur_step]['volume']
        if self.cur_step > 1 : #if there is an observation before this one
            self.bid_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['b_c']
            self.ask_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['a_c']
            self.volume_p1 = self.stock_price_history.iloc[self.cur_step-1]['volume']
            self.bid_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['b_c']
            self.ask_close_p2 = self.stock_price_history.iloc[self.cur_step-2]['a_c']
            self.volume_p2 = self.stock_price_history.iloc[self.cur_step-2]['volume']
            self.bid_close_p3 = self.stock_price_history.iloc[self.cur_step-3]['b_c']
            self.ask_close_p3 = self.stock_price_history.iloc[self.cur_step-3]['a_c']
            self.volume_p3 = self.stock_price_history.iloc[self.cur_step-3]['volume']
        else: #just pretend nothing changed since the last observation till this one
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.volume_p1 = self.volume
            self.bid_close_p2 = self.bid_close
            self.ask_close_p2 = self.ask_close
            self.volume_p2 = self.volume
            self.bid_close_p3 = self.bid_close
            self.ask_close_p3 = self.ask_close
            self.volume_p3 = self.volume
        self._trade(action)
        cur_val = self._get_val()
        reward = cur_val - prev_val
        done = (self.cur_step == len(self.stock_price_history) - 1)
        info = {'cur_val': cur_val}
        return self._get_obs(), reward, done, info


    def _get_val(self): #reward function
        return (self.stock_owned * self.bid_close) + self.balance #- self.init_invest


    def _trade(self, action):
        if action == 0:
            self.balance += self.bid_close * self.stock_owned
            self.stock_owned = 0
        elif action == 2:
            can_buy = True #not sure how this is going to be used yet
            if self.balance > (self.ask_close * 100): #if we can buy at least 100 shares
                self.stock_owned += 100
                self.balance -= self.ask_close *100
            else:
                can_buy = False


class TradingEnvOanda(gym.Env):

  def __init__(self, init_invest=1000):
    self.client = oandapyV20.API(access_token='82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43')
    self.accountID = "101-004-12401398-001"
    self.r = accounts.AccountDetails(self.accountID) #requests (about out account)
    params = {"instruments": "EUR_USD", "timeout": "5"}
    self.pc = pricing.PricingStream(self.accountID, params) #stream of prices
    self.order_type = 'limit'
    self.tickcounter = 0

    self.init_invest = init_invest #initial balance
    #self.cur_step = None
    self.stock_owned = None
    self.balance = None #== position value
    #self.nav = None #==balance + (b_c * position_val) if long and (a_c * position_val) if short
    self.volume = None
    self.bid_close = None
    self.ask_close = None
    self.bid_close_p1 = None
    self.ask_close_p1 = None
    self.volume_p1 = None
    self.bid_close_p2 = None
    self.ask_close_p2 = None
    self.volume_p2 = None
    self.bid_close_p3 = None
    self.ask_close_p3 = None
    self.volume_p3 = None

    # action space
    self.action_space = spaces.Discrete(3)

    # observation space: give estimates in order to sample and build scaler
    balance_range = np.array((-init_invest * 2, init_invest * 2))
    stock_range = np.array((0, init_invest * 2 // 1.5)) #stock owned
    bid_range = np.array((0, 1.5))
    ask_range = np.array((0,1.5))
    volume_range = np.array((0, 1.5))
    ask_p1_range = ask_range
    bid_p1_range = bid_range
    volume_p1_range = volume_range
    ask_p2_range = ask_range
    bid_p2_range = bid_range
    volume_p2_range = volume_range
    ask_p3_range = ask_range
    bid_p3_range = bid_range
    volume_p3_range = volume_range
    self.observation_space = spaces.Box(low = np.array((balance_range[0]
    ,stock_range[0], bid_range[0], ask_range[0], volume_range[0],
    ask_p1_range[0], bid_p1_range[0], volume_p1_range[0],
    ask_p2_range[0], bid_p2_range[0], volume_p2_range[0],
    ask_p3_range[0], bid_p3_range[0], volume_p3_range[0])),
    high = np.array((balance_range[1],stock_range[1], bid_range[1], ask_range[1],
     volume_range[1], ask_p1_range[1], bid_p1_range[1],
     volume_p1_range[1], ask_p2_range[1], bid_p2_range[1],
     volume_p2_range[1], ask_p3_range[1], bid_p3_range[1],
     volume_p3_range[1])))

    self._reset()

  def _reset(self):
    self.tick_counter = 0
    self.client.request(self.r)
    res = self.r.response
    print(res)
    self.stock_owned = (float)(res['account']['positionValue']) #If more forex pairs were traded: [0] * self.n_stock
    self.balance = self.init_invest #this will not be taken from the API in order to hide the actual amount
    #update all prices and volume
    #wait until update comes from the streaming api
    pcr = self.client.request(self.pc)
    for tick in pcr:
        if tick['type'] == "PRICE":
            self.bid_close = (float)(tick['closeoutBid'])
            self.ask_close = (float)(tick['closeoutAsk'])
            self.volume = 1.0 #next time we train, volume needs to be taken out of features
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.volume_p1 = self.volume
            self.bid_close_p2 = self.bid_close
            self.ask_close_p2 = self.ask_close
            self.volume_p2 = self.volume
            self.bid_close_p3 = self.bid_close
            self.ask_close_p3 = self.ask_close
            self.volume_p3 = self.volume
            self.tickcounter += 1
            break
    return self._get_obs()

  def _step(self, action):
    assert self.action_space.contains(action)
    prev_val = self._get_val()
    res = self.r.response
    self.stock_owned = (float)(res['account']['positionValue']) #If more forex pairs were traded: [0] * self.n_stock
    pcr = self.client.request(self.pc)
    for tick in pcr:
        if tick['type'] == "PRICE":
            self.bid_close_p3 = self.bid_close_p2
            self.ask_close_p3 = self.ask_close_p2
            self.volume_p3 = self.volume_p2
            self.bid_close_p2 = self.bid_close_p1
            self.ask_close_p2 = self.ask_close_p1
            self.volume_p2 = self.volume_p1
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.volume_p1 = self.volume
            self.bid_close = (float)(tick['closeoutBid'])
            self.ask_close = (float)(tick['closeoutAsk'])
            self.volume = 1.0 #next time we train, volume needs to be taken out of features
            self.tickcounter += 1
            break

    self._trade(action)
    cur_val = self._get_val()
    reward = cur_val - prev_val + self.balance
    done = self.tickcounter == 12 #aka every minute there should be an update if a tick is every 5 sec
    info = {'cur_val': cur_val}
    return self._get_obs(), reward, done, info

  def _get_obs(self):
    obs = []
    obs.append(self.stock_owned) #use extend if there are multiple
    obs.append(self.balance)
    obs.append(self.bid_close)
    obs.append(self.ask_close)
    obs.append(self.volume)
    obs.append(self.bid_close_p1)
    obs.append(self.ask_close_p1)
    obs.append(self.volume_p1)
    obs.append(self.bid_close_p2)
    obs.append(self.ask_close_p2)
    obs.append(self.volume_p2)
    obs.append(self.bid_close_p3)
    obs.append(self.ask_close_p3)
    obs.append(self.volume_p3)

  def _get_val(self): #reward function
    return (self.stock_owned * self.bid_close) + self.balance


  def _trade(self, action):
    print(action)
    if action == 0: #sell
        #self.balance += self.bid_close * self.stock_owned
        #self.stock_owned = 0
        if (self.order_type == "limit"): #create limit order
            data = {
              "order": {
                "price": self.bid_close,
                "stopLossOnFill": {
                  "timeInForce": "GTC",
                  "price": self.bid_lose
                },
                "timeInForce": "GFD",
                "instrument": "EUR_USD",
                "units": -self.stock_owned,
                "type": "LIMIT",
                "positionFill": "DEFAULT"
              }
            }
        else: #create market order
            data = {
                "order": {
                "timeInForce": "FOK",
                "instrument": "EUR_USD",
                "units": -self.stock_owned,
                "type": "MARKET",
                "positionFill": "DEFAULT"
              }
            }
        #update balance although the order happening is not guaranteed with limit order
        #and the exact price is not guaranteed with the market order
        self.balance += self.bid_close * self.stock_owned
        self.stock_owned = 0
        oc = orders.OrderCreate(accountID, data=data)
        client.request(self.r)
    elif action == 2: #buy stocks
        if self.balance > (self.ask_close * 100): #if we can buy at least 100 shares
            if (self.order_type == "limit"): #create limit order
                data = {
                  "order": {
                    "price": self.ask_close,
                    "stopLossOnFill": {
                      "timeInForce": "GTC",
                      "price": self.ask_close
                    },
                    "timeInForce": "GFD",
                    "instrument": "EUR_USD",
                    "units": 100,
                    "type": "LIMIT",
                    "positionFill": "DEFAULT"
                  }
                }
            else: #create market order
                data = {
                    "order": {
                    "timeInForce": "FOK",
                    "instrument": "EUR_USD",
                    "units": 100,
                    "type": "MARKET",
                    "positionFill": "DEFAULT"
                  }
                }
            self.stock_owned += 100
            self.balance -= self.ask_close *100
            oc = orders.OrderCreate(accountID, data=data)
            client.request(r)
