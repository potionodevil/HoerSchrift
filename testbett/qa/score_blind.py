"""Aggregate the hand-scored blind QA: text transcription (T) vs no-input control (C).

judgements.json holds one row per question: clip, id, category, scope, score_T, score_C
(0, 0.5 or 1, rubric in ergebnisse/qa_auswertung.md) and each reader's own confidence.
Scope "headline" = factual questions with certain ground truth; "subjective" = mood;
"uncertain" = ground truth in doubt.

    python qa/score_blind.py
"""
import json
import os

import numpy as np

QA = os.path.dirname(os.path.abspath(__file__))


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def auroc(conf, hit):
    """Probability that a random full-credit answer has higher confidence than a random miss."""
    pos = [c for c, h in zip(conf, hit) if h]
    neg = [c for c, h in zip(conf, hit) if not h]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def bootstrap(rows, key=None, n=10_000, seed=0):
    """95 % CI of mean(score_T) - mean(score_C), resampling questions or clusters (key)."""
    rng = np.random.default_rng(seed)
    if key is None:
        d = np.array([r["score_T"] - r["score_C"] for r in rows])
        idx = rng.integers(0, len(d), (n, len(d)))
        stats = d[idx].mean(axis=1)
    else:
        groups = sorted({r[key] for r in rows})
        per = [np.array([r["score_T"] - r["score_C"] for r in rows if r[key] == g]) for g in groups]
        stats = np.empty(n)
        for b in range(n):
            pick = rng.integers(0, len(per), len(per))
            stats[b] = np.concatenate([per[i] for i in pick]).mean()
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return 100 * lo, 100 * hi


def main():
    rows = json.load(open(os.path.join(QA, "judgements.json")))
    head = [r for r in rows if r["scope"] == "headline"]

    print("| set | n | T | C | gap (T minus C) |\n|---|---|---|---|---|")
    for name, sel in (("headline: factual, certain ground truth", head), ("all questions", rows),
                      ("subjective (mood)", [r for r in rows if r["scope"] == "subjective"]),
                      ("uncertain ground truth", [r for r in rows if r["scope"] == "uncertain"])):
        t, c = sum(r["score_T"] for r in sel), sum(r["score_C"] for r in sel)
        print(f"| {name} | {len(sel)} | {t:g} = {100 * t / len(sel):.1f} % | {c:g} = {100 * c / len(sel):.1f} % | "
              f"{100 * (t - c) / len(sel):+.1f} pts |")
    w = sum(r["score_T"] > r["score_C"] for r in head)
    l = sum(r["score_T"] < r["score_C"] for r in head)
    print(f"\nheadline pairs: T better on {w}, C better on {l}, ties {len(head) - w - l}")
    lo, hi = bootstrap(head)
    clo, chi = bootstrap(head, key="clip")
    print(f"bootstrap 95 % CI of the gap (10,000 resamples, seed 0): questions {lo:+.1f} to {hi:+.1f} pts, "
          f"clips {clo:+.1f} to {chi:+.1f} pts")
    full_t = sum(r["score_T"] == 1 for r in head)
    full_c = sum(r["score_C"] == 1 for r in head)
    print(f"full credit only: T {full_t}/{len(head)}, C {full_c}/{len(head)}\n")

    print("| category | n | T | C | gap |\n|---|---|---|---|---|")
    cats = sorted({r["category"] for r in head})
    stats = []
    for cat in cats:
        sel = [r for r in head if r["category"] == cat]
        t, c = mean([r["score_T"] for r in sel]), mean([r["score_C"] for r in sel])
        stats.append((t - c, cat, len(sel), t, c))
    mood = [r for r in rows if r["category"] == "mood"]
    for gap, cat, n, t, c in sorted(stats, reverse=True):
        print(f"| {cat} | {n} | {100 * t:.1f} % | {100 * c:.1f} % | {100 * gap:+.1f} |")
    t, c = mean([r["score_T"] for r in mood]), mean([r["score_C"] for r in mood])
    print(f"| mood (subjective) | {len(mood)} | {100 * t:.1f} % | {100 * c:.1f} % | {100 * (t - c):+.1f} |\n")

    print("| clip | headline n | T | C | gap | all questions T / C |\n|---|---|---|---|---|---|")
    for clip in sorted({r["clip"] for r in rows}):
        sh = [r for r in head if r["clip"] == clip]
        sa = [r for r in rows if r["clip"] == clip]
        t, c = mean([r["score_T"] for r in sh]), mean([r["score_C"] for r in sh])
        ta, ca = mean([r["score_T"] for r in sa]), mean([r["score_C"] for r in sa])
        print(f"| {clip} | {len(sh)} | {100 * t:.1f} % | {100 * c:.1f} % | {100 * (t - c):+.1f} | "
              f"{100 * ta:.1f} % / {100 * ca:.1f} % |")
    print()

    print("| condition | set | n | mean confidence | accuracy | confidence minus accuracy | Brier | AUROC |\n"
          "|---|---|---|---|---|---|---|---|")
    for k in "TC":
        for name, sel in (("all", rows), ("headline", head)):
            cs = [r[f"conf_{k}"] for r in sel]
            ss = [r[f"score_{k}"] for r in sel]
            brier = mean([(c - s) ** 2 for c, s in zip(cs, ss)])
            au = auroc(cs, [s == 1 for s in ss])
            print(f"| {k} | {name} | {len(sel)} | {mean(cs):.3f} | {mean(ss):.3f} | {mean(cs) - mean(ss):+.3f} | "
                  f"{brier:.3f} | {au:.2f} |")
    print("\n| condition | confidence bin | n | mean confidence | accuracy |\n|---|---|---|---|---|")
    for k in "TC":
        for lab, lo_, hi_ in (("below 0.4", 0, 0.4), ("0.4 to 0.7", 0.4, 0.7), ("0.7 and above", 0.7, 1.01)):
            sel = [r for r in rows if lo_ <= r[f"conf_{k}"] < hi_]
            if sel:
                print(f"| {k} | {lab} | {len(sel)} | {mean([r[f'conf_{k}'] for r in sel]):.3f} | "
                      f"{mean([r[f'score_{k}'] for r in sel]):.3f} |")


if __name__ == "__main__":
    main()
