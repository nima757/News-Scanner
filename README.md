# News Word Scanner V2

Robuster Streamlit-MVP zur Messung der relativen Worthäufigkeit in deutschen Online-Nachrichten.

## Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## V2
- sofort sichtbares Dashboard, auch ohne Daten
- Testmodus mit Demo-Daten
- echte RSS-Feeds
- Google-News-RSS-Suche
- Artikeltext-Extraktion
- tägliche / wöchentliche / monatliche Aggregation
- korrekte Gesamtquote: Summe Wortvorkommen / Summe aller Wörter
- interaktives Plotly-Diagramm
- Quellenfilter
- Rohdaten- und Aggregat-CSV-Export
- sichtbare Fehlerdiagnose
- SQLite-Datenbank
- automatische Erkennung neuer Artikel per URL

## Hinweis zur Datenbasis
Das Tool erfasst nur Quellen, die über zugängliche Feeds bzw. Seiten erreichbar sind. Es ist nicht garantiert, dass damit "alle deutschen Zeitungen" vollständig erfasst werden. Paywalls, robots.txt, Lizenzbedingungen und technische Änderungen können die Abdeckung einschränken.

Bei tagesschau.de gibt es offizielle RSS-Feeds; deren Nutzungsbedingungen sind zu beachten.
