import os
from huggingface_hub import hf_hub_download

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_REPO = 'Qwen/Qwen2.5-0.5B-Instruct-GGUF'
MODEL_FILENAME = 'qwen2.5-0.5b-instruct-q2_k.gguf'

os.makedirs(MODEL_DIR, exist_ok=True)

print(f"Downloading {MODEL_FILENAME} (~300 MB)...")
local_path = hf_hub_download(
    repo_id=MODEL_REPO,
    filename=MODEL_FILENAME,
    local_dir=MODEL_DIR,
)
print(f"Model downloaded to: {local_path}")
