import sqlite3, hashlib, re
from datetime import datetime, timezone
from urllib.parse import quote_plus
import feedparser
import requests
import trafilatura
import pandas as pd

DB = "news.db"
UA = "Mozilla/5.0 (NewsWordScanner/2.0)"

def db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS articles(
        id TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT, url TEXT UNIQUE,
        published TEXT, text TEXT, fetched_at TEXT)""")
    con.commit()
    return con

def clean_text(value):
    if not value:
        return ""
    try:
        x = trafilatura.extract(value, include_comments=False, include_tables=False)
        if x:
            return x
    except Exception:
        pass
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()

def article_text(url, fallback=""):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        r.raise_for_status()
        txt = clean_text(r.text)
        if len(txt.split()) >= max(80, len(fallback.split())):
            return txt
    except Exception:
        pass
    return clean_text(fallback)

def add_feed(source, url, limit=100, fetch_pages=True):
    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError("Feed konnte nicht gelesen werden.")
    con = db()
    added = 0
    for e in feed.entries[:limit]:
        link = str(e.get("link","")).strip()
        if not link:
            continue
        title = str(e.get("title","")).strip()
        fallback = str(e.get("summary",""))
        if e.get("content"):
            fallback += "\n" + str(e.get("content")[0].get("value",""))
        txt = article_text(link, fallback) if fetch_pages else clean_text(fallback)
        published = str(e.get("published", e.get("updated","")))
        aid = hashlib.sha256(link.encode("utf-8")).hexdigest()
        try:
            con.execute("INSERT INTO articles VALUES (?,?,?,?,?,?,?)",
                (aid, source, title, link, published, txt,
                 datetime.now(timezone.utc).isoformat()))
            added += 1
        except sqlite3.IntegrityError:
            pass
    con.commit(); con.close()
    return added

def add_google_news(query, limit=100):
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=de&gl=DE&ceid=DE:de"
    return add_feed("Google News: " + query, url, limit, fetch_pages=True)

def tokenize(text):
    return re.findall(r"[A-Za-zÄÖÜäöüß]+(?:[-'][A-Za-zÄÖÜäöüß]+)*", str(text).lower())

def load_articles(source=None):
    con = db()
    q = "SELECT source,title,url,published,text FROM articles"
    params = []
    if source and source != "Alle":
        q += " WHERE source=?"
        params.append(source)
    df = pd.read_sql_query(q, con, params=params)
    con.close()
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["date"] = df["date"].fillna(pd.Timestamp.now(tz="UTC"))
    return df

def analyze(terms, source=None, freq="W"):
    arts = load_articles(source)
    if arts.empty:
        return pd.DataFrame()
    terms = [t.lower().strip() for t in terms if t.strip()]
    rows = []
    for _, a in arts.iterrows():
        words = tokenize(a["text"])
        if not words:
            continue
        counts = {t: sum(1 for w in words if w == t) for t in terms}
        bucket = a["date"].to_period(freq).start_time
        for t, c in counts.items():
            rows.append({
                "period": bucket, "term": t, "occurrences": c,
                "total_words": len(words), "articles": 1
            })
    if not rows:
        return pd.DataFrame()
    x = pd.DataFrame(rows)
    g = x.groupby(["period","term"], as_index=False).agg(
        occurrences=("occurrences","sum"),
        total_words=("total_words","sum"),
        articles=("articles","sum")
    )
    g["relative_percent"] = (g["occurrences"] / g["total_words"] * 100).fillna(0)
    return g.sort_values(["period","term"])
