import requests
import numpy as np
from pathlib import Path

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "bge-m3:latest"
CHAT_MODEL = "qwen3.5:4b"

def embed(texts):
    r = requests.post(f"{OLLAMA}/api/embed", json={"model": EMBED_MODEL, "input": texts})
    return np.array(r.json()["embeddings"])

def ask_llm(prompt):
    r = requests.post(f"{OLLAMA}/api/chat", json={
        "model": CHAT_MODEL, "stream": False,
        "messages": [{"role": "user", "content": prompt}]})
    return r.json()["message"]["content"]

chunks = []
for file in Path("docs").glob("*.md"):
    chunks += [p.strip() for p in file.read_text(encoding="utf-8").split("\n\n") if p.strip()]

chunk_vectors = embed(chunks)
#print(f"indexed {len(chunks)} chunks\n")

def retrieve(question, k=5):
    q = embed([question])[0]
    scores = chunk_vectors @ q /(np.linalg.norm(chunk_vectors, axis=1) * np.linalg.norm(q))
    return [chunks[i] for i in np.argsort(scores)[::-1][:k]]

while True:
    question = input("Kérdezz akármit a Kőrisliget Erdészeti és Logisztikai KFT.-ről!😊\n\n")
    context = "\n\n".join(retrieve(question))
    prompt = f"""Answer the question using ONLY the context below.
    Do not try to use anything else other than the context.
    If the answer isn't in the context, say "Erről nincs információm, hívj fel minket a telefonszámunkon!".
    
    Context:
    {context}
            
    Question: {question}"""
    print("\n" + ask_llm(prompt) + "\n")