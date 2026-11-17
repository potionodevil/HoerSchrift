# Blind-QA: Texttranskription (T) gegen Kontrolle ohne Eingabe (C)

Auf 44 Faktenfragen mit sicherer Referenz erreicht T 92,0 % und C 58,0 %. Die Lücke beträgt +34,1 Punkte. Das 95-%-Bootstrap-Intervall reicht von +20,5 bis +47,7 Punkten über Fragen und von +17,1 bis +46,1 Punkten über Clips.

Ein Leser pro Bedingung, ein Durchlauf, ein Bewerter für alle 100 Antworten. Alle Tabellen druckt `testbett/qa/score_blind.py` aus `testbett/qa/judgements.json`. Fragen: `testbett/qa/questions.json`, Referenz: `testbett/qa/answers.json`.

## Bedingungen und Clips

| Kürzel | Eingabe des Lesers |
|---|---|
| T | Texttranskription des Clips, kein Audio |
| C | keine Eingabe, nur die Fragen |

| Clip | Quelle | Inhalt |
|---|---|---|
| clip1 | T3 (synthetisch) | Ballade, Crescendo, neues Instrument ab Takt 9 rechts |
| clip2 | T4 (synthetisch) | Szene aus einzelnen Geräuschen mit Richtung |
| clip3 | T5 (synthetisch) | Tonartwechsel C-Dur nach D-Dur |
| clip4 | T2 (synthetisch) | Tanzstück, Intro, Lead, Breakdown |
| clip5 | Fremdaufnahme, nicht enthalten | Brahms, Ungarischer Tanz Nr. 5, Streichorchester |
| clip6 | T6 (synthetisch) | Tempowechsel 90 nach 120 BPM |

## Bewertungsregeln (vor der Bewertung festgelegt, gleich für T und C)

1. Zahlen. Toleranzen: Tempo 4 %; Zeiten 1 Takt oder 1 s, der größere Wert; Tonhöhe 50 Cent; Taktnummern 1 Takt. Innerhalb der Toleranz 1, innerhalb der doppelten Toleranz 0,5, sonst 0.
2. Kategorien (Tonart, Tongeschlecht, Richtung, lauter/leiser, ja/nein, Akkordfolge). Richtig 1. Vertretbarer Beinahe-Treffer 0,5: Paralleltonart; ein Akkord von vier falsch; richtige Funktionen in falscher Tonart; richtige Klangfamilie mit falscher Quelle. Sonst 0.
3. Harmonik. Ein Dreiklang für einen Septakkord (G für G7) zählt als richtig. Eine Folge nur als Funktionen (I-IV-V-I) wird nach Funktionen bewertet.
4. Klangfarbe. Quelle und Familie richtig, oder Familie richtig ohne falsche Quelle: 1. Nur generische Quelle oder Familie mit falscher Quelle: 0,5. Falsche Familie: 0.
5. Mehrteilige Fragen: Mittel der Teile, auf 0,5 gerundet; 0,25 und 0,75 runden ab. Ein Listenteil gibt 1 wenn alles stimmt, 0,5 wenn mindestens die Hälfte stimmt bei höchstens einem Fehler.
6. Stimmung (subjektiv): kein widersprechender Begriff 1, teils passend 0,5, Kern widersprochen 0. Getrennt berichtet.
7. Unsichere Referenz (clip5 q3, Tonart der Brahms-Aufnahme): gegen die Tonart im Dateititel bewertet, getrennt berichtet, nicht in der Kopfzahl.
8. Zusätzliche Angaben kosten nichts, solange sie die Antwort nicht ändern.
9. Zweifelsfälle gehen zugunsten von C. Die Lücke T − C ist damit eine Untergrenze.

## Kopfzahlen

| Menge | n | T | C | Lücke |
|---|---|---|---|---|
| Faktenfragen, sichere Referenz | 44 | 40,5 = 92,0 % | 25,5 = 58,0 % | +34,1 Pkt. |
| alle Fragen | 50 | 44,5 = 89,0 % | 29,0 = 58,0 % | +31,0 Pkt. |
| subjektiv (Stimmung) | 5 | 4,0 = 80,0 % | 3,5 = 70,0 % | +10,0 Pkt. |
| unsichere Referenz | 1 | 0 | 0 | 0 |

