# Manifest: Testbett Audio-Texttranskription

Alle geteilten Dateien. Freigegeben sind Testwerkzeuge (Generator, Referenzdaten, Fragen und Antworten, Bewertungsskripte) und Ergebnistabellen.

| Pfad | Zweck | Herkunft | Größe (Bytes) |
|---|---|---|---|
| `.gitignore` | schließt Caches und erzeugte WAV-Dateien aus | neu erstellt | 166 |
| `requirements.txt` | Python-Pakete der Testbett-Skripte | neu erstellt | 40 |
| `testbett/synth_tests.py` | erzeugt 6 synthetische Testclips (22,05 kHz Stereo, additive Synthese) mit exakter Referenz | Prototyp, Kopfkommentar bereinigt | 18.762 |
| `testbett/data/synth/T1.json` | Referenz T1: Pop-Folge C-Dur, 100 BPM | Prototyp, unverändert (identisch mit Neuerzeugung) | 9.418 |
| `testbett/data/synth/T2.json` | Referenz T2: a-Moll, 128 BPM, Intro, Lead, Breakdown | Prototyp, unverändert | 12.263 |
| `testbett/data/synth/T3.json` | Referenz T3: Ballade D-Dur, 70 BPM, Crescendo | Prototyp, unverändert | 7.406 |
| `testbett/data/synth/T4.json` | Referenz T4: Geräuschszene, 12 Ereignisse mit Richtung | Prototyp, unverändert | 1.498 |
| `testbett/data/synth/T5.json` | Referenz T5: Tonartwechsel C-Dur nach D-Dur | Prototyp, unverändert | 11.047 |
| `testbett/data/synth/T6.json` | Referenz T6: Tempowechsel 90 nach 120 BPM | Prototyp, unverändert | 9.811 |
| `testbett/score_transcription.py` | Metriken für Tempo, Tonart, Akkorde, Noten, Schlagzeug, Abschnitte und Ereignisse gegen die Referenz; Selbsttest | neu geschrieben aus den formatunabhängigen Prototyp-Metriken | 10.509 |
| `testbett/qa/questions.json` | 50 Fragen zu 6 Clips | Prototyp, Formatlegende entfernt, Audio-Zuordnung ergänzt | 4.663 |
| `testbett/qa/answers.json` | Referenzantworten mit Begründung | Prototyp, Fremdaufnahme als nicht enthalten markiert | 9.154 |
| `testbett/qa/judgements.json` | Einzelwertung pro Frage für T und C mit Konfidenz | Prototyp, Notizen entfernt | 7.969 |
| `testbett/qa/score_blind.py` | rechnet Kopfzahlen, Kategorien, Clips, Kalibrierung und Bootstrap-Intervalle | neu geschrieben | 5.557 |
| `ergebnisse/qa_auswertung.md` | Auswertung der Blind-QA | neu geschrieben aus der Prototyp-Auswertung | 5.869 |
| `ergebnisse/messwerte_synthetisch.md` | Messwerte auf T1 bis T6, Tokens pro Sekunde, Rechenzeit | neu geschrieben aus den Prototyp-Tabellen | 2.775 |
| `MANIFEST.md` | diese Liste | neu erstellt | - |

Summe der aufgeführten Dateien: 116.907 Bytes (0,12 MB). `README.md` und `assets/` werden getrennt gepflegt und sind hier nicht aufgeführt.

## Voraussetzungen

- Python 3.10+, `pip install -r requirements.txt`
- Aufrufe aus `testbett/`: `python synth_tests.py` (etwa 5 s), `python score_transcription.py --selftest`, `python qa/score_blind.py`
- clip5 der Blind-QA nutzt eine Fremdaufnahme, die nicht beiliegt

## Nicht enthalten

- Methodencode des Verfahrens und seine Analysekette
- das interne Textformat, seine Ausgaben und die daraus erzeugten QA-Eingaben
- verfahrensspezifische Auswertungsskripte der Verbesserungsrunden
- Fremdaufnahmen (Musik, Sprache, Naturgeräusche) und Zwischenergebnisse der Analyse
- erzeugte WAV-Dateien (etwa 19 MB); `synth_tests.py` erzeugt sie bitgleich neu
- Register, Messprotokolle und Entwurfsnotizen
