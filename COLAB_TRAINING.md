# Training Nova on Google Colab

## Quick Start

1. **Upload to Colab:**
   - Go to [Google Colab](https://colab.research.google.com/)
   - Click "File" → "Upload notebook"
   - Upload `train_on_colab.ipynb`

2. **Enable GPU:**
   - Click "Runtime" → "Change runtime type"
   - Select "T4 GPU" (free tier)
   - Click "Save"

3. **Run Training:**
   - Click "Runtime" → "Run all"
   - When prompted, upload `training_data.jsonl` (contains multi-step reasoning examples)
   - Wait ~10-15 minutes

4. **Download Results:**
   - The notebook will automatically download `nova_skill_adapter.zip`
   - Extract the contents to `NOVA/models/nova_skill_adapter/`

## What Gets Trained

The model learns **Autonomous Reasoning** using:

- `<THOUGHT> logic </THOUGHT>` - For internal planning
- `[SKILL] command [/SKILL]` - For built-in tools
- `[SCRIPT] code [/SCRIPT]` - For Python automation
- `[CMD] command [/CMD]` - For system commands

## After Training

The [llm_manager.py](file:///c:/Users/SUNDARESH%20MONDAL/OneDrive/Desktop/project/NOVA/core/llm_manager.py) is already configured to load adapters if they exist in `models/nova_skill_adapter`. Just ensure the extracted files are there!

```python
# The system automatically looks for:
# models/nova_skill_adapter/adapter_config.json
# models/nova_skill_adapter/adapter_model.bin
```

## Troubleshooting

**"No GPU available"**: Make sure you selected T4 GPU in runtime settings

**"Out of memory"**: Reduce `per_device_train_batch_size` to 2 in the notebook

**Upload fails**: Make sure you're uploading the JSONL file, not a folder
