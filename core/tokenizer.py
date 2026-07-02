
import json
import os

class CharTokenizer:
    """ Simple character-level tokenizer for NOVA's scratch LLM """
    def __init__(self, vocab=None):
        if vocab:
            self.chars = vocab
        else:
            # Standard ASCII + symbols + common emoji placeholders
            self.chars = sorted(list(set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " + 
                "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~\n\t" + 
                "✨"
            )))
        
        self.vocab_size = len(self.chars)
        self.stoi = { ch:i for i,ch in enumerate(self.chars) }
        self.itos = { i:ch for i,ch in enumerate(self.chars) }

    def encode(self, s):
        return [self.stoi.get(c, self.stoi.get(' ', 0)) for c in s] # fallback to space if char unknown

    def decode(self, l):
        return ''.join([self.itos.get(i, '?') for i in l])

    def save(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.chars, f, ensure_ascii=False)

    @classmethod
    def load(cls, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                vocab = json.load(f)
            return cls(vocab)
        return cls()
