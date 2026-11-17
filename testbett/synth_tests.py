"""Generate the synthetic audio test set (T1-T6) with exact ground truth.

Run:  python synth_tests.py            -> data/synth/T*.wav + T*.json

Every file is additive synthesis (numpy), ADSR envelopes, saw/square/sine
voices, noise drums, 22.05 kHz stereo. Ground truth JSON holds tempo, meter,
key, bar times, chords per bar, melody and bass notes (onset s, dur s, midi),
drum hits per instrument and 16-step grid strings, sections, events.
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy import signal

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "synth")
NOTE_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
ROOTS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
         "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10]}


def midi_name(m):
    return f"{NOTE_NAMES[m % 12]}{m // 12 - 1}"


def mhz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def parse_chord(ch):
    root = ch[:2] if len(ch) > 1 and ch[1] in "#b" else ch[:1]
    return ROOTS[root], QUAL[ch[len(root):]]


# ---------------------------------------------------------------- voices
def adsr(n, a=0.01, d=0.08, s=0.7, r=0.08):
    """ADSR envelope of n samples; release happens inside the note length."""
    env = np.full(n, s, dtype=np.float32)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    env[:na] = np.linspace(0, 1, na, endpoint=False)
    nd = min(nd, max(0, n - na))
    env[na:na + nd] = np.linspace(1, s, nd, endpoint=False)
    nr = min(nr, n)
    if nr > 0:
        env[n - nr:] *= np.linspace(1, 0, nr)
    return env


def osc(freq, n, kind="saw", phase=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float64)
    kmax = int((SR / 2 - 200) // freq)
    if kind == "sine":
        out = np.sin(2 * np.pi * freq * t + phase)
    elif kind == "flute":
        out = np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(4 * np.pi * freq * t)
    elif kind == "saw":
        for k in range(1, min(kmax, 40) + 1):
            out += np.sin(2 * np.pi * k * freq * t) / k
        out *= 0.6
    elif kind == "square":
        for k in range(1, min(kmax, 40) + 1, 2):
            out += np.sin(2 * np.pi * k * freq * t) / k
        out *= 0.8
    elif kind == "soft":  # triangle-like pad
        for k in range(1, min(kmax, 12) + 1, 2):
            out += ((-1) ** ((k - 1) // 2)) * np.sin(2 * np.pi * k * freq * t) / (k * k)
    elif kind == "piano":  # decaying harmonics
        for k in range(1, min(kmax, 12) + 1):
            out += np.sin(2 * np.pi * k * freq * t) * np.exp(-t * (1.5 + 1.2 * k)) / k
    elif kind == "bass":
        out = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return out.astype(np.float32)


def pan_gains(p):
    """Constant-power pan, p in [-1 (left), 1 (right)]."""
    th = (p + 1) * np.pi / 4
    return np.cos(th), np.sin(th)


def place(buf, x, t0, pan=0.0, itd=True):
    """Add mono signal x at time t0 into stereo buf with level pan and ITD."""
    gl, gr = pan_gains(pan)
    i0 = int(round(t0 * SR))
    delay = int(round(abs(pan) * 0.0006 * SR)) if itd else 0  # up to 0.6 ms
    dl = delay if pan > 0 else 0  # source on right -> left ear later
    dr = delay if pan < 0 else 0
    for ch, g, d in ((0, gl, dl), (1, gr, dr)):
        a = i0 + d
        b = min(a + len(x), buf.shape[1])
        if a < buf.shape[1] and b > a:
            buf[ch, a:b] += g * x[: b - a]


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 110 * np.exp(-t / 0.025)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-t / 0.12)).astype(np.float32)


_rng_drum = np.random.default_rng(7)
_b_sn, _a_sn = signal.butter(2, [1200 / (SR / 2), 7000 / (SR / 2)], "band")
_b_hh, _a_hh = signal.butter(4, 7000 / (SR / 2), "high")


def snare():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    nz = signal.lfilter(_b_sn, _a_sn, _rng_drum.standard_normal(n)) * np.exp(-t / 0.07)
    tone = 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    return (1.6 * nz + tone).astype(np.float32)


def hat():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    nz = signal.lfilter(_b_hh, _a_hh, _rng_drum.standard_normal(n)) * np.exp(-t / 0.025)
    return (1.4 * nz).astype(np.float32)


DRUMS = {"K": kick, "S": snare, "H": hat}
DRUM_GAIN = {"K": 0.55, "S": 0.32, "H": 0.10}
DRUM_PAN = {"K": 0.0, "S": -0.15, "H": 0.3}


# ---------------------------------------------------------------- melody writer
RHYTHMS = [[1, 1, 1, 1], [2, 1, 1], [1, 0.5, 0.5, 2], [0.5, 0.5, 1, 2], [1.5, 0.5, 1, 1],
           [1, 1, 2], [1, 0.5, 0.5, 1, 1], [0.5, 0.5, 0.5, 0.5, 2]]


def scale_pcs(tonic, mode):
    steps = [0, 2, 4, 5, 7, 9, 11] if mode == "major" else [0, 2, 3, 5, 7, 8, 10]
    return {(tonic + s) % 12 for s in steps}


def write_melody(chords, tonic, mode, rng, lo=62, hi=81, rhythm_ids=None):
    """Return list of (bar_idx, beat_pos, dur_beats, midi). Chord tones on strong beats."""
    pcs = scale_pcs(tonic, mode)
    scale = [m for m in range(lo, hi + 1) if m % 12 in pcs]
    notes = []
    prev = scale[len(scale) // 2]
    for bi, ch in enumerate(chords):
        root, iv = parse_chord(ch)
        ctones = [m for m in range(lo, hi + 1) if (m - root) % 12 in iv]
        rid = rhythm_ids[bi % len(rhythm_ids)] if rhythm_ids else rng.integers(len(RHYTHMS))
        pos = 0.0
        for d in RHYTHMS[rid]:
            strong = pos in (0.0, 2.0)
            pool = ctones if strong or d >= 1 else scale
            cand = sorted(pool, key=lambda m: abs(m - prev) + rng.random() * 2.5)
            # avoid repeating the same pitch too often, keep movement musical
            m = cand[0] if cand[0] != prev or rng.random() < 0.25 else cand[1]
            notes.append((bi, pos, d, int(m)))
            prev = m
            pos += d
    return notes


# ---------------------------------------------------------------- piece builder
def bar_starts(tempos, beats_per_bar=4):
    t, out = 0.0, []
    for bpm in tempos:
        out.append(t)
        t += beats_per_bar * 60.0 / bpm
    return np.array(out + [t])


def beat_time(starts, tempos, bar, beat):
    return starts[bar] + beat * 60.0 / tempos[bar]


def build_piece(spec):
    nb = len(spec["chords"])
    tempos = spec["tempos"]
    bpb = spec.get("beats_per_bar", 4)
    starts = bar_starts(tempos, bpb)
    total = starts[-1] + 1.5
    buf = np.zeros((2, int(total * SR) + SR), dtype=np.float32)
    gt = {"name": spec["name"], "sr": SR, "duration": float(total), "tempo_per_bar": tempos,
          "meter": f"{bpb}/4", "beats_per_bar": bpb, "key_per_bar": spec["key_per_bar"],
          "key": spec["key"], "chords": spec["chords"], "bar_times": starts.tolist(),
          "beat_times": [], "sections": spec["sections"], "melody": [], "bass": [],
          "drums": {"K": [], "S": [], "H": []}, "drum_grid": [], "notes": spec.get("notes", "")}
    for b in range(nb):
        for k in range(bpb):
            gt["beat_times"].append(beat_time(starts, tempos, b, k))
    layers = {}

    def layer(name):
        if name not in layers:
            layers[name] = np.zeros_like(buf)
        return layers[name]

    # chords (pad), voiced near C4
    for b, ch in enumerate(spec["chords"]):
        root, iv = parse_chord(ch)
        dur = starts[b + 1] - starts[b]
        voicing = []
        for i in iv:
            m = 55 + ((root + i - 55) % 12)
            voicing.append(m)
        kind = spec.get("pad_kind", "soft")
        if spec.get("arpeggio"):  # eighth-note piano arpeggio
            seq = sorted(voicing) + [sorted(voicing)[1] + 12]
            e = 60.0 / tempos[b] / 2
            for k in range(bpb * 2):
                m = seq[[0, 1, 2, 3, 2, 1, 2, 3][k % 8] % len(seq)]
                x = osc(mhz(m), int(e * 1.6 * SR), "piano") * adsr(int(e * 1.6 * SR), 0.003, 0.1, 0.6, 0.15)
                place(layer("pad"), spec.get("pad_gain", 0.10) * x, starts[b] + k * e, pan=-0.2)
        else:
            for j, m in enumerate(voicing):
                n = int(dur * SR)
                x = osc(mhz(m), n, kind) * adsr(n, 0.03, 0.2, 0.8, 0.12)
                place(layer("pad"), spec.get("pad_gain", 0.07) * x, starts[b], pan=(j - 1) * 0.5)

    # melody
    for (b, pos, d, m) in spec["melody"]:
        t0 = beat_time(starts, tempos, b, pos)
        dur = d * 60.0 / tempos[b]
        n = int(dur * 0.92 * SR)
        x = osc(mhz(m), n, spec.get("mel_kind", "saw")) * adsr(n, 0.008, 0.06, 0.75, 0.04)
        place(layer("mel"), spec.get("mel_gain", 0.22) * x, t0, pan=0.1)
        gt["melody"].append([round(t0, 4), round(dur, 4), m])

    # counter melody (new instrument)
    for (b, pos, d, m) in spec.get("counter", []):
        t0 = beat_time(starts, tempos, b, pos)
        dur = d * 60.0 / tempos[b]
        n = int(dur * 0.95 * SR)
        x = osc(mhz(m), n, spec.get("counter_kind", "saw")) * adsr(n, 0.06, 0.1, 0.8, 0.1)
        place(layer("ctr"), spec.get("counter_gain", 0.12) * x, t0, pan=0.45)

    # bass
    for b, ch in enumerate(spec["chords"]):
        root, iv = parse_chord(ch)
        for (pos, d, iv_off) in spec["bass_pattern"]:
            if pos >= bpb:
                continue
            m = 36 + ((root + iv_off - 36) % 12)
            t0 = beat_time(starts, tempos, b, pos)
            dur = d * 60.0 / tempos[b]
            n = int(dur * 0.9 * SR)
            x = osc(mhz(m), n, "bass") * adsr(n, 0.006, 0.1, 0.8, 0.05)
            place(layer("bass"), spec.get("bass_gain", 0.28) * x, t0, pan=0.0)
            gt["bass"].append([round(t0, 4), round(dur, 4), m])

    # drums
    steps = bpb * 4
    for b in range(nb):
        pat = spec["drums"][b] if b < len(spec["drums"]) else None
        grid = {}
        if pat:
            for inst, s in pat.items():
                grid[inst] = s
                for k, c in enumerate(s):
                    if c == "x":
                        t0 = beat_time(starts, tempos, b, k / 4)
                        place(layer("drums"), DRUM_GAIN[inst] * DRUMS[inst](), t0, pan=DRUM_PAN[inst], itd=False)
                        gt["drums"][inst].append(round(t0, 4))
        gt["drum_grid"].append({i: grid.get(i, "." * steps) for i in "KSH"})

    # mix with per-layer gain curves
    mix = np.zeros_like(buf)
    for name, lay in layers.items():
        mix += lay
    if "gain_db" in spec:  # crescendo etc: piecewise-linear dB over time
        tt = np.arange(mix.shape[1]) / SR
        gdb = np.interp(tt, spec["gain_db"][0], spec["gain_db"][1])
        mix *= (10 ** (gdb / 20)).astype(np.float32)
    mix += (10 ** (-75 / 20)) * np.random.default_rng(1).standard_normal(mix.shape).astype(np.float32)
    mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))
    mix = mix[:, : int(total * SR)]
    gt["melody"].sort()
    gt["bass"].sort()
    return mix, gt


def rhythm_cycle(n, seed):
    r = np.random.default_rng(seed)
    return [int(r.integers(len(RHYTHMS))) for _ in range(n)]


def make_T1():
    chords = ["C", "G", "Am", "F"] * 4
    rng = np.random.default_rng(11)
    melA = write_melody(chords[:8], 0, "major", rng, 62, 79, rhythm_cycle(4, 1))
    melB = write_melody(chords[8:], 0, "major", rng, 67, 84, rhythm_cycle(4, 2))
    mel = melA + [(b + 8, p, d, m) for (b, p, d, m) in melB]
    dA = {"K": "x.......x.......", "S": "....x.......x...", "H": "x.x.x.x.x.x.x.x."}
    dB = {"K": "x.......x.x.....", "S": "....x.......x...", "H": "xxxxxxxxxxxxxxxx"}
    spec = dict(name="T1", chords=chords, tempos=[100.0] * 16, key="C major", key_per_bar=["C major"] * 16,
                melody=mel, mel_kind="saw", bass_pattern=[(0, 2, 0), (2, 2, 0)],
                drums=[dA] * 8 + [dB] * 8,
                sections=[{"label": "A", "bar": 1}, {"label": "A'", "bar": 9}],
                notes="I-V-vi-IV in C, saw lead; bars 9-16 new melody one register higher, 16th hats, extra kick")
    return spec


def make_T2():
    chords = ["Am", "F", "C", "G"] * 4
    rng = np.random.default_rng(22)
    mel = write_melody(chords[4:12], 9, "minor", rng, 64, 81, rhythm_cycle(4, 3))
    mel = [(b + 4, p, d, m) for (b, p, d, m) in mel]
    d = {"K": "x.....x.x.......", "S": "....x.......x...", "H": "xxxxxxxxxxxxxxxx"}
    spec = dict(name="T2", chords=chords, tempos=[128.0] * 16, key="A minor", key_per_bar=["A minor"] * 16,
                melody=mel, mel_kind="square", mel_gain=0.17,
                bass_pattern=[(k * 0.5, 0.5, 0) for k in range(8)],
                drums=[d] * 12 + [None] * 4,
                sections=[{"label": "A", "bar": 1}, {"label": "B", "bar": 5}, {"label": "C", "bar": 13}],
                notes="i-VI-III-VII in A minor; bars 1-4 intro without lead, bars 5-12 square lead, bars 13-16 breakdown without drums")
    return spec


def make_T3():
    chords = ["D", "Bm", "G", "A"] * 4
    rng = np.random.default_rng(33)
    mel = write_melody(chords, 2, "major", rng, 66, 83, rhythm_cycle(4, 4))
    counter = []
    for b in range(8, 16):
        root, iv = parse_chord(chords[b])
        for pos, off in ((0, iv[1]), (2, iv[2])):
            m = 50 + ((root + off - 50) % 12)
            counter.append((b, pos, 2, m))
    starts = bar_starts([70.0] * 16)
    spec = dict(name="T3", chords=chords, tempos=[70.0] * 16, key="D major", key_per_bar=["D major"] * 16,
                melody=mel, mel_kind="flute", mel_gain=0.26, arpeggio=True, pad_gain=0.09,
                counter=counter, counter_kind="saw", counter_gain=0.10,
                bass_pattern=[(0, 4, 0)], bass_gain=0.22, drums=[None] * 16,
                gain_db=([0, starts[16]], [-24, 0]),
                sections=[{"label": "A", "bar": 1}, {"label": "B", "bar": 9}],
                notes="ballad, piano arpeggio + flute-like sine lead + bass, crescendo -24 dB to 0 dB, saw (brass/string-like) counter line enters bar 9 panned right")
    return spec


def make_T5():
    cC = ["C", "F", "G7", "C"] * 2
    cD = ["D", "G", "A7", "D"] * 2
    rng = np.random.default_rng(55)
    melC = write_melody(cC, 0, "major", rng, 62, 79, rhythm_cycle(4, 5))
    melD = [(b + 8, p, d, m + 2) for (b, p, d, m) in melC]
    d = {"K": "x...x...x...x...", "S": "....x.......x...", "H": "..x...x...x...x."}
    spec = dict(name="T5", chords=cC + cD, tempos=[110.0] * 16, key="C major -> D major",
                key_per_bar=["C major"] * 8 + ["D major"] * 8,
                melody=melC + melD, mel_kind="saw", bass_pattern=[(0, 1, 0), (1, 1, 7), (2, 1, 0), (3, 1, 7)],
                drums=[d] * 16,
                sections=[{"label": "A", "bar": 1}, {"label": "A'", "bar": 9}],
                notes="modulation up a whole step at bar 9: I-IV-V7-I in C then same in D, melody transposed")
    return spec


def make_T6():
    chords = ["Am", "Dm", "E", "Am"] * 4
    rng = np.random.default_rng(66)
    mel = write_melody(chords, 9, "minor", rng, 64, 81, rhythm_cycle(4, 6))
    mel = [(b, p, d, (m + 1 if (m % 12 == 7 and chords[b] == "E") else m)) for (b, p, d, m) in mel]  # G# over E
    d = {"K": "x.......x.......", "S": "....x.......x...", "H": "x.x.x.x.x.x.x.x."}
    spec = dict(name="T6", chords=chords, tempos=[90.0] * 8 + [120.0] * 8, key="A minor", key_per_bar=["A minor"] * 16,
                melody=mel, mel_kind="saw", bass_pattern=[(0, 2, 0), (2, 2, 0)], drums=[d] * 16,
                sections=[{"label": "A", "bar": 1}, {"label": "A'", "bar": 9}],
                notes="tempo jump 90 -> 120 BPM at bar 9, i-iv-V-i in A minor (harmonic minor V = E major)")
    return spec


# ---------------------------------------------------------------- T4 scene
def make_T4():
    dur = 18.0
    buf = np.zeros((2, int(dur * SR)), dtype=np.float32)
    rng = np.random.default_rng(44)
    ev = [  # time, dur, class, pan, params
        (1.00, 0.30, "beep", -0.8, {"hz": 880.0}),
        (2.50, 0.40, "noise", 0.8, {}),
        (4.00, 0.25, "thump", 0.0, {}),
        (7.00, 0.20, "beep", -0.8, {"hz": 1318.5}),
        (7.50, 0.20, "beep", -0.8, {"hz": 1318.5}),
        (9.00, 0.60, "noise", 0.8, {}),
        (10.50, 1.00, "sweep", 0.0, {"f0": 300.0, "f1": 3000.0}),
        (12.50, 0.25, "thump", 0.0, {}),
        (13.00, 0.25, "thump", 0.0, {}),
        (14.20, 0.01, "click", -0.6, {}),
        (15.00, 0.50, "beep", 0.7, {"hz": 440.0}),
        (16.20, 0.30, "noise", 0.0, {}),
    ]
    gt_ev = []
    for (t0, d, cls, pan, p) in ev:
        n = int(d * SR)
        tt = np.arange(n) / SR
        if cls == "beep":
            x = 0.35 * np.sin(2 * np.pi * p["hz"] * tt) * adsr(n, 0.005, 0.02, 0.9, 0.01)
        elif cls == "noise":
            x = 0.30 * rng.standard_normal(n) * adsr(n, 0.01, 0.05, 0.8, 0.05)
        elif cls == "thump":
            f = 45 + 60 * np.exp(-tt / 0.03)
            x = 0.9 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.08)
        elif cls == "sweep":
            ph = 2 * np.pi * np.cumsum(p["f0"] * (p["f1"] / p["f0"]) ** (tt / d)) / SR
            x = 0.30 * np.sin(ph) * adsr(n, 0.01, 0.02, 0.9, 0.02)
        elif cls == "click":
            n = int(0.004 * SR)
            x = 0.8 * rng.standard_normal(n) * np.exp(-np.arange(n) / (0.0008 * SR))
        place(buf, x.astype(np.float32), t0, pan=pan, itd=True)
        side = "C" if abs(pan) < 0.25 else ("L" if pan < 0 else "R")
        e = {"t": t0, "dur": d, "class": cls, "pan": pan, "dir": side}
        e.update(p)
        gt_ev.append(e)
    buf += (10 ** (-70 / 20)) * rng.standard_normal(buf.shape).astype(np.float32)
    gt = {"name": "T4", "sr": SR, "duration": dur, "events": gt_ev,
          "silences": [[4.25, 7.0]],
          "notes": "scene: beeps left (880 Hz A5, 1318.5 Hz E6 x2), one 440 Hz beep right, noise bursts right, "
                   "thumps center, a sweep 300->3000 Hz center, a click left, a centered noise burst; "
                   "level pan + ITD up to 0.6 ms; room noise -70 dBFS"}
    return buf, gt


def main():
    os.makedirs(OUT, exist_ok=True)
    for mk in (make_T1, make_T2, make_T3, make_T5, make_T6):
        spec = mk()
        y, gt = build_piece(spec)
        sf.write(os.path.join(OUT, spec["name"] + ".wav"), y.T, SR, subtype="PCM_16")
        gt["chord_per_bar"] = spec["chords"]
        with open(os.path.join(OUT, spec["name"] + ".json"), "w") as f:
            json.dump(gt, f, indent=1)
        print(spec["name"], f"{gt['duration']:.1f}s", len(gt["melody"]), "mel notes")
    y, gt = make_T4()
    sf.write(os.path.join(OUT, "T4.wav"), y.T, SR, subtype="PCM_16")
    with open(os.path.join(OUT, "T4.json"), "w") as f:
        json.dump(gt, f, indent=1)
    print("T4", gt["duration"], len(gt["events"]), "events")


if __name__ == "__main__":
    main()
