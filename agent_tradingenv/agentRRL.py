#agentDRL.py

from collections import deque
import random
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout, Flatten
from keras.optimizers import Adam


# Deep Q-learning Agent
class RRLDQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size[0]
        #print("state size", self.state_size)
        self.action_size = action_size
        self.memory = deque(maxlen=3000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.00015
        self.model = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        #model = Sequential()
        #model.add(Dense(120, input_dim=self.state_size, activation='relu'))
        #model.add(Dense(120, activation='relu'))
        #model.add(Dense(self.action_size, activation='linear'))
        #model.compile(loss='mse',
        #              optimizer=Adam(lr=self.learning_rate))

        model=Sequential()
        model.add(LSTM(300, input_shape = (1, 6), return_sequences=True))
        model.add(Dropout(0.5))
        model.add(LSTM(200,input_shape = (1, 6), return_sequences=False))
        model.add(Dropout(0.5))
        #model.add(Flatten())
        model.add(Dense(100,kernel_initializer='uniform',activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',optimizer=Adam(lr=self.learning_rate))

        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state = np.reshape(state,(1,1,6))
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):
        if len(self.memory) > batch_size:
            minibatch = random.sample(self.memory, batch_size)
        else:
            minibatch = self.memory

        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state =  np.reshape(next_state,(1,1,6))
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            state =  np.reshape(state,(1,1,6))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        """states = np.array([tup[0][0] for tup in minibatch])
        actions = np.array([tup[1] for tup in minibatch])
        rewards = np.array([tup[2] for tup in minibatch])
        next_states = np.array([tup[3][0] for tup in minibatch])
        done = np.array([tup[4] for tup in minibatch])


        #print("shape",np.array(minibatch).shape)
        #print("states", states,"actions", actions,"rewards", rewards,"next_states", next_states,"done", done)
        #print("states shape", next_states.shape)
        next_states = np.reshape(next_states,(1,len(minibatch),6))
        states = np.reshape(states,(1,len(minibatch),6))
        #print("states shape 2", next_states.shape)


        # Q(s', a)
        target = rewards + self.gamma * np.amax(self.model.predict(next_states), axis=1)
        # end state target is reward itself (no lookahead)
        target[done] = rewards[done]

        # Q(s, a)
        target_f = self.model.predict(states)
        # make the agent to approximately map the current state to future discounted reward
        print("second", target_f)
        target_f[range(batch_size), actions] = target"""

        self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name, by_name=True)


    def save(self, name):
        self.model.save_weights(name)
