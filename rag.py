import os
import uuid
import warnings
from pathlib import Path
import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_data')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_REPO = 'Qwen/Qwen2.5-0.5B-Instruct-GGUF'
MODEL_FILENAME = 'qwen2.5-0.5b-instruct-q2_k.gguf'
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

_llm = None
_client = None
_collection = None


def get_llm():
    global _llm
    if _llm is not None:
        return _llm
    if not os.path.exists(MODEL_PATH):
        _download_model()
    from llama_cpp import Llama
    _llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,
        n_threads=1,
        n_gpu_layers=0,
        verbose=False,
    )
    return _llm


# Pre-load model at import time
get_llm()


def _download_model():
    print(f"Downloading {MODEL_FILENAME} from HuggingFace...")
    try:
        from huggingface_hub import hf_hub_download
        hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            local_dir=MODEL_DIR,
        )
        print("Download complete!")
    except ImportError:
        raise RuntimeError(
            "Model not found and huggingface_hub not installed. "
            "Run: pip install huggingface_hub\n"
            "Or download manually:\n"
            f"  mkdir -p {MODEL_DIR}\n"
            f"  cd {MODEL_DIR}\n"
            f"  curl -L -o {MODEL_FILENAME} "
            f"https://huggingface.co/{MODEL_REPO}/resolve/main/{MODEL_FILENAME}"
        )


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    global _collection
    try:
        if _collection is not None:
            _collection.count()
            return _collection
    except Exception:
        _collection = None
    client = get_client()
    try:
        _collection = client.get_collection('documents')
    except Exception:
        _collection = client.create_collection('documents')
    return _collection


def reset_collection():
    global _collection
    _collection = None


def add_document(text, filename):
    chunks = split_text(text, 500, 50)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{'source': filename, 'chunk': i} for i in range(len(chunks))]
    collection = get_collection()
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def split_text(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def search(query, n_results=2):
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    if results['documents']:
        return results['documents'][0]
    return []


def generate(query, context):
    llm = get_llm()
    if context:
        system_prompt = (
            "Tu es un assistant commercial pour Optimus AI, une entreprise spécialisée "
            "dans l'automatisation intelligente et l'intelligence artificielle. "
            "Réponds toujours en français en utilisant uniquement le contexte fourni."
        )
        user_prompt = f"Contexte :\n{context}\n\nQuestion : {query}"
    else:
        system_prompt = (
            "Tu es un assistant commercial pour Optimus AI, une entreprise spécialisée "
            "dans l'automatisation intelligente et l'intelligence artificielle. "
            "Réponds toujours en français de manière concise et utile."
        )
        user_prompt = query
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=100,
        temperature=0.3,
        stop=['<|im_end|>', '</s>'],
    )
    return response['choices'][0]['message']['content'].strip()


def get_document_count():
    collection = get_collection()
    return collection.count()
