import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
from core.scratch_llm import ScratchLLM
from core.tokenizer import CharTokenizer

# Hyperparameters
batch_size = 32
block_size = 128
max_iters = 5000
eval_interval = 500
learning_rate = 3e-4
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
n_embd = 128
n_head = 4
n_layer = 4
dropout = 0.2

# 1. Load Data
def load_data(filepath):
    if filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Flatten intents into text
            text = ""
            for intent in data.get('intents', []):
                for pattern in intent.get('patterns', []):
                    text += f"User: {pattern}\nNova: {intent.get('responses', [''])[0]}\n"
            return text
    elif filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def get_batch(data, split):
    # generate a small batch of data of inputs x and targets y
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i+block_size] for i in ix])
    y = torch.stack([data[i+1:i+block_size+1] for i in ix])
    x, y = x.to(device), y.to(device)
    return x, y

@torch.no_grad()
def estimate_loss(model, train_data, val_data):
    out = {}
    model.eval()
    for split, data in [('train', train_data), ('val', val_data)]:
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            X, Y = get_batch(data, split)
            logits, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out

def train(dataset_path, model_save_path=os.path.join("userdata", "models", "scratch_nova.pth")):
    text = load_data(dataset_path)
    if not text:
        print("❌ No data found at", dataset_path)
        return

    tokenizer = CharTokenizer()
    data = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    
    # Train/Val split
    n = int(0.9*len(data))
    train_data = data[:n]
    val_data = data[n:]

    model = ScratchLLM(vocab_size=tokenizer.vocab_size, n_embd=n_embd, n_head=n_head, n_layer=n_layer, block_size=block_size, dropout=dropout)
    m = model.to(device)
    
    # create a PyTorch optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    print(f" Training on {device}...")
    for iter in range(max_iters):

        # every once in a while evaluate the loss on train and val sets
        if iter % eval_interval == 0 or iter == max_iters - 1:
            losses = estimate_loss(model, train_data, val_data)
            print(f"step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

        # sample a batch of data
        xb, yb = get_batch(train_data, 'train')

        # evaluate the loss
        logits, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

    # Save the model
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'vocab': tokenizer.chars,
        'config': {
            'n_embd': n_embd,
            'n_head': n_head,
            'n_layer': n_layer,
            'block_size': block_size,
            'vocab_size': tokenizer.vocab_size
        }
    }, model_save_path)
    print(f"✅ Model saved to {model_save_path}")

if __name__ == "__main__":
    train(os.path.join("userdata", "intents.json"))
