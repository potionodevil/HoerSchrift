"""Score a music or sound-event transcription against the synthetic ground truth (data/synth/T*.json).

Prediction format (JSON, one file per test, every field optional):
  music (T1, T2, T3, T5, T6)
    "tempo": 100.0                     or [90.0, 120.0] for first half / second half (T6)
    "key": "C major"                   or ["C major", "D major"] for start / end key (T5)
    "beats_per_bar": 4
    "chords": [[t0, t1, "Am"], ...]    chord label per time span, "N" = no chord
    "melody": [[onset_s, midi], ...]
    "bass":   [[onset_s, midi], ...]
    "drums":  {"K": [t, ...], "S": [...], "H": [...]}
    "section_starts": [t, ...]         boundaries after the first section
  sound events (T4)
    "events": [{"t": 1.0, "class": "beep", "dir": "L", "hz": 880.0}, ...]

Metrics: tempo error (BPM); key exact and MIREX weighted score (1 exact, .5 fifth, .3 relative,
.2 parallel); chord accuracy at the 1/4 and 3/4 point of every bar (major/minor and exact label);
note P/R/F (onset within 50 ms, pitch class or exact pitch, greedy one-to-one); drum hit F within
50 ms; section boundary F within one bar; event P/R/F within 100 ms, class and direction accuracy,
beep pitch error in cents.

    python score_transcription.py data/synth/T1.json prediction_T1.json
    python score_transcription.py --selftest      # ground truth vs itself and vs a perturbed copy
"""
import argparse
import copy
import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PCS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
       "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


# ------------------------------------------------------------------ elementary metrics
def parse_chord(lab):
    if lab in ("N", None):
        return None, None
    root = lab[:2] if len(lab) > 1 and lab[1] in "#b" else lab[:1]
    return PCS[root], lab[len(root):]


def majmin(q):
    return "min" if q.startswith("m") and not q.startswith("maj") else ("dim" if q == "dim" else "maj")


def key_parts(k):
    t, m = k.split()
    return PCS[t], m


def mirex_key(est, ref):
    """MIREX key score: 1 exact, .5 fifth, .3 relative, .2 parallel, 0 else."""
    (et, em), (rt, rm) = key_parts(est), key_parts(ref)
    if et == rt and em == rm:
        return 1.0
    if em == rm and (et - rt) % 12 in (5, 7):
        return 0.5
    if em != rm:
        if rm == "major" and em == "minor" and (et - rt) % 12 == 9:
            return 0.3
        if rm == "minor" and em == "major" and (et - rt) % 12 == 3:
            return 0.3
        if et == rt:
            return 0.2
    return 0.0


def prf(hits, n_est, n_ref):
    p = hits / n_est if n_est else (1.0 if not n_ref else 0.0)
    r = hits / n_ref if n_ref else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"P": round(p, 4), "R": round(r, 4), "F": round(f, 4), "n_est": n_est, "n_ref": n_ref}


def match_notes(est, ref, tol=0.05, pc_only=True):
    """Greedy one-to-one matching: onset within tol and pitch class (or exact pitch)."""
    used, hits = set(), 0
    for r in ref:
        best, bj = None, None
        for j, e in enumerate(est):
            if j in used:
                continue
            dt = abs(e[0] - r[0])
            if dt > tol:
                continue
            ok = (round(e[1]) % 12 == round(r[1]) % 12) if pc_only else (round(e[1]) == round(r[1]))
            if ok and (best is None or dt < best):
                best, bj = dt, j
        if bj is not None:
            used.add(bj)
            hits += 1
    return prf(hits, len(est), len(ref))


def match_times(est, ref, tol):
    used, hits = set(), 0
    for r in ref:
        c = [(abs(e - r), j) for j, e in enumerate(est) if j not in used and abs(e - r) <= tol]
        if c:
            used.add(min(c)[1])
            hits += 1
    return prf(hits, len(est), len(ref))


# ------------------------------------------------------------------ test-level scoring
def score_music(gt, pred):
    R = {}
    tb, bar_t = gt["tempo_per_bar"], gt["bar_times"]
    if "tempo" in pred:
        t = pred["tempo"]
        if max(tb) - min(tb) > 1:
            half = len(tb) // 2
            est = t if isinstance(t, list) else [t, t]
            R["tempo_err_bpm"] = round((abs(est[0] - tb[0]) + abs(est[1] - tb[half])) / 2, 3)
        else:
            R["tempo_err_bpm"] = round(abs((t[0] if isinstance(t, list) else t) - tb[0]), 3)
    if "key" in pred:
        k = pred["key"]
        if "->" in gt["key"]:
            refs = [gt["key_per_bar"][0], gt["key_per_bar"][-1]]
            est = k if isinstance(k, list) else [k, k]
            sc = [mirex_key(est[0], refs[0]), mirex_key(est[1], refs[1])]
        else:
            sc = [mirex_key(k[0] if isinstance(k, list) else k, gt["key"])]
        R["key_exact"] = sum(s == 1.0 for s in sc) / len(sc)
        R["key_mirex"] = sum(sc) / len(sc)
    if "beats_per_bar" in pred:
        R["meter_ok"] = float(pred["beats_per_bar"] == gt["beats_per_bar"])
    if "chords" in pred:
        ok_mm = ok_ex = n = 0
        for bi, ch in enumerate(gt["chord_per_bar"]):
            t0, t1 = bar_t[bi], bar_t[bi + 1]
            for frac in (0.25, 0.75):
                t = t0 + frac * (t1 - t0)
                lab = next((c[2] for c in pred["chords"] if c[0] <= t < c[1]), "N")
                er, eq = parse_chord(lab)
                rr, rq = parse_chord(ch)
                n += 1
                if er is not None and er == rr and majmin(eq) == majmin(rq):
                    ok_mm += 1
                    ok_ex += eq == rq
        R["chord_majmin"] = round(ok_mm / n, 4)
        R["chord_exact"] = round(ok_ex / n, 4)
    for part in ("melody", "bass"):
        if part in pred:
            ref = [(t, m) for t, d, m in gt[part]]
            R[part] = match_notes(pred[part], ref)
            R[part + "_exact_octave"] = match_notes(pred[part], ref, pc_only=False)
    if "drums" in pred:
        per = {i: match_times(pred["drums"].get(i, []), gt["drums"][i], 0.05) for i in "KSH"}
        R["drums"] = per
        n_ref = sum(per[i]["n_ref"] for i in "KSH")
        n_est = sum(per[i]["n_est"] for i in "KSH")
        hits = sum(round(per[i]["R"] * per[i]["n_ref"]) for i in "KSH")
        R["drum_F"] = prf(hits, n_est, n_ref)["F"] if n_ref else None
        if not n_ref:
            R["drum_false_hits"] = n_est
    if "section_starts" in pred:
        ref = [bar_t[s["bar"] - 1] for s in gt["sections"][1:]]
        bar_len = gt["beats_per_bar"] * 60.0 / (sum(tb) / len(tb))
        R["sections"] = match_times(pred["section_starts"], ref, bar_len)
    return R


