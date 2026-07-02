"""
Deep Reinforcement Learning (DRL) System for NOVA
Enables adaptive learning through reward-based optimization
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import random

class DRLSystem:
    def __init__(self, drl_file=os.path.join("userdata", "drl_model.json")):
        self.drl_file = drl_file
        self.q_table = {}  # State-Action-Value table
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2
        self.reward_history = []
        self.load_model()
    
    def load_model(self):
        """Load DRL model from file"""
        try:
            if os.path.exists(self.drl_file):
                with open(self.drl_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.q_table = data.get('q_table', {})
                    self.reward_history = data.get('reward_history', [])
                print(f"🤖 DRL System: Loaded {len(self.q_table)} state-action pairs")
        except Exception as e:
            print(f"⚠️ DRL load error: {e}")
    
    def save_model(self):
        """Save DRL model to file"""
        try:
            os.makedirs(os.path.dirname(self.drl_file), exist_ok=True)
            with open(self.drl_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'q_table': self.q_table,
                    'reward_history': self.reward_history[-100:]  # Keep last 100
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️ DRL save error: {e}")
    
    def get_state_key(self, intent: str, sentiment: str, confidence: float) -> str:
        """Create state key from current context"""
        conf_bucket = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        return f"{intent}_{sentiment}_{conf_bucket}"
    
    def get_action_options(self) -> List[str]:
        """Get available actions"""
        return [
            "direct_response",
            "ask_clarification",
            "use_knowledge_base",
            "use_llm",
            "suggest_alternative",
            "proactive_engagement",
            "multi_step_reasoning"
        ]
    
    def select_action(self, state: str) -> str:
        """Select action using epsilon-greedy policy"""
        # Exploration vs Exploitation
        if random.random() < self.exploration_rate:
            # Explore: random action
            return random.choice(self.get_action_options())
        else:
            # Exploit: best known action
            if state in self.q_table:
                actions = self.q_table[state]
                # Ensure all available actions are present in the state
                for action in self.get_action_options():
                    if action not in actions:
                        actions[action] = 0.0
                return max(actions, key=actions.get)
            else:
                # No experience with this state, initialize and return random
                self.q_table[state] = {a: 0.0 for a in self.get_action_options()}
                return random.choice(self.get_action_options())
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """Update Q-value using Q-learning algorithm"""
        # Initialize state if not exists
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.get_action_options()}
        else:
            # Ensure all current actions exist in the state (for model upgrades)
            for a in self.get_action_options():
                if a not in self.q_table[state]:
                    self.q_table[state][a] = 0.0
        
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in self.get_action_options()}
        
        # Q-learning update rule
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
        self.save_model()
    
    def calculate_reward(self, user_feedback: str, response_time: float, 
                        confidence: float) -> float:
        """Calculate reward based on multiple factors"""
        reward = 0.0
        
        # User feedback reward
        if user_feedback == "positive":
            reward += 1.0
        elif user_feedback == "negative":
            reward -= 1.0
        elif user_feedback == "neutral":
            reward += 0.0
        
        # Response time penalty (faster is better)
        if response_time < 1.0:
            reward += 0.2
        elif response_time > 3.0:
            reward -= 0.2
        
        # Confidence bonus
        if confidence > 0.8:
            reward += 0.1
        
        return reward
    
    def record_reward(self, state: str, action: str, reward: float):
        """Record reward for analysis"""
        self.reward_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state,
            'action': action,
            'reward': reward
        })
        
        # Keep only recent history
        if len(self.reward_history) > 100:
            self.reward_history = self.reward_history[-100:]
        
        self.save_model()
    
    def get_performance_stats(self) -> Dict:
        """Get DRL performance statistics"""
        if not self.reward_history:
            return {
                'total_episodes': 0,
                'average_reward': 0.0,
                'learned_states': len(self.q_table)
            }
        
        recent_rewards = [r['reward'] for r in self.reward_history[-20:]]
        
        return {
            'total_episodes': len(self.reward_history),
            'average_reward': sum(recent_rewards) / len(recent_rewards) if recent_rewards else 0.0,
            'learned_states': len(self.q_table),
            'exploration_rate': self.exploration_rate
        }
    
    def adapt_exploration_rate(self):
        """Decrease exploration rate over time (more exploitation)"""
        # Decay exploration rate
        self.exploration_rate = max(0.05, self.exploration_rate * 0.995)
