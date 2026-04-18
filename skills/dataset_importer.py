"""
Dataset Importer Skill
Enables importing conversation data from local CSV files (Kaggle style)
"""

import csv
import os
import json
from core.conversation_trainer import ConversationTrainer

trainer = ConversationTrainer()

def detect_columns(headers):
    """
    Detect question/answer columns from headers
    Returns (question_col_name, answer_col_name) or None
    """
    headers = [h.lower().strip() for h in headers]
    
    # Possible mappings
    q_candidates = ['question', 'query', 'user', 'input', 'instruction', 'prompt', 'context']
    a_candidates = ['answer', 'response', 'bot', 'output', 'reply', 'target']
    
    q_col = None
    a_col = None
    
    for h in headers:
        if h in q_candidates and not q_col:
            q_col = h
        elif h in a_candidates and not a_col:
            a_col = h
            
    if q_col and a_col:
        return q_col, a_col
        
    # Fallback: if we have 'text' and 'label' (classification), probably not conversation
    # If we have just two columns, assume Q -> A
    if len(headers) == 2:
        return headers[0], headers[1]
        
    return None, None

def cmd_import_csv(args):
    """
    Import a local CSV file
    Usage: import csv "path/to/file.csv" [limit 100]
    """
    # Parse limit
    limit = 1000  # Default safety limit
    if "limit" in args.lower():
        try:
            import re
            limit_match = re.search(r'limit\s+(\d+)', args, re.IGNORECASE)
            if limit_match:
                limit = int(limit_match.group(1))
        except: pass
        
    # Parse path (handle quotes)
    import re
    path_match = re.search(r'import csv\s+["\'](.+?)["\']', args, re.IGNORECASE)
    if not path_match:
        # Try without quotes
        args_clean = args.replace("import csv", "").strip()
        parts = args_clean.split(" limit ")
        path = parts[0].strip()
    else:
        path = path_match.group(1)
        
    if not os.path.exists(path):
        return f"❌ File not found: {path}"
        
    try:
        count = 0
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            
            # Detect columns
            if not reader.fieldnames:
                return "❌ Empty CSV or invalid format."
                
            q_col, a_col = detect_columns(reader.fieldnames)
            
            if not q_col or not a_col:
                return f"❌ Could not auto-detect columns. Found: {reader.fieldnames}. I need pair like 'Question/Answer', 'User/Bot', 'Input/Output'."
            
            print(f"📂 Importing from {q_col} -> {a_col}...")
            
            for row in reader:
                if count >= limit:
                    break
                    
                q = row.get(q_col, "").strip()
                a = row.get(a_col, row.get(a_col.lower(), "")).strip() # Case sensitive dict key fix? No, DictReader keys are as in file
                # Re-reading row with exact detected keys
                
                # Check actual keys in row (case sensitive usually in headers)
                # But we lowercased headers in detection logic
                # So let's find the actual key that matches our detected q_col (which might be lowercased version of real header)
                
                actual_q_key = next((k for k in row.keys() if k.lower().strip() == q_col), None)
                actual_a_key = next((k for k in row.keys() if k.lower().strip() == a_col), None)
                
                if actual_q_key and actual_a_key:
                    q_text = row[actual_q_key]
                    a_text = row[actual_a_key]
                    
                    if q_text and a_text and len(q_text) > 1 and len(a_text) > 1:
                        trainer.teach_response(q_text, a_text, category="csv_import", mood="neutral")
                        count += 1
        
        return f"✅ Import successful! Learned {count} new patterns from {os.path.basename(path)}."
        
    except Exception as e:
        return f"❌ Error importing CSV: {e}"

def cmd_create_sample_csv(args):
    """Create a sample CSV for the user to fill"""
    filename = "sample_training.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Question", "Answer"])
            writer.writerow(["What is Nova?", "Nova is an advanced AI assistant."])
            writer.writerow(["Who created you?", "I was created by my developer."])
            writer.writerow(["Do you like Python?", "Yes, it is my native language!"])
            
        return f"✅ Created '{filename}'. You can fill it with data and run: import csv \"{filename}\""
    except Exception as e:
        return f"Error creating sample: {e}"

