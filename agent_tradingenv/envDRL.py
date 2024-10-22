import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from numpy.random import randint
import itertools


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
        self.bid_close = None
        self.ask_close = None
        self.bid_close_p1 = None
        self.ask_close_p1 = None

        # action space
        self.action_space = spaces.Discrete(3)

        # observation space: give estimates in order to sample and build scaler
        balance_range = np.array((-init_invest * 2, init_invest * 2))
        stock_range = np.array((0, init_invest * 2 // self.stock_price_history['a_c'].max())) #stock owned
        bid_range = np.array((0, self.stock_price_history['a_c'].max()))
        ask_range = np.array((0,self.stock_price_history['a_c'].max()))
        ask_p1_range = ask_range
        bid_p1_range = bid_range
        self.observation_space = spaces.Box(low = np.array((balance_range[0]
        ,stock_range[0], bid_range[0], ask_range[0],
        ask_p1_range[0], bid_p1_range[0])),
        high = np.array((balance_range[1],stock_range[1], bid_range[1], ask_range[1],
         ask_p1_range[1], bid_p1_range[1],
         volume_p1_range[1], ask_p2_range[1])))

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
        if self.cur_step > 1 : #if there is an observation before this one
            self.bid_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['b_c']
            self.ask_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['a_c']
        else: #just pretend nothing changed since the last observation till this one
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close

        return self._get_obs()

    def _step(self, action):
        assert self.action_space.contains(action)
        prev_val = self._get_val()
        self.cur_step += 1
        self.bid_close = self.stock_price_history.iloc[self.cur_step]['b_c']
        self.ask_close = self.stock_price_history.iloc[self.cur_step]['a_c']
        if self.cur_step > 1 : #if there is an observation before this one
            self.bid_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['b_c']
            self.ask_close_p1 = self.stock_price_history.iloc[self.cur_step-1]['a_c']
        else: #just pretend nothing changed since the last observation till this one
            self.bid_close_p1 = self.bid_close
            self.ask_close_p1 = self.ask_close

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
        obs.append(self.bid_close_p1)
        obs.append(self.ask_close_p1)
        return obs

    def _get_val(self): #reward function
        return (self.stock_owned * self.bid_close) +self.balance


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
