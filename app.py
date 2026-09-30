import streamlit as st
import pandas as pd
from scanner import init_db, add_feed, add_google_news, scan

st.set_page_config(page_title="News Word Scanner", layout="wide")
init_db()

st.title("🇩🇪 Deutscher Nachrichten-Wortscanner")
st.caption("Relative Worthäufigkeit in erfassten Nachrichtenartikeln")

with st.sidebar:
    st.header("Quellen")
    feeds = {
        "tagesschau": "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
        "tagesschau_inland": "https://www.tagesschau.de/inland/index~rss2.xml",
        "tagesschau_wirtschaft": "https://www.tagesschau.de/wirtschaft/index~rss2.xml",
    }
    selected = st.multiselect("Feeds abrufen", list(feeds), default=["tagesschau"])
    if st.button("Feeds jetzt scannen"):
        total=0
        for name in selected:
            total += add_feed(name, feeds[name])
        st.success(f"{total} neue Feed-Einträge gespeichert.")

    st.header("Google News")
    gquery = st.text_input("Suchbegriff für Google News", "Deutschland")
    if st.button("Google News scannen"):
        n = add_google_news(gquery, 100)
        st.success(f"{n} neue Google-News-Einträge gespeichert.")

terms = st.text_input("Wörter (Komma-getrennt)", "migration, einwanderung, flüchtlinge, asyl")
terms = [x.strip().lower() for x in terms.split(",") if x.strip()]

df = scan(terms)
if df.empty:
    st.info("Noch keine Artikel. Wähle links einen Feed und starte den Scan.")
    st.stop()

agg = df.groupby(["day","term"], as_index=False).agg(
    relative=("relative","mean"),
    occurrences=("count","sum"),
    articles=("title","nunique"),
    words=("words","sum")
)
agg["relative_percent"] = agg["relative"] * 100

st.subheader("Zeitreihe")
chart = agg.pivot(index="day", columns="term", values="relative_percent")
st.line_chart(chart)

st.subheader("Tabelle")
st.dataframe(agg.sort_values(["day","term"], ascending=False), use_container_width=True)

st.download_button("CSV exportieren",
                   agg.to_csv(index=False).encode("utf-8"),
                   "news_word_frequencies.csv",
                   "text/csv")
