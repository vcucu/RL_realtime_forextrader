from envDRL import TradingEnv
from envDRL import TradingEnvOanda
from agentDRL import DQNAgent
import time
import pandas as pd
import numpy as np


if __name__ == "__main__":
    # initialize gym environment and the agent
    data = pd.read_csv("dataS15.csv")
    train_data = data.iloc[:12900]#get 80% for training
    test_data = data.iloc[12900:]#20% for validation
    params = {"episodes_nr" : 2000,
              "initial_investment":1000,
              "train_or_test": "test_oanda", #train, test, continue_train, test_oanda
              "batch_size": 100}

    env = TradingEnv(train_data, params["initial_investment"])
    data = train_data
    state_size = env.observation_space.shape
    action_size = env.action_space.n

    agent = DQNAgent(state_size, action_size)

    if params['train_or_test'] == "test":
        env = TradingEnv(test_data, params["initial_investment"]) #overwrite
        data = test_data
        agent.load("weights/201912091656-dqn_copy2.h5") #load previously calculate weights
    elif params['train_or_test'] == 'continue_train':
        agent.load("weights/201912091656-dqn_copy2.h5")
    elif params['train_or_test'] == 'test_oanda':
        env = TradingEnvOanda()
        agent.load("weights/201912091656-dqn_copy2.h5")

    if (params['train_or_test'] != "test_oanda"):
        for e in range(params['episodes_nr']):
            # reset state in the beginning of each game
            state = env.reset()

            state = np.reshape(state, [1, 14]) #8 because we have 8 dimensions in state definition

            for tick in range(len(data)): #for time in range(env.n_step): #lets make it at most 500 ticks =roughly 2 hours

                action = agent.act(state) # Decide action
                next_state, reward, done, info = env.step(action)
                next_state = np.reshape(next_state, [1, 14])
                if (params['train_or_test'] == "train"):
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
                if (params['train_or_test'] == "train" or params['train_or_test'] == "continue_train") and (e + 1) % 10 == 0:  # checkpoint weights
                    agent.save('weights/{}-dqn_copy2.h5'.format(timestamp))
            # train the agent with the experience of the episode
            if (params['train_or_test'] == "train" or params['train_or_test'] == "continue_train"  ):
                #batch size
                agent.replay(100)

    if params['train_or_test'] == "test_oanda":

        while True:
            state = env.reset()
            print(state)
            state = np.reshape(state, [1, 14]) #8 because we have 8 dimensions in state definition
            while not done:

                action = agent.act(state) # Decide action
                next_state, reward, done, info = env.step(action)
                next_state = np.reshape(next_state, [1, 14])
                print("score: {}".format(info['cur_val']))
                print(state)
