import numpy as np
import random
from collections import deque
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if CUDA is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")

class ThreatEnvironment:
    """Environment for the reinforcement learning agent"""
    def __init__(self):
        self.state_size = 10  # Number of features in state
        self.action_space = [
            "block_ip",
            "rate_limit",
            "alert_only",
            "quarantine",
            "allow"
        ]
        self.action_size = len(self.action_space)
        self.current_state = None
        self.reset()
    
    def reset(self):
        """Reset the environment to initial state"""
        self.current_state = np.zeros(self.state_size)
        return self.current_state
    
    def step(self, action_idx: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Execute one step in the environment
        Returns: (next_state, reward, done, info)
        """
        action = self.action_space[action_idx]
        reward = 0.0
        done = False
        info = {"action_taken": action}
        
        # Simulate environment response to action
        # In a real system, this would interact with the actual environment
        
        # Calculate reward based on action and current state
        if action == "block_ip":
            # High reward for blocking actual threats, high penalty for false positives
            if self.current_state[0] > 0.7:  # High threat confidence
                reward = 1.0
            else:
                reward = -0.5
                
        elif action == "rate_limit":
            # Moderate reward for rate limiting suspicious traffic
            if 0.3 < self.current_state[0] < 0.7:  # Medium threat confidence
                reward = 0.7
            else:
                reward = -0.2
                
        elif action == "alert_only":
            # Low reward for just alerting on high threats
            if self.current_state[0] > 0.7:
                reward = 0.2
            else:
                reward = 0.1
                
        # Generate next state (simulated)
        self.current_state = np.random.random(self.state_size)
        
        # Randomly end episode (for simulation)
        done = random.random() < 0.05
        
        return self.current_state, reward, done, info

class ReplayBuffer:
    """Experience replay buffer for storing and sampling transitions"""
    def __init__(self, buffer_size: int = 10000):
        self.buffer = deque(maxlen=buffer_size)
    
    def add(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Add a transition to the buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple:
        """Sample a batch of transitions"""
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(np.array(states)).to(device),
            torch.LongTensor(actions).to(device),
            torch.FloatTensor(rewards).to(device),
            torch.FloatTensor(np.array(next_states)).to(device),
            torch.FloatTensor(dones).to(device)
        )
    
    def __len__(self) -> int:
        return len(self.buffer)

class QNetwork(nn.Module):
    """Deep Q-Network for approximating Q-values"""
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 64):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, action_size)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

class DQNAgent:
    """Deep Q-Learning agent for threat response"""
    def __init__(
        self,
        state_size: int,
        action_size: int,
        hidden_size: int = 64,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        memory_size: int = 10000,
        target_update_freq: int = 100,
        model_path: str = None
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = ReplayBuffer(memory_size)
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.steps = 0
        
        # Initialize Q-networks
        self.policy_net = QNetwork(state_size, action_size, hidden_size).to(device)
        self.target_net = QNetwork(state_size, action_size, hidden_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer and loss function
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        
        # Load model if path is provided
        if model_path:
            self.load(model_path)
    
    def act(self, state: np.ndarray, eval_mode: bool = False) -> int:
        """Select an action using epsilon-greedy policy"""
        if not eval_mode and random.random() < self.epsilon:
            return random.randrange(self.action_size)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()
    
    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Store experience in replay memory"""
        self.memory.add(state, action, reward, next_state, done)
    
    def replay(self) -> Optional[float]:
        """Train on a batch of experiences from memory"""
        if len(self.memory) < self.batch_size:
            return None
        
        # Sample batch from memory
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Compute Q(s_t, a)
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Compute V(s_{t+1}) for all next states
        with torch.no_grad():
            next_q_values = self.target_net(next_states)
            next_q = next_q_values.max(1)[0].detach()
            expected_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss and update
        loss = self.criterion(current_q.squeeze(), expected_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update target network
        self.steps += 1
        if self.steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        return loss.item()
    
    def save(self, path: str):
        """Save the model"""
        torch.save({
            'policy_state_dict': self.policy_net.state_dict(),
            'target_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps': self.steps
        }, path)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load the model"""
        try:
            checkpoint = torch.load(path, map_location=device)
            self.policy_net.load_state_dict(checkpoint['policy_state_dict'])
            self.target_net.load_state_dict(checkpoint['target_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.epsilon = checkpoint.get('epsilon', self.epsilon)
            self.steps = checkpoint.get('steps', 0)
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")

class ThreatResponseAgent:
    """High-level agent for managing threat response with RL"""
    def __init__(self, model_path: str = None):
        self.env = ThreatEnvironment()
        self.agent = DQNAgent(
            state_size=self.env.state_size,
            action_size=self.env.action_size,
            model_path=model_path
        )
        self.episode_rewards = []
        self.losses = []
    
    def train(self, num_episodes: int = 1000, save_path: str = None):
        """Train the agent"""
        logger.info("Starting training...")
        
        for episode in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                # Select and perform action
                action = self.agent.act(state)
                next_state, reward, done, info = self.env.step(action)
                
                # Store experience and train
                self.agent.remember(state, action, reward, next_state, done)
                loss = self.agent.replay()
                
                if loss is not None:
                    self.losses.append(loss)
                
                episode_reward += reward
                state = next_state
            
            self.episode_rewards.append(episode_reward)
            
            # Log progress
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_loss = np.mean(self.losses[-10:]) if self.losses else 0
                logger.info(
                    f"Episode {episode + 1}/{num_episodes}, "
                    f"Avg Reward: {avg_reward:.2f}, "
                    f"Avg Loss: {avg_loss:.4f}, "
                    f"Epsilon: {self.agent.epsilon:.4f}"
                )
            
            # Save model periodically
            if save_path and (episode + 1) % 100 == 0:
                self.agent.save(f"{save_path}_episode_{episode + 1}.pth")
        
        # Save final model
        if save_path:
            self.agent.save(f"{save_path}_final.pth")
        
        return self.episode_rewards
    
    def predict_action(self, state: np.ndarray) -> str:
        """Predict the best action for a given state"""
        action_idx = self.agent.act(state, eval_mode=True)
        return self.env.action_space[action_idx]
    
    def get_action_probs(self, state: np.ndarray) -> Dict[str, float]:
        """Get action probabilities for a given state"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            q_values = self.agent.policy_net(state_tensor).squeeze().cpu().numpy()
            probs = np.exp(q_values) / np.sum(np.exp(q_values))  # Softmax
            return {action: float(prob) for action, prob in zip(self.env.action_space, probs)}

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = ThreatResponseAgent()
    
    # Train the agent
    print("Training agent...")
    rewards = agent.train(num_episodes=100, save_path="threat_response_model")
    
    # Test the trained agent
    print("\nTesting agent...")
    test_state = np.random.random(agent.env.state_size)
    action = agent.predict_action(test_state)
    print(f"Recommended action: {action}")
    
    # Get action probabilities
    action_probs = agent.get_action_probs(test_state)
    print("\nAction probabilities:")
    for action, prob in action_probs.items():
        print(f"{action}: {prob:.4f}")
