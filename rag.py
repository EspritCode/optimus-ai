import os
import uuid
import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_data')
os.makedirs(CHROMA_DIR, exist_ok=True)

_client = None
_collection = None


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
    chunks = split_text(text, 200, 20)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{'source': filename, 'chunk': i} for i in range(len(chunks))]
    collection = get_collection()
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def split_text(text, chunk_size=200, overlap=20):
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
    from mistralai import Mistral
    api_key = os.environ.get('MISTRAL_API_KEY')
    if not api_key:
        return "Erreur : clé API Mistral non configurée."
    client = Mistral(api_key=api_key)
    if context:
        words = context.split()
        if len(words) > 300:
            context = ' '.join(words[:300])
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
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        max_tokens=200,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def get_document_count():
    collection = get_collection()
    return collection.count()
