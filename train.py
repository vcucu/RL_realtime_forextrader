from envDRL import TradingEnv
from envOANDA import TradingEnvOanda
from agentDRL import DQNAgent
from agentRRL import RRLDQNAgent
import time
import pandas as pd
import numpy as np
import csv


if __name__ == "__main__":
    # initialize gym environment and the agent
    data = pd.read_csv("dataS15.csv")
    train_data = data.iloc[:12900]#get 80% for training
    test_data = data.iloc[12900:]#20% for validation
    params = {"episodes_nr" : 2000,
              "initial_investment":1000,
              "recurrent": False,
              "live": True,
              "train_or_test": "test", #train, test, continue_train
              "best_weights": "weights/202001101913-dqn-copy3.h5", #RLL "weights/202001141757-dqn-copy5.h5", # DRL ,
              "batch_size": 100}

    if params['live']:
        env = TradingEnvOanda(params["initial_investment"])
    else:
        env = TradingEnv(train_data, params["initial_investment"])
        data = train_data
    state_size = env.observation_space.shape
    action_size = env.action_space.n

    if params['recurrent']:
        agent =  RRLDQNAgent(state_size, action_size)
    else:
        agent = DQNAgent(state_size, action_size)

    if params['train_or_test'] == "test" or params['train_or_test'] == 'continue_train':
        agent.load(params['best_weights'])



    #run
    if (params['live'] == False):
        for e in range(params['episodes_nr']):
            # reset state in the beginning of each game
            state = env.reset()
            state = np.reshape(state, [1, 6]) #8 because we have 8 dimensions in state definition
            for tick in range(len(data)): #for time in range(env.n_step): #lets make it at most 500 ticks =roughly 2 hours
                action = agent.act(state) # Decide action
                next_state, reward, done, info = env.step(action)
                next_state = np.reshape(next_state, [1, 6])
                if (params['train_or_test'] != test):
                    # Remember the previous state, action, reward, and done
                    agent.remember(state, action, reward, next_state, done)
                # make next_state the new current state for the next frame.
                state = next_state
                if done:
                    # print the score and break out of the loop
                    print("episode: {}/{}, score: {}"
                          .format(e, params['episodes_nr'], info['cur_val']))
                    print(state)
                    break
                timestamp = time.strftime('%Y%m%d%H%M')
                if (params['train_or_test'] != test) and (e + 1) % 10 == 0:  # checkpoint weights
                    agent.save('weights/{}-dqn_copy2.h5'.format(timestamp))
            # train the agent with the experience of the episode
            if (params['train_or_test'] != test):
                #batch size
                agent.replay(100)

    if params['live'] and params['train_or_test'] == 'test':
        with open('testing_results.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Price", "Algo", "Order_type", "Stock_owned", "Current_val", "balance"])
            algo = "RRL" if params['recurrent'] else "DRL"
            while True:
                state = env.reset()
                print("state after reset", state)
                state = np.reshape(state, [1, 6])
                done = False
                while not done:

                    action = agent.act(state) # Decide action
                    next_state, reward, done, info = env.step(action)
                    next_state = np.reshape(next_state, [1, 6])
                    state = next_state
                    print("score: {}".format(info['cur_val']))
                    print(state)

                    timestamp = time.strftime('%Y%m%d%H%M')
                    writer.writerow([timestamp, info['bid_close'], algo, info['order_type'], info['stock_owned'], info['cur_val'], info['balance']])
