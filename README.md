# Deutscher Nachrichten-Wortscanner

MVP für relative Worthäufigkeiten in deutschen Online-Nachrichten.

## Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Funktionsumfang
- RSS-Feeds als Quellen
- Google-News-Suche über RSS-Suchendpunkte (optional, abhängig von Verfügbarkeit)
- Artikeltext-Extraktion
- Wort-/Lemma-Zählung
- relative Häufigkeit je Zeitfenster
- Vergleich mehrerer Begriffe
- CSV-Export
- Quellenfilter

## Datenbasis
Der Scanner speichert standardmäßig Metadaten und extrahierten Artikeltext lokal. Prüfe vor produktiver Nutzung die Nutzungsbedingungen der jeweiligen Quelle. Für tagesschau.de existieren offizielle RSS-Feeds; deren Nutzungsbedingungen beschränken insbesondere Archivierung und Weitergabe.

Google News hat seit 2025 seine Publisher-Infrastruktur geändert; der Scanner behandelt Google News deshalb als zusätzliche Such-/Discovery-Quelle und nicht als vollständigen Ersatz für direkte Verlagsfeeds.