- Paarweise über die 44 Faktenfragen: T besser bei 22, C besser bei 2, 20 gleich.
- Nur volle Punkte: T 40/44 = 90,9 %, C 20/44 = 45,5 %.
- Auf den 5 synthetischen Clips erreicht T 97,4 % (38/39) und C 57,7 %. Auf der einzigen echten Aufnahme erreicht T 50,0 % und C 60,0 % (n = 5).

## Nach Kategorie (Faktenfragen)

| Kategorie | n | T | C | Lücke |
|---|---|---|---|---|
| Tonart/Tongeschlecht | 5 | 100 % | 50,0 % | +50,0 |
| Zeitpunkte | 3 | 100 % | 50,0 % | +50,0 |
| Tempo/Takt | 10 | 100 % | 65,0 % | +35,0 |
| Klangfarbe/Instrument | 9 | 72,2 % | 38,9 % | +33,3 |
| Harmonik | 5 | 100 % | 70,0 % | +30,0 |
| Ereignisse/Richtung | 9 | 88,9 % | 61,1 % | +27,8 |
| Dynamik/Struktur | 3 | 100 % | 83,3 % | +16,7 |
| Stimmung (subjektiv) | 5 | 80,0 % | 70,0 % | +10,0 |

Kategorien haben 3 bis 10 Fragen. Eine Frage verschiebt eine Kategorie um 10 bis 33 Punkte.

## Nach Clip

| Clip | Faktenfragen | T | C | Lücke | alle Fragen T / C |
|---|---|---|---|---|---|
| clip1 | 9 | 88,9 % | 33,3 % | +55,6 | 90,0 % / 35,0 % |
| clip2 | 9 | 100 % | 55,6 % | +44,4 | 100 % / 55,6 % |
| clip3 | 7 | 100 % | 64,3 % | +35,7 | 100 % / 68,8 % |
| clip4 | 8 | 100 % | 75,0 % | +25,0 | 100 % / 77,8 % |
| clip5 | 5 | 50,0 % | 60,0 % | −10,0 | 35,7 % / 42,9 % |
| clip6 | 6 | 100 % | 66,7 % | +33,3 | 100 % / 71,4 % |

## Kalibrierung

| Bedingung | Menge | n | mittlere Konfidenz | Genauigkeit | Konfidenz − Genauigkeit | Brier | AUROC |
|---|---|---|---|---|---|---|---|
| T | alle | 50 | 0,738 | 0,890 | −0,152 | 0,112 | 0,81 |
| T | Fakten | 44 | 0,761 | 0,920 | −0,159 | 0,083 | 0,90 |
| C | alle | 50 | 0,313 | 0,580 | −0,267 | 0,240 | 0,70 |
| C | Fakten | 44 | 0,314 | 0,580 | −0,266 | 0,239 | 0,69 |

Beide Leser sind unterkonfident, T um 15 Punkte, C um 27 Punkte. Die Konfidenz von T trennt Treffer von Fehlern (AUROC 0,81 über alle 50 Fragen).

## Fehler von T

T liegt bei 6 Fragen unter 1. 5 davon betreffen clip5, die einzige echte Aufnahme.

| Frage | T-Punkte | Ursache |
|---|---|---|
| clip1 q7, Seite des neuen Instruments | 0 | Die Transkription zeigt keine Richtung pro Instrument. |
| clip5 q1, Solo oder Ensemble | 0 | Die Transkription nennt keine Besetzung. |
| clip5 q2, Instrumentenfamilie | 0 | Die Klangangaben passen eher zu Klavier als zu Streichern. |
| clip5 q6, Genre | 0,5 | Die Transkription nennt 3/4-Takt für einen Tanz im geraden Takt. |
| clip5 q7, Stimmung | 0 | Transkription ohne Akzentangaben, Leser gewichtete Tempoangaben gering. |
| clip5 q3, Tonart | 0 (unsichere Referenz) | T nennt g-Moll. Die Aufnahme klingt in g-Moll; der Dateititel nennt fis-Moll. |

## Grenzen

- 5 von 6 Clips sind saubere Synthese. Die Zahlen sind für echte Aufnahmen eine Obergrenze.
- C trifft stereotype Werte (128 BPM, Am-F-C-G, Lead ab Takt 5) mit Konfidenz 0,1 bis 0,3. Teile davon verrät der Fragetext.
- Ein Bewerter, keine Zweitbewertung.
