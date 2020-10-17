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


class TradingEnvOanda(gym.Env):

  def __init__(self, init_invest=1000):

    file = open("access.txt","r+")
    self.access_token = '82957cd1a8234cf899f729284c094d27-e31e01c267351992774813f5e64c8b43' #file.readline()
    self.accountID = "101-004-12401398-001"  #file.readline()
    print(self.accountID)
    print(self.access_token)
    file.close()
    self.init_invest = init_invest #initial balance
    self.client = oandapyV20.API(access_token=self.access_token)
    self.r = accounts.AccountDetails(self.accountID) #requests (about out account)
    params = {"instruments": "EUR_USD", "timeout": "5"}
    self.pc = pricing.PricingStream(self.accountID, params) #stream of prices
    self.order_type = 'market'
    self.tickcounter = 0
    #self.init_balance_diff = 0


    #self.cur_step = None
    self.stock_owned = None
    self.balance = None #== position value
    self.bid_close = None
    self.ask_close = None
    self.bid_close_p1 = None
    self.ask_close_p1 = None

    # action space
    self.action_space = spaces.Discrete(3)

    # observation space: give estimates in order to sample and build scaler
    balance_range = np.array((-init_invest * 2, init_invest * 2))
    stock_range = np.array((0, init_invest * 2 // 1.5)) #stock owned
    bid_range = np.array((0, 1.5))
    ask_range = np.array((0,1.5))
    ask_p1_range = ask_range
    bid_p1_range = bid_range

    self.observation_space = spaces.Box(low = np.array((balance_range[0]
    ,stock_range[0], bid_range[0], ask_range[0],
    ask_p1_range[0], bid_p1_range[0])),
    high = np.array((balance_range[1],stock_range[1], bid_range[1], ask_range[1],
     ask_p1_range[1], bid_p1_range[1])))

    self._reset()

  def _reset(self):
    self.tick_counter = 0
    self.client.request(self.r)
    res = self.r.response
    print("response", res)
    long =  (float)(res['account']['positions'][0]['long']['units'])
    short = (float)(res['account']['positions'][0]['short']['units'])
    self.stock_owned = long - short
    #(float)(res['account']['positionValue']) #If more forex pairs were traded: [0] * self.n_stock
    #self.init_balance_diff = (float)(res['account']['marginAvailable']) - self.init_invest #this will not be taken from the API in order to hide the actual amount
    self.balance = (float)(res['account']['balance'])# - self.init_balance_diff
    #update all prices and volume
    #wait until update comes from the streaming api
    pcr = self.client.request(self.pc)
    for tick in pcr:
        if tick['type'] == "PRICE":
            self.bid_close = (float)(tick['closeoutBid'])
            self.ask_close = (float)(tick['closeoutAsk'])
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.tickcounter += 1
            break
    return self._get_obs()



  def _step(self, action):
    assert self.action_space.contains(action)
    prev_val = self._get_val()
    res = self.r.response
    long =  (float)(res['account']['positions'][0]['long']['units'])
    short = (float)(res['account']['positions'][0]['short']['units'])
    self.stock_owned = long - short
    self.balance = (float)(res['account']['balance']) #- self.init_balance_diff
    print("stock owned was updated to", self.stock_owned)#check why am i constantly buying
    print("And the balance is ", self.balance)
    pcr = self.client.request(self.pc)
    for tick in pcr:
        if tick['type'] == "PRICE":
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close
            self.bid_close = (float)(tick['closeoutBid'])
            self.ask_close = (float)(tick['closeoutAsk'])
            self.tickcounter += 1
            break

    self._trade(action)

    self.balance = (float)(res['account']['balance'])# - self.init_balance_diff
    long =  (float)(res['account']['positions'][0]['long']['units'])
    short = (float)(res['account']['positions'][0]['short']['units'])
    self.stock_owned = long - short

    cur_val = self._get_val()
    reward = cur_val - prev_val
    done = self.tickcounter == 12 #aka every minute there should be an update if a tick is every 5 sec
    info = {'cur_val': cur_val, 'bid_close':self.bid_close, 'order_type': self.order_type, 'stock_owned': self.stock_owned , 'balance': self.balance, 'price': self.bid_close}
    return self._get_obs(), reward, done, info

  def _get_obs(self):
    obs = []
    obs.append(self.stock_owned) #use extend if there are multiple
    obs.append(self.balance)
    obs.append(self.bid_close)
    obs.append(self.ask_close)
    obs.append(self.bid_close_p1)
    obs.append(self.ask_close_p1)

    return obs

  def _get_val(self): #reward function
    return (self.stock_owned * self.bid_close) + self.balance


  def _trade(self, action):
    print("action", action)
    if action == 0: #sell
        #self.balance += self.bid_close * self.stock_owned
        #self.stock_owned = 0
        if self.stock_owned > 0:
            if (self.order_type == "limit"): #create limit order
                data = {
                  "order": {
                    "price": np.around(self.bid_close, decimals = 3)-0.01,
                    "stopLossOnFill": {
                      "timeInForce": "GTC",
                      "price": np.around(self.bid_close, decimals = 3)-0.01
                    },
                    "timeInForce": "GFD",
                    "instrument": "EUR_USD",
                    "units": -100,
                    "type": "LIMIT",
                    "positionFill": "DEFAULT"
                  }
                }
            else: #create market order
                data = {
                    "order": {
                    "timeInForce": "FOK",
                    "instrument": "EUR_USD",
                    "units": -100,
                    "type": "MARKET",
                    "positionFill": "DEFAULT"
                  }
                }
            #update balance although the order happening is not guaranteed with limit order
            #and the exact price is not guaranteed with the market order
            #self.balance += self.bid_close * self.stock_owned
            #self.stock_owned = 0
            #print('price', data['order']['price'])
            oc = orders.OrderCreate(self.accountID, data=data)
            self.client.request(oc)
            print(oc.response)
    elif action == 2: #buy stocks
        if self.balance > (self.ask_close * 100): #if we can buy at least 100 shares
            if (self.order_type == "limit"): #create limit order
                data = {
                  "order": {
                    "price": np.around(self.ask_close, decimals = 2)+0.01,
                    "stopLossOnFill": {
                      "timeInForce": "GTC",
                      "price": np.around(self.ask_close, decimals = 2)+0.01
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
            #self.stock_owned += 100
            #self.balance -= self.ask_close *100
            oc = orders.OrderCreate(self.accountID, data=data)
            print(oc)
            self.client.request(oc)
            print(oc.response)
