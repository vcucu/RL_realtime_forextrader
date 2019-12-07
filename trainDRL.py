from envDRL import TradingEnv
from agentDRL import DQNAgent
import pandas as pd

if __name__ == "__main__":
    # initialize gym environment and the agent
    data = pd.read_csv("dataS15.csv")
    train_data = data.iloc[:12900]#get 80% for training
    test_data = data.iloc[12900:]#20% for validation
    params = {"episodes_nr" : 100,
              "initial_investment":10,
              "train_or_test": "train",
              "batch_size": 100}

    env = TradingEnv(train_data)
    state_size = env.observation_space.shape
    action_size = env.action_space
    agent = DQNAgent(state_size, action_size)

    if params['train_or_test'] == "test":
        env = TradingEnv(test_data) #overwrite
        agent.load(args.weights) #load previously calculate weights

    for e in range(params['episodes_nr']):
        # reset state in the beginning of each game
        state = env.reset()
        state = np.reshape(state, [1, 4]) #whyyy?

        for tick in range(500): #for time in range(env.n_step): #lets make it at most 500 ticks =roughly 2 hours

            action = agent.act(state) # Decide action
            # Advance the game to the next frame based on the action.
            next_state, reward, done, info = env.step(action)
            next_state = np.reshape(next_state, [1, 4]) #whyyy
            if (params['train_or_test'] == "train"):
                # Remember the previous state, action, reward, and done
                agent.remember(state, action, reward, next_state, done)
            # make next_state the new current state for the next frame.
            state = next_state

            if done:
                # print the score and break out of the loop
                print("episode: {}/{}, score: {}"
                      .format(e, params['episodes_nr'], info['cur_val']))
                break
            if params['train_or_test'] == "train" and (e + 1) % 10 == 0:  # checkpoint weights
                agent.save('weights/{}-dqn.h5'.format(timestamp))
        # train the agent with the experience of the episode
        agent.replay(32)
