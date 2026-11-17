# Messwerte auf dem synthetischen Testset

Die Transkription trifft auf 5 Musiktests im Mittel das Tempo auf 0,90 BPM, die Tonart zu 100 % und die Dur/Moll-Akkorde zu 100 %. Melodie-F liegt bei 0,885, Bass-F bei 0,936, Schlagzeug-F bei 0,976. Auf der Geräuschszene T4 findet sie 12 von 12 Ereignissen mit richtiger Klasse und Richtung.

Testdaten: `testbett/synth_tests.py`, Referenz: `testbett/data/synth/T*.json`. Die Metriken rechnet `testbett/score_transcription.py`. Gemessen am 17.11.2026 auf einer CPU.

## Musik (T1, T2, T3, T5, T6)

| Test | Tempo Ref. | Tempo gemessen | Fehler BPM | Tonart Ref. | Tonart gemessen | Takt richtig | Akkorde Dur/Moll | Akkorde exakt | Melodie F | Bass F | Schlagzeug F | Abschnitte F |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 100 | 99,4 | 0,62 | C-Dur | C-Dur | ja | 100 % | 100 % | 0,98 | 1,00 | 1,00 | 1,00 |
| T2 | 128 | 129,2 | 1,20 | a-Moll | a-Moll | ja | 100 % | 100 % | 0,61 | 0,98 | 1,00 | 0,67 |
| T3 | 70 | 69,8 | 0,16 | D-Dur | D-Dur | ja | 100 % | 97 % | 0,92 | 0,70 | - (0 Fehltreffer) | 1,00 |
| T5 | 110 | 112,3 | 2,35 | C-Dur → D-Dur | C-Dur → D-Dur | ja | 100 % | 81 % | 0,95 | 1,00 | 0,91 | 0,67 |
| T6 | 90 → 120 | 90 → 118 | 0,15 | a-Moll | a-Moll | ja | 100 % | 100 % | 0,96 | 1,00 | 0,99 | 1,00 |

- Mittel über 5 Tests: Tempofehler 0,90 BPM (max. 2,35), Tonart 100 % exakt, Akkorde Dur/Moll 100 %, exakt mit Septimen 95,6 %, Melodie-F 0,885, Bass-F 0,936, Schlagzeug-F 0,976, Abschnittsgrenzen-F 0,87.
- Noten zählen als Treffer bei Einsatz innerhalb 50 ms und gleicher Tonklasse.
- T2: Die Melodie-Präzision liegt bei 0,47, der Recall bei 0,90. Die Transkription meldet zusätzliche Melodienoten.
- T3: Die Lautstärke pro Takt korreliert mit der Taktnummer zu r = 1,00 (erster/letzter Takt −33,8 / −11,2 dBFS).

## Geräuschszene (T4)

| Ereignisse P | Ereignisse R | F | Klasse | Richtung (L/C/R) | Tonhöhenfehler Pieptöne | Einsatzfehler |
|---|---|---|---|---|---|---|
| 1,00 | 1,00 | 1,00 | 100 % | 100 % | 6,08 Cent | 0,71 ms |

## Tokens pro Sekunde Audio (o200k_base)

| Darstellung | Tokens pro Sekunde |
|---|---|
| rohes PCM 16 kHz int16 als Dezimaltext (gemessen) | 44.594 |
| EnCodec 24 kHz, 75 Frames/s x 32 Codebooks (24 kbit/s) | 2.400 |
| EnCodec 24 kHz, 75 x 8 Codebooks (6 kbit/s) | 600 |
| EnCodec 24 kHz, 75 x 2 Codebooks (1,5 kbit/s) | 150 |
| Whisper-Encoder (Audio-Embeddings) | 50 |
| Qwen2-Audio-Encoder (nach Pooling) | 25 |
| Texttranskription, Standardumfang, Median über Dateien > 10 s (Spanne) | 31 (19 bis 49) |
| Texttranskription, Kurzfassung, Median über Dateien > 10 s (Spanne) | 20 (10 bis 33) |

## Rechenzeit

844 s Audio in 73,7 s auf der CPU, ein Prozess: 5,2 s pro Minute Audio, Echtzeitfaktor 0,087 (Median pro Datei 0,076).