def cmd_import_hf(args):
    """
    Import from Hugging Face Datasets and add directly to intents.json
    Usage: import hf "dataset_name" [limit 100]
    Example: import hf databricks/databricks-dolly-15k limit 50
    """
    try:
        from datasets import load_dataset
    except ImportError:
        return "❌ The 'datasets' library is missing. Install it with: pip install datasets"

    # Parse limit
    limit = 50  # Default limit for safety
    if "limit" in args.lower():
        try:
            import re
            limit_match = re.search(r'limit\s+(\d+)', args, re.IGNORECASE)
            if limit_match:
                limit = int(limit_match.group(1))
        except: pass
        
    # Parse dataset name
    import re
    name_match = re.search(r'import hf\s+["\']?([a-zA-Z0-9_/-]+)["\']?', args, re.IGNORECASE)
    if not name_match:
        return "❌ Please specify a dataset name. Example: import hf databricks/databricks-dolly-15k"
    
    dataset_name = name_match.group(1)
    
    print(f"🌍 Connecting to Hugging Face: {dataset_name} (Limit: {limit})...")
    
    try:
        # Load in streaming mode to save memory
        dataset = load_dataset(dataset_name, split="train", streaming=True)
        
        count = 0
        skipped = 0
        collected_pairs = []
        
        print("📥 Downloading and processing (this may take a moment)...")
        
        for i, row in enumerate(dataset):
            if count >= limit:
                break
                
            # Extract question/answer pairs based on dataset structure
            try:
                q_text = None
                a_text = None
                
                # 0. Dolly-15k Support (Instruction/Response)
                if 'instruction' in row and 'response' in row:
                    q_text = row['instruction']
                    a_text = row['response']

                # 1. DailyDialog Support (List of strings)
                elif 'dialog' in row:
                    dialog = row['dialog']
                    for j in range(len(dialog) - 1):
                        q_text = dialog[j]
                        a_text = dialog[j+1]
                        if len(q_text) > 2 and len(a_text) > 2:
                            collected_pairs.append((q_text, a_text))
                            count += 1
                            if count % 10 == 0: print(f"   Collected {count} pairs...")
                    continue

                # 2. Chatbot Arena Support
                elif 'conversation_a' in row:
                    winner = row.get('winner', 'model_a')
                    if winner == 'model_a':
                        conv = row.get('conversation_a', [])
                    elif winner == 'model_b':
                        conv = row.get('conversation_b', [])
                    else:
                        conv = row.get('conversation_a', [])
                    
                    # Extract pairs (User -> Assistant)
                    for j in range(len(conv) - 1):
                        msg1 = conv[j]
                        msg2 = conv[j+1]
                        
                        if msg1['role'] == 'user' and msg2['role'] == 'assistant':
                            q_text = msg1['content']
                            a_text = msg2['content']
                            if 3 < len(q_text) < 300 and 3 < len(a_text) < 500:
                                collected_pairs.append((q_text, a_text))
                                count += 1
                    continue
                
                # For single Q&A formats
                if q_text and a_text:
                    if len(q_text) > 2 and len(a_text) > 2 and len(q_text) < 300 and len(a_text) < 500:
                        collected_pairs.append((q_text, a_text))
                        count += 1
                        if count % 10 == 0: print(f"   Collected {count} pairs...")
                    else:
                        skipped += 1
                        
            except Exception as row_err:
                skipped += 1
                continue
        
        # Now append to intents.json
        if not collected_pairs:
            return "❌ No suitable pairs found in the dataset."
        
        print(f"\n💾 Adding {len(collected_pairs)} patterns to intents.json...")
        
        intents_file = os.path.join("userdata", "intents.json")
        with open(intents_file, 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
        
        # Create a new intent for this dataset
        safe_name = dataset_name.replace('/', '_').replace('-', '_')
        new_intent = {
            "tag": f"hf_{safe_name}",
            "patterns": [pair[0] for pair in collected_pairs],
            "responses": [pair[1] for pair in collected_pairs]
        }
        
        intents_data['intents'].append(new_intent)
        
        with open(intents_file, 'w', encoding='utf-8') as f:
            json.dump(intents_data, f, indent=4, ensure_ascii=False)
        
        return f"✅ Import complete! Added {len(collected_pairs)} new patterns to intents.json as tag '{new_intent['tag']}'. Run training to apply!"
        
    except Exception as e:
        return f"❌ Error importing HF dataset: {e}"

def register(dispatcher):
    dispatcher.register("import csv", cmd_import_csv)
    dispatcher.register("create sample csv", cmd_create_sample_csv)
    dispatcher.register("make sample csv", cmd_create_sample_csv)
    dispatcher.register("import hf", cmd_import_hf)
