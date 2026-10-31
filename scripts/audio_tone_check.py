"""
Pitch-contour tone checker for single-syllable recordings (dev tool, not used at runtime).

Why: a wrong-tone recording teaches wrong pronunciation. For monosyllables we can compare the
tone in the recording against the expected tone from the word list.

Method: extract F0 with Praat (parselmouth), turn the voiced contour into speaker-normalised
semitones resampled to 10 points, and classify tones 1-4 with a random forest trained on the
1,707 labelled syllable recordings (tone known from the file name). Accuracy is measured by
5-fold cross-validation and printed; it is a *flagging* aid, not ground truth. Neutral tone (5)
is not checked.

    pip install praat-parselmouth numpy scikit-learn
    python scripts/audio_tone_check.py <audio-cmn checkout>
"""
import glob
import os
import re
import subprocess
import sys
import tempfile
from multiprocessing import Pool

import numpy as np
import parselmouth

N_POINTS = 10


def contour(path: str):
    """Speaker-normalised F0 contour (semitones, N_POINTS values) or None if too little voicing."""
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-ar", "16000", wav], check=True)
        pitch = parselmouth.Sound(wav).to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=500)
    f0 = pitch.selected_array["frequency"]
    voiced = np.where(f0 > 0)[0]
    if len(voiced) < 8:
        return None
    seg = f0[voiced[0]:voiced[-1] + 1].astype(float)
    idx = np.arange(len(seg))
    ok = seg > 0
    seg = np.interp(idx, idx[ok], seg[ok])  # bridge short unvoiced gaps (creaky 3rd tone)
    st = 12 * np.log2(seg / np.exp(np.mean(np.log(seg))))
    return np.interp(np.linspace(0, len(st) - 1, N_POINTS), np.arange(len(st)), st)


def features(c):
    return np.concatenate([c, [c[-1] - c[0], c.max() - c.min(), np.argmin(c) / (N_POINTS - 1), np.argmax(c) / (N_POINTS - 1)]])


def _feat(path):
    try:
        c = contour(path)
        return None if c is None else features(c)
    except Exception:
        return None


def extract(paths, workers=2):
    with Pool(workers) as p:
        return p.map(_feat, paths, chunksize=16)


def train_and_report(root: str):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_predict
    files = sorted(glob.glob(os.path.join(root, "24k-abr", "syllabs", "cmn-*.mp3")))
    labelled = [(f, int(m.group(1))) for f in files if (m := re.search(r"([1-4])\.mp3$", f))]
    feats = extract([f for f, _ in labelled])
    X = np.array([x for x, (f, t) in zip(feats, labelled) if x is not None])
    y = np.array([t for x, (f, t) in zip(feats, labelled) if x is not None])
    clf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=2)
    pred = cross_val_predict(clf, X, y, cv=5)
    print(f"syllables used {len(y)}/{len(labelled)}; 5-fold CV accuracy {np.mean(pred == y):.1%}")
    for t in (1, 2, 3, 4):
        m = y == t
        print(f"  tone {t}: recall {np.mean(pred[m] == t):.1%} (n={m.sum()})")
    return clf.fit(X, y)


if __name__ == "__main__":
    train_and_report(sys.argv[1])
