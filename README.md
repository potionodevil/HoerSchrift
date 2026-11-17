# HörSchrift

**Reine Text-Sprachmodelle erfassen Musik, Geräusche und Richtung, ohne Audio-Training.**

![Status](https://img.shields.io/badge/Status-Forschungsprototyp-orange)
![Sprache](https://img.shields.io/badge/Sprache-Deutsch-blue)
![Lizenz](https://img.shields.io/badge/Lizenz-Alle%20Rechte%20vorbehalten-lightgrey)

Forschungsprototyp 0.3.1, nicht veröffentlicht. Stand 17.11.2026.

## Auf einen Blick

- Ein Sprachmodell ohne Audiozugang beantwortet 92,0 % von 44 Faktenfragen zu Audio-Clips richtig. Ohne Eingabe sind es 58,0 % (gemessen).
- Auf 5 synthetischen Musikstücken stimmen Tonart (5 von 5) und Dur/Moll-Akkorde (100 %). Der Tempofehler liegt bei 0,90 BPM (gemessen).
- Die Ausgabe kostet 31 Tokens pro Sekunde Audio im Median, so viel wie Gemini mit 32 (gemessen).
- Eine Minute Audio braucht 4,3 bis 5,2 Sekunden auf einem CPU-Kern (gemessen).

Schreibweise: Tok/s heißt Tokens pro Sekunde Audio. F1 ist das harmonische Mittel aus Precision und Recall.

## Problem

Das beste Audio-Sprachmodell liegt 18,7 Punkte hinter Menschen. Reine Text-Sprachmodelle hören gar nicht.

MMAU-Pro, 5.305 Expertenfragen, Stand August 2025 (Genauigkeit in %):

| System | Gesamt | Musik | Geräusch | Raum |
|---|---|---|---|---|
| Mensch | 77,9 | 70,5 | 78,2 | 88,2 |
| Gemini 2.5 Flash | 59,2 | 64,9 | 51,9 | 36,3 |
| GPT-4o-Audio | 52,5 | 63,1 | 44,7 | 21,4 |
| Qwen2.5-Omni-7B | 52,2 | 61,5 | 47,6 | 41,2 |
| Zufall | 23,4 | 26,1 | 28,3 | 21,2 |

- Beim Raumhören beträgt der Abstand zum Menschen 47,0 Punkte, bei Musik 5,6 Punkte (berechnet).
- Audio-Sprachmodelle brauchen einen gelernten Audio-Encoder mit 12,5 bis 50 Positionen pro Sekunde und Zugriff auf die Modellgewichte. Geschlossene Text-Modelle lassen sich so nicht nachrüsten.
- Transkription mit Whisper liefert nur Wörter, etwa 3,3 Tok/s bei 150 Wörtern pro Minute. Tonhöhe, Musik, Geräusche und Richtung fehlen.
- Rohes Audio als Zahlentext kostet 44.594 Tok/s bei 16 kHz (gemessen). Ein Kontext mit 200.000 Tokens wäre nach 4,5 Sekunden voll.

## Ergebnisse

Testbedingungen: 5 synthetische Musikstücke mit exakter Wahrheit, 1 synthetische Geräuschszene mit 12 Ereignissen, 13 echte Aufnahmen (Orchester, Instrumentalstücke, gelesene Sprache, Walgesang, Vogelruf). Ein CPU-Kern. Tokens gezählt mit tiktoken o200k_base.

### Musik und Geräusche

| Größe | Ergebnis | Basis | Art |
|---|---|---|---|
| Tempo | mittlerer Fehler 0,90 BPM, höchstens 2,35 BPM | 5 Stücke | gemessen |
| Tempowechsel 90 auf 120 BPM | auf 0,15 BPM genau | 1 Stück | gemessen |
| Tonart | 5 von 5 richtig, Wechsel C-Dur nach D-Dur in Takt 9 gefunden | 5 Stücke | gemessen |
| Akkorde pro Halbtakt, Dur/Moll | 100 % | 160 Halbtakte | gemessen |
| Akkorde inklusive Septimen | 95,6 % | 160 Halbtakte | gemessen |
| Melodietöne | F1 0,90 | 300 Noten | gemessen |
| Basstöne | F1 0,94 | 272 Noten | gemessen |
| Schlagzeugschläge | F1 0,98 | 4 Stücke | gemessen |
| Formteilgrenzen, 1 Takt Toleranz | F1 0,87 | 6 Grenzen | gemessen |
| Geräuschereignisse | 12 von 12 gefunden, Klasse und Richtung 100 % | 1 Szene | gemessen |
| Tonhöhe und Einsatzzeit der Ereignisse | 6 Cent und 0,7 ms Fehler | 1 Szene | gemessen |
| Inhaltsklasse Musik, Sprache, Szene | 13 von 13 echt, 6 von 6 synthetisch | auf denselben Dateien abgestimmt | gemessen |

### Tokenrate

| Darstellung | Tok/s | 200.000 Tokens reichen für | Art |
|---|---|---|---|
| rohes Audio als Text, 16 kHz | 44.594 | 4,5 s | gemessen |
| Whisper-Encoder | 50 | 67 min | Literatur |
| Gemini API | 32 | 104 min | Literatur |
| HörSchrift Standard, Median über Dateien ab 10 s | 31 (19 bis 49) | 108 min | gemessen |
| HörSchrift Standard, 7 echte Musikdateien | 34,3 | 97 min | gemessen |
| Qwen2-Audio | 25 | 133 min | Literatur |
| HörSchrift kompakt, Median | 20 (10 bis 33) | 167 min | gemessen |
| Qwen3-Omni | 12,5 | 4,4 h | Literatur |
| Whisper-Transkript, nur Wörter | 3,3 | 17 h | berechnet |

HörSchrift spart gegenüber Audio-Encodern keine Kontextplätze. Jedes Text-Sprachmodell liest die Ausgabe aber ohne Audio-Training und ohne Audioeingang.

### Blindtest

50 Fragen zu 6 Clips: 5 synthetische Clips und 1 echte Orchesteraufnahme (Brahms). Leser und Kontrolle: Claude Opus 5.5 ohne Audiozugang. Die Kontrolle sah nur die Fragen (gemessen).

| Menge | Fragen | HörSchrift | ohne Eingabe | Abstand in Punkten |
|---|---|---|---|---|
| Faktenfragen mit sicherer Wahrheit | 44 | 92,0 % | 58,0 % | +34,1 |
| davon offene Fragen | 35 | 95,7 % | 52,9 % | +42,9 |
| davon geschlossene Fragen (2 bis 3 Optionen) | 9 | 7 von 9 | 7 von 9 | 0 |
| 5 synthetische Clips | 39 | 97,4 % | 57,7 % | +39,7 |
| echte Aufnahme, Streichorchester | 5 | 50,0 % | 60,0 % | minus 10,0 |

| Kategorie | Fragen | HörSchrift | ohne Eingabe |
|---|---|---|---|
| Tonart und Tongeschlecht | 5 | 100 % | 50,0 % |
| Tempo und Takt | 10 | 100 % | 65,0 % |
| Harmonie | 5 | 100 % | 70,0 % |
| Ereignisse und Richtung | 9 | 88,9 % | 61,1 % |
| Klangfarbe und Instrument | 9 | 72,2 % | 38,9 % |

- Das 95-%-Bootstrap-Intervall des Abstands reicht von +17,5 bis +46,1 Punkten über Clips und von +20,5 bis +47,7 über Fragen.
- Gepaart gewinnt HörSchrift 22 Fragen, die Kontrolle 2, 20 enden gleich.
- Alle 4 Fehler im Hauptergebnis stammen aus der Ausgabe, 0 aus dem Lesen. Drei betreffen Instrument, Ensemble und Genre der echten Aufnahme.

### Störungstest

Prüfrunde 1, 5 synthetische Stücke (gemessen):

| Bedingung | Akkorde Dur/Moll | Tonart (MIREX) | Melodie F1 |
|---|---|---|---|
| sauber | 100 % | 1,00 | 0,90 |
| Rauschen, SNR 10 dB | 99,4 % | 0,86 | 0,89 |
| Tiefpass 3,5 kHz, mono | 100 % | 1,00 | 0,90 |
| Nachhall 1,2 s | 84,4 % | 0,66 | 0,85 |
| alle Störungen kombiniert | 95,0 % | 0,60 | 0,82 |

- Verstimmung von minus 40 bis plus 40 Cent: Tonart und Akkorde bleiben bei 1,00 (Prüfrunde 1, Version 0.3.1).
- 7 echte Aufnahmen nach drei Veränderungen, darunter Tempo mal 1,1 und Tonhöhe plus 1 Halbton: Die Tonart bleibt in 100 % der Fälle konsistent, das Tempo in 29 bis 71 %. Insgesamt verhalten sich 74,6 % der Angaben wie erwartet. Das Ziel von 90 % ist verfehlt.

### Rechenzeit und Latenz

- 844 Sekunden Audio laufen in 73,7 Sekunden durch, Echtzeitfaktor 0,087 (gemessen).
- In Abschnitten von 8 Sekunden kostet jeder Abschnitt etwa 1 Sekunde CPU. Die Latenz liegt damit bei etwa 9 Sekunden (gemessen).
- Tempo und Akkorde stimmen ab 4 Sekunden Audio, die Dur/Moll-Entscheidung braucht etwa 16 Sekunden (gemessen).
- Eine Latenz unter 1 Sekunde ist mit dem jetzigen Aufbau nicht erreichbar.

## Grenzen

- 5 von 6 Blindtest-Clips sind eigene, saubere Synthese. Synthese, Fragen und Wahrheit stammen aus derselben Hand. Der Blindtest ist eine interne Konsistenzprüfung.
- Mehrere Einstellungen wurden auf denselben synthetischen Dateien abgestimmt, ohne zurückgehaltene Testmenge. Die synthetischen Werte sind Obergrenzen.
- Auf der einzigen echten Aufnahme im Blindtest liegt HörSchrift unter der Kontrolle (50 % gegen 60 %, 5 Fragen).
- Instrumente und Ensembles erkennt der Prototyp nicht. Ein Streichorchester erscheint als Soloinstrument.
- Die echten Aufnahmen haben wenig belegte Wahrheit: Tonart für 2 Dateien, Takt für 2.
- Langsame Stücke unter 85 BPM erscheinen in 11 von 21 synthetischen Fällen mit doppeltem Tempo (Prüfrunde 3).
- Nachhall von 1,2 Sekunden senkt die Tonartgenauigkeit auf 0,66.
- Raumklang fehlt. Die Sprachmelodie ist ein erster, ungeprüfter Entwurf.
- Kurze Clips kosten mehr pro Sekunde: 78 Tok/s für 5,3 Sekunden, 115 Tok/s für 2,7 Sekunden.
- Ein Vergleich mit Audio-Sprachmodellen auf denselben Fragen fehlt.
- Ein einziger Bewerter. Leser, Kontrolle und Bewerter gehören zur selben Modellfamilie.

## Stand und Fahrplan

| Phase | Inhalt | Stand |
|---|---|---|
| Phase 1 | Prototyp 0.3, Labormessung, Blindtest | abgeschlossen |
| Prüfrunden 1 bis 3 | Störungstests, Korrektur in Version 0.3.1, Nachmessungen | abgeschlossen |
| Phase 2 | Vergleich mit Audio-Sprachmodellen auf denselben Fragen. Bewertung ohne Kenntnis der Bedingung, zweiter Bewerter aus anderer Modellfamilie | geplant |
| Phase 3 | Stabilitätstests auf 13 echten Aufnahmen. Ziel: 90 % konsistente Angaben | geplant |
| Phase 4 | Zurückgehaltene echte Datensätze: GiantSteps (Tonart, Tempo), Isophonics und Billboard (Akkorde), GTZAN (Beats), MuChoMusic (Fragen) | geplant |
| Phase 5 | Benchmark gegen etablierte Systeme auf MMAU-Pro und MMAR. Mindestziel 51,7 % (Audio Flamingo 3), Ziel 61,9 % (AudioToolAgent) | geplant |
| Phase 6 | Instrumente, Raumklang, Sprachmelodie | geplant |

## Projektstruktur

```
hoerschrift/
  README.md
  MANIFEST.md
  requirements.txt
  testbett/      Testdaten, Generatoren, Bewertungsskripte
  ergebnisse/    Messwerte und Auswertungen
```

Das Repository enthält das Testbett und die Ergebnisse. Jede Datei steht mit Zweck und Größe in `MANIFEST.md`. Code und Methodik des Verfahrens sind nicht Teil dieses Repositorys.

## Zugehörige Arbeit

- Interner Forschungsbericht, November 2026, unveröffentlicht.
- Eigene Vorarbeit (2026): KI-Effizienz auf Consumer-Hardware. Unveröffentlicht.

## Lizenz

Alle Rechte vorbehalten. Keine Nutzung ohne Zustimmung.

Kontakt: auf Anfrage
