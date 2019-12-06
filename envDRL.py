import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import itertools


class TradingEnv(gym.Env):

  def __init__(self, train_data, init_invest=10):
    # data
    self.stock_price_history = np.around(train_data, decimals = 4) # round up to integer to reduce state space
    #self.n_stock, self.n_step = self.stock_price_history.shape

    # instance attributes
    self.init_invest = init_invest #initial balance
    self.cur_step = None
    self.stock_owned = None
    self.balance = None #== position value
    #self.nav = None #==balance + (b_c * position_val) if long and (a_c * position_val) if short
    self.volume = None
    self.bid_close = None
    self.ask_close = None
    self.bid_close_previous = None
    self.ask_close_previous = None
    self.volume_previous = None

    # action space
    #self.action_space = spaces.Discrete(3**self.n_stock)

    # observation space: give estimates in order to sample and build scaler
    #stock_max_price = self.stock_price_history.max(axis=1)
    #stock_range = [[0, init_invest * 2 // mx] for mx in stock_max_price]
    #price_range = [[0, mx] for mx in stock_max_price]
    #cash_in_hand_range = [[0, init_invest * 2]]
    #self.observation_space = spaces.MultiDiscrete(stock_range + price_range + cash_in_hand_range)

    # seed and start
    #self._seed()
    self._reset()


  #def _seed(self, seed=None):
    #self.np_random, seed = seeding.np_random(seed)
    #return [seed]


  def _reset(self):
    self.cur_step = 0
    self.stock_owned = 0 #If more forex pairs were traded: [0] * self.n_stock
    self.init_invest = init_invest #initial balance
    self.balance = init_invest
    #update all prices and volume
    self.bid_close = self.stock_price_history.iloc[cur_step]['b_c']
    self.ask_close = self.stock_price_history.iloc[cur_step]['a_c']
    self.volume = self.stock_price_history.iloc[cur_step]['volume']
    if cur_step > 0 : #if there is an observation before this one
        self.bid_close_previous = self.stock_price_history.iloc[cur_step-1]['b_c']
        self.ask_close_previous = self.stock_price_history.iloc[cur_step-1]['a_c']
        self.volume_previous = self.stock_price_history.iloc[cur_step-1]['volume']
    else: #just pretend nothing changed since the last observation till this one
        self.bid_close_previous = self.bid_close
        self.ask_close_previous = self.ask_close
        self.volume_previous = self.volume
    #self.nav = None #==balance + (b_c * position_val) if long and (a_c * position_val) if short
    return self._get_obs()


  def _step(self, action):
    assert self.action_space.contains(action)
    prev_val = self._get_val()
    self.cur_step += 1
    self.bid_close = self.stock_price_history.iloc[cur_step]['b_c']
    self.ask_close = self.stock_price_history.iloc[cur_step]['a_c']
    self.volume = self.stock_price_history.iloc[cur_step]['volume']
    if cur_step > 0 : #if there is an observation before this one (robustness)
        self.bid_close_previous = self.stock_price_history.iloc[cur_step-1]['b_c']
        self.ask_close_previous = self.stock_price_history.iloc[cur_step-1]['a_c']
        self.volume_previous = self.stock_price_history.iloc[cur_step-1]['volume']
    else: #just pretend nothing changed since the last observation till this one
        self.bid_close_previous = self.bid_close
        self.ask_close_previous = self.ask_close
        self.volume_previous = self.volume
    self._trade(action)
    cur_val = self._get_val()
    reward = cur_val - prev_val
    done = (self.cur_step == len(self.stock_price_history - 1)
    info = {'cur_val': cur_val}
    return self._get_obs(), reward, done, info


  def _get_obs(self):
    obs = []
    obs.append(self.stock_owned) #use extend if there are multiple
    obs.append(self.balance)
    obs.append(self.bid_close)
    obs.append(self.ask_close)
    obs.append(self.volume)
    obs.append(self.bid_close_previous)
    obs.append(self.ask_close_previous)
    obs.append(self.ask_close_previous)
    return obs


  def _get_val(self): #reward function
    return (self.stock_owned * self.self.bid_close) + self.balance


  def _trade(self, action):

    if action == 0:
        self.balance += self.bid_close * self.stock_owned
        self.stock_owned = 0
    elif action == 2:
        can_buy = True #not sure how this is going to be used yet
        if self.balance > self.ask_close * 100: #if we can buy at least 100 shares
            self.stock_owned += 100
            self.balance -= self.ask_close *100
        else:
            can_buy =False
