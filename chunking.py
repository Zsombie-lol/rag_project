import re
from pathlib import Path


def split_markdown(text, source, max_chars=1500):
    title, h2, h3 = "", "", ""
    buf, out = [], []

    def flush():
        body = "\n".join(buf).strip()
        buf.clear()
        if not body:
            return
        header = " > ".join(x for x in (title, h2, h3) if x)
        paras, cur = body.split("\n\n"), ""
        for p in paras:
            if cur and len(cur) + len(p) > max_chars:
                out.append((f"{header}\n\n{cur.strip()}", source))
                cur = ""
            cur += p + "\n\n"
        if cur.strip():
            out.append((f"{header}\n\n{cur.strip()}", source))

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            flush(); h2, h3 = line[3:].strip(), ""
        elif line.startswith("### "):
            flush(); h3 = line[4:].strip()
        elif line.strip() != "---":
            buf.append(line)
    flush()
    return out



import re

def split_faq(text, source):
    category, q, a, out = "", None, [], []

    def flush():
        if q:
            body = f"Kérdés: {q}\nVálasz: {' '.join(a)}"
            head = f"{category}\n" if category else ""
            out.append((head + body, source))

    for line in text.splitlines():
        m = re.match(r"\*\*\d+\.\s*(.+?)\*\*\s*(.*)", line)
        if line.startswith("###"):
            flush(); q, a = None, []
            category = re.sub(r"^#+\s*[\d.]*\s*", "", line).strip()
        elif m:
            flush(); q, a = m.group(1).strip(), [m.group(2).strip()] if m.group(2).strip() else []
        elif line.strip() and q:
            a.append(line.strip())
    flush()
    return out


def load_chunks(folder="docs"):
    chunks = []
    for file in sorted(Path(folder).glob("*.md")):
        text = file.read_text(encoding="utf-8")
        if "faq" in file.stem.lower():
            chunks += split_faq(text, file.name)
        else:
            chunks += split_markdown(text, file.name)
    return chunks