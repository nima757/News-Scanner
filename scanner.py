import re, sqlite3, hashlib
from datetime import datetime, timezone
import feedparser
import trafilatura
import pandas as pd
import requests
from urllib.parse import quote_plus

DB = "news.db"

def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS articles(
      id TEXT PRIMARY KEY, source TEXT, title TEXT, url TEXT UNIQUE,
      published TEXT, text TEXT
    );
    """)
    con.commit(); con.close()

def clean_text(html_or_text):
    if not html_or_text: return ""
    extracted = trafilatura.extract(html_or_text, include_comments=False, include_tables=False)
    return extracted or re.sub(r"<[^>]+>", " ", html_or_text)

def add_feed(source, url, limit=100):
    feed = feedparser.parse(url)
    con = sqlite3.connect(DB)
    n = 0
    for e in feed.entries[:limit]:
        link = e.get("link","").strip()
        if not link: continue
        raw = e.get("summary","") + "\n" + e.get("content",[{}])[0].get("value","")
        text = clean_text(raw)
        # Wenn der Feed nur einen Teaser enthält, versuchen wir den öffentlich
        # erreichbaren Artikeltext von der verlinkten Seite zu extrahieren.
        if len(text.split()) < 80:
            try:
                html = requests.get(link, timeout=15, headers={"User-Agent":"NewsWordScanner/0.1"}).text
                full = clean_text(html)
                if len(full.split()) > len(text.split()):
                    text = full
            except Exception:
                pass
        published = e.get("published", e.get("updated",""))
        aid = hashlib.sha256(link.encode()).hexdigest()
        try:
            con.execute("INSERT INTO articles VALUES (?,?,?,?,?,?)",
                        (aid, source, e.get("title",""), link, published, text))
            n += 1
        except sqlite3.IntegrityError:
            pass
    con.commit(); con.close()
    return n

def tokenize(text):
    return re.findall(r"[A-Za-zÄÖÜäöüß]+", text.lower())

def frequency(words, terms):
    total = len(words)
    if not total: return {t: 0 for t in terms}
    return {t: words.count(t.lower()) / total for t in terms}

def scan(terms, source=None):
    con = sqlite3.connect(DB)
    q = "SELECT source,title,url,published,text FROM articles"
    params=[]
    if source:
        q += " WHERE source=?"; params.append(source)
    df = pd.read_sql_query(q, con, params=params)
    con.close()
    if df.empty: return pd.DataFrame()
    rows=[]
    for _, r in df.iterrows():
        words = tokenize(r.text or "")
        vals = frequency(words, terms)
        try: dt = pd.to_datetime(r.published, utc=True)
        except: dt = pd.NaT
        for term, rel in vals.items():
            rows.append({"date": dt, "source": r.source, "title": r.title,
                         "url": r.url, "term": term, "relative": rel,
                         "count": int(rel*len(words)), "words": len(words)})
    out = pd.DataFrame(rows)
    out["day"] = out["date"].dt.date
    return out

if __name__ == "__main__":
    init_db()
    print("DB initialisiert.")


def add_google_news(query, limit=100):
    """Google-News-Suche als zusätzliche Discovery-Quelle."""
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=de&gl=DE&ceid=DE:de"
    return add_feed("google_news:" + query, url, limit)
