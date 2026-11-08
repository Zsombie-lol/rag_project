import requests
import numpy as np
import lancedb
from chunking import load_chunks
from ollama import chat
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from lancedb.index import FTS
from tools import fuvardij

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "bge-m3:latest"
CHAT_MODEL = "qwen3.5:4b"

db = lancedb.connect("./.lancedb")
func = get_registry().get("ollama").create(name=EMBED_MODEL)

def embed(texts):
    r = requests.post(f"{OLLAMA}/api/embed", json={"model": EMBED_MODEL, "input": texts})
    return np.array(r.json()["embeddings"])

def desc_llm(prompt, thinks=False):
    r = chat(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}], think=thinks)
    return r.message.content

class Chunk(LanceModel):
    text: str = func.SourceField()
    source: str
    vector: Vector(func.ndims()) = func.VectorField()

if "chunks" in db.list_tables() and db.open_table("chunks").count_rows() > 0:
    table = db.open_table("chunks")
else:
    chunks = load_chunks()
    print(len(chunks))
    table = db.create_table("chunks", schema=Chunk, mode="overwrite", exist_ok=True)
    table.add([{"text": desc_llm(f"Make a brief summary for this chunk in my vector database: {c}") + "\n" + c, "source": s} for c,s in chunks])
    table.create_index("text", config=FTS())

def retrieve(question, k=5):
    rows = (table.search(question, query_type="hybrid", vector_column_name="vector", fts_columns="text").limit(k).to_pydantic(Chunk))
    return [r.text for r in rows]

def kereses_dokumentumban(kerdes: str) -> str:
    """Keresés a Kőrisliget Kft. kézikönyvében és GYIK-jében. Használd minden, a céggel,
    szolgáltatásokkal, árlistával, szabályokkal vagy folyamatokkal kapcsolatos kérdésnél.

    Args:
        kerdes: a keresett téma vagy kérdés magyarul
    """
    return "\n\n".join(retrieve(kerdes))

SYSTEM = """Te a Kőrisliget Erdészeti és Logisztikai KFT. ügyfélszolgálati chatbotja vagy. Magyarul válaszolj.
Szabályok:
1. Cégre vonatkozó kérdésnél MINDIG hívd meg a kereses_dokumentumban eszközt, és csak a találatokból válaszolj.
2. Szállítási díj kiszámításához használd a fuvardij eszközt, ne számolj fejből. Ha a jármű típusa vagy a távolság nincs megadva, kérdezd meg az ügyféltől.
3. Ha a válasz nincs a találatokban: "Erről nincs információm, hívj fel minket a telefonszámunkon!"
4. Ha a kérdés nem a céggel kapcsolatos: "Erről nem beszélhetünk, használj erre egyéb AI agent-et." """

messages = [{"role": "system", "content": SYSTEM}]


TOOLS = [fuvardij, kereses_dokumentumban]
TOOL_MAP = {f.__name__: f for f in TOOLS}

def run_chat():
    for _ in range(6):
        resp = chat(model=CHAT_MODEL, messages=messages, tools=TOOLS, think=False)
        messages.append(resp.message)
        if not resp.message.tool_calls:
            return resp.message.content
        for call in resp.message.tool_calls:
            name, args = call.function.name, call.function.arguments
            print(f"[eszköz: {name} {args}]")
            fn = TOOL_MAP.get(name)
            try:
                result = str(fn(**args)) if fn else f"Ismeretlen eszköznév: {name}"
            except Exception as e:
                result = f"Hiba az eszköz futtatásakor: {e}"
            messages.append({"role":"tool", "tool_name": name, "content": result})
    return f"Sajnos nem sikerült, próbáld meg újra."
while True:
    question = input("Kérdezz a Kőrisliget Erdészeti és Logisztikai KFT.-ről!😊\n\n")
    messages.append({"role": "user", "content": question})
    print("\n" + run_chat() + "\n")