import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import yaml
from scanner import db, add_feed, add_google_news, analyze, load_articles

st.set_page_config(page_title="News Word Scanner V2", page_icon="📰", layout="wide")

st.title("📰 Deutscher Nachrichten-Wortscanner")
st.caption("Relative Worthäufigkeit in erfassten Online-Nachrichten")

# Always initialize DB and catch errors visibly.
try:
    db()
except Exception as e:
    st.error(f"Datenbankfehler: {e}")
    st.stop()

with st.sidebar:
    st.header("1. Wörter")
    term_text = st.text_area(
        "Wörter oder Begriffe, durch Komma getrennt",
        "migration, einwanderung, flüchtlinge, asyl",
        height=90
    )
    terms = [x.strip().lower() for x in term_text.split(",") if x.strip()]

    st.header("2. Zeitraum-Auflösung")
    freq_label = st.selectbox("Aggregieren nach", ["Woche", "Tag", "Monat"], index=0)
    freq = {"Tag":"D", "Woche":"W", "Monat":"M"}[freq_label]

    st.header("3. Quellen")
    default_sources = {
        "tagesschau": "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
        "tagesschau_inland": "https://www.tagesschau.de/inland/index~rss2.xml",
        "tagesschau_ausland": "https://www.tagesschau.de/ausland/index~rss2.xml",
        "tagesschau_wirtschaft": "https://www.tagesschau.de/wirtschaft/index~rss2.xml",
        "tagesschau_wissen": "https://www.tagesschau.de/wissen/index~rss2.xml",
    }
    selected = st.multiselect("RSS-Feeds", list(default_sources), default=["tagesschau"])
    if st.button("▶ Quellen scannen", use_container_width=True):
        if not selected:
            st.warning("Bitte mindestens eine Quelle auswählen.")
        else:
            progress = st.progress(0)
            messages=[]
            for i, name in enumerate(selected):
                try:
                    n=add_feed(name, default_sources[name], 100, True)
                    messages.append(f"{name}: {n} neue Artikel")
                except Exception as e:
                    messages.append(f"{name}: FEHLER – {e}")
                progress.progress((i+1)/len(selected))
            for m in messages:
                st.write(m)

    st.header("Google News")
    google_query = st.text_input("Suchbegriff", "Migration")
    if st.button("🔎 Google News scannen", use_container_width=True):
        try:
            n=add_google_news(google_query, 100)
            st.success(f"{n} neue Google-News-Einträge.")
        except Exception as e:
            st.error(f"Google News Fehler: {e}")

    st.header("Demo")
    st.caption("Damit du das Dashboard sofort testen kannst.")
    demo = st.checkbox("Demo-Daten verwenden", value=True)

if demo:
    dates = pd.date_range("2026-01-04", periods=36, freq="W")
    data=[]
    base={"migration":0.10,"einwanderung":0.05,"flüchtlinge":0.08,"asyl":0.04}
    for i,d in enumerate(dates):
        for j,t in enumerate(terms or ["migration"]):
            import math
            v=base.get(t,0.04) + 0.025*math.sin(i/3+j) + 0.012*(i/36) + (0.06 if i in [15,16] and j==0 else 0)
            data.append({"period":d,"term":t,"occurrences":round(max(v,0)*1000),"total_words":100000,"articles":120})
    result=pd.DataFrame(data)
    result["relative_percent"]=result["occurrences"]/result["total_words"]*100
    demo_note=True
else:
    result=analyze(terms, None, freq)
    demo_note=False

arts=load_articles()
c1,c2,c3=st.columns(3)
c1.metric("Gespeicherte Artikel", len(arts))
c2.metric("Analysierte Wörter", f"{int(arts['text'].fillna('').map(lambda x: len(str(x).split())).sum()):,}" if not arts.empty else "0")
c3.metric("Begriffe", len(terms))

if demo_note:
    st.info("Demo-Daten sind aktiviert. Deaktiviere links „Demo-Daten verwenden“, um echte Daten zu sehen.")

if result.empty:
    st.warning("Noch keine analysierbaren Artikel. Scanne links zuerst eine Quelle.")
    st.stop()

st.subheader("Relative Worthäufigkeit über die Zeit")
pivot=result.pivot(index="period", columns="term", values="relative_percent").reset_index()
long=pivot.melt(id_vars="period", var_name="term", value_name="relative_percent")
fig=px.line(long, x="period", y="relative_percent", color="term",
            markers=True, labels={"period":"Zeitraum","relative_percent":"Relative Häufigkeit (%)","term":"Wort"})
fig.update_layout(hovermode="x unified", height=520, legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Kennzahlen")
show=result.copy()
show["relative_percent"]=show["relative_percent"].map(lambda x: f"{x:.5f}%")
st.dataframe(show.sort_values(["period","term"], ascending=False), use_container_width=True, hide_index=True)

st.download_button("⬇ Aggregierte CSV", result.to_csv(index=False).encode("utf-8"), "news_word_frequencies.csv", "text/csv")
if not arts.empty:
    st.download_button("⬇ Artikel-Rohdaten CSV", arts.to_csv(index=False).encode("utf-8"), "news_articles.csv", "text/csv")

st.caption("V2 gewichtet Zeiträume über tatsächliche Wortmengen: relative Häufigkeit = Wortvorkommen / alle analysierten Wörter × 100.")