def side(pan):
    return "C" if abs(pan) < 0.25 else ("L" if pan < 0 else "R")


def score_events(gt, pred):
    est, ref = pred.get("events", []), gt["events"]
    used, pairs = set(), []
    for r in ref:
        c = [(abs(e["t"] - r["t"]), j) for j, e in enumerate(est) if j not in used and abs(e["t"] - r["t"]) <= 0.1]
        if c:
            j = min(c)[1]
            used.add(j)
            pairs.append((r, est[j]))
    R = {"events": prf(len(pairs), len(est), len(ref))}
    R["class_acc"] = round(sum(r["class"] == e.get("class") for r, e in pairs) / len(pairs), 4) if pairs else 0.0
    R["dir_acc"] = round(sum(r["dir"] == e.get("dir") for r, e in pairs) / len(pairs), 4) if pairs else 0.0
    errs = [abs(1200 * math.log2(e["hz"] / r["hz"])) for r, e in pairs
            if r["class"] == "beep" and e.get("class") == "beep" and e.get("hz")]
    R["beep_pitch_err_cents"] = round(sum(errs) / len(errs), 2) if errs else None
    R["onset_err_ms"] = round(sum(abs(r["t"] - e["t"]) * 1000 for r, e in pairs) / len(pairs), 2) if pairs else None
    return R


def score(gt, pred):
    return score_events(gt, pred) if "events" in gt else score_music(gt, pred)


# ------------------------------------------------------------------ self-test
def oracle(gt):
    """Prediction that copies the ground truth (every metric should be perfect)."""
    if "events" in gt:
        return {"events": [{"t": e["t"], "class": e["class"], "dir": e["dir"], "hz": e.get("hz")} for e in gt["events"]]}
    tb, bt = gt["tempo_per_bar"], gt["bar_times"]
    half = len(tb) // 2
    keys = gt["key_per_bar"]
    return {"tempo": [tb[0], tb[half]] if max(tb) - min(tb) > 1 else tb[0],
            "key": [keys[0], keys[-1]] if "->" in gt["key"] else gt["key"],
            "beats_per_bar": gt["beats_per_bar"],
            "chords": [[bt[i], bt[i + 1], c] for i, c in enumerate(gt["chord_per_bar"])],
            "melody": [[t, m] for t, d, m in gt["melody"]], "bass": [[t, m] for t, d, m in gt["bass"]],
            "drums": {i: list(gt["drums"][i]) for i in "KSH"},
            "section_starts": [bt[s["bar"] - 1] for s in gt["sections"][1:]]}


def perturb(pred):
    """Degraded copy: +3 BPM, every 4th melody note dropped, onsets +30 ms, melody one octave up."""
    p = copy.deepcopy(pred)
    if "events" in p:
        p["events"] = [dict(e, t=e["t"] + 0.03) for k, e in enumerate(p["events"]) if k % 4 != 3]
        return p
    p["tempo"] = [x + 3 for x in p["tempo"]] if isinstance(p["tempo"], list) else p["tempo"] + 3
    p["melody"] = [[t + 0.03, m + 12] for k, (t, m) in enumerate(p["melody"]) if k % 4 != 3]
    return p


def headline(R):
    if "events" in R:
        return f"events F {R['events']['F']:.2f}, class {R['class_acc']:.2f}, dir {R['dir_acc']:.2f}"
    return (f"tempo err {R['tempo_err_bpm']:.2f} BPM, key {R['key_exact']:.2f}, chords {R['chord_majmin']:.2f}, "
            f"melody F {R['melody']['F']:.2f} (octave {R['melody_exact_octave']['F']:.2f}), bass F {R['bass']['F']:.2f}, "
            f"drum F {R['drum_F'] if R['drum_F'] is not None else '-'}, sections F {R['sections']['F']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gt", nargs="?")
    ap.add_argument("pred", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        for path in sorted(glob.glob(os.path.join(HERE, "data", "synth", "T*.json"))):
            gt = json.load(open(path))
            o = oracle(gt)
            print(f"{gt['name']} oracle:    {headline(score(gt, o))}")
            print(f"{gt['name']} perturbed: {headline(score(gt, perturb(o)))}")
        return
    if not (a.gt and a.pred):
        ap.error("give GT and PRED, or --selftest")
    print(json.dumps(score(json.load(open(a.gt)), json.load(open(a.pred))), indent=1))


if __name__ == "__main__":
    main()
