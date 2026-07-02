import torch
import torch.nn as nn
import numpy as np
import json
import os
import re
import string

class ResidualBlock(nn.Module):
    def __init__(self, size):
        super(ResidualBlock, self).__init__()
        self.fc = nn.Linear(size, size)
        self.bn = nn.BatchNorm1d(size)
        self.relu = nn.ReLU()

    def forward(self, x):
        residual = x
        out = self.fc(x)
        out = self.bn(out)
        out = self.relu(out)
        return out + residual

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes, emotion_size):
        super(NeuralNet, self).__init__()
        self.input_layer = nn.Linear(input_size, hidden_size)
        self.bn_input = nn.BatchNorm1d(hidden_size)
        
        # 9 Residual Blocks as seen in state_dict
        self.res_layers = nn.ModuleList([ResidualBlock(hidden_size) for _ in range(9)])
        
        self.intent_head = nn.Linear(hidden_size, num_classes)
        self.emotion_head = nn.Linear(hidden_size, emotion_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        out = self.input_layer(x)
        out = self.bn_input(out)
        out = self.relu(out)
        
        for res_block in self.res_layers:
            out = res_block(out)
            
        intent = self.intent_head(out)
        emotion = self.emotion_head(out)
        return intent, emotion

class NeuralChat:
    def __init__(self, model_path=os.path.join("userdata", "brain.pth"), intents_file=os.path.join("userdata", "intents.json")):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_path = model_path
        self.intents_file = intents_file
        
        if os.path.exists(model_path):
            try:
                data = torch.load(model_path, map_location=self.device, weights_only=False)
                self.input_size = data["input_size"]
                self.hidden_size = data["hidden_size"]
                self.output_size = data["output_size"]
                self.emotion_size = data["emotion_size"]
                self.all_words = data["all_words"]
                self.tags = data["tags"]
                self.emotion_tags = data["emotion_tags"]
                self.model_state = data["model_state"]

                self.model = NeuralNet(self.input_size, self.hidden_size, self.output_size, self.emotion_size).to(self.device)
                self.model.load_state_dict(self.model_state)
                self.model.eval()
                print(f" NeuralChat: Loaded model from {model_path}")
            except Exception as e:
                print(f"❌ NeuralChat Error loading model: {e}")
                self.model = None # type: ignore
        else:
            # Informational only, as training is optional
            print(f"ℹ️ NeuralChat: Custom model ({model_path}) not found. Using LLM fallbacks.")
            self.model = None # type: ignore

    def _tokenize(self, sentence):
        return re.findall(r'\w+', sentence.lower())

    def _bag_of_words(self, tokenized_sentence, words):
        bag = np.zeros(len(words), dtype=np.float32)
        for idx, w in enumerate(words):
            if w in tokenized_sentence: 
                bag[idx] = 1
        return bag

    def predict(self, sentence):
        if self.model is None:
            return {"tag": "unknown", "probability": 0.0, "emotion": "neutral"}

        tokens = self._tokenize(sentence)
        X = self._bag_of_words(tokens, self.all_words)
        X = torch.from_numpy(X.reshape(1, X.shape[0])).to(self.device)

        with torch.no_grad():
            intent_out, emotion_out = self.model(X)
            
            intent_prob = torch.softmax(intent_out, dim=1)
            intent_val, intent_idx = torch.max(intent_prob, dim=1)
            tag = self.tags[intent_idx.item()]
            
            emotion_prob = torch.softmax(emotion_out, dim=1)
            _, emotion_idx = torch.max(emotion_prob, dim=1)
            emotion = self.emotion_tags[emotion_idx.item()]

        return {
            "tag": tag,
            "probability": intent_val.item(),
            "emotion": emotion
        }

    def train(self, epochs=500):
        # Placeholder for training logic if needed
        print("️ NeuralChat: Training logic requested. (Not fully implemented in restoration)")
        pass
