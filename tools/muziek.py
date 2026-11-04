#!/usr/bin/env python3
"""Maakt vrolijke, eigen muziek voor een video, zonder rechten van anderen.
Ukelele, marimba, bas, drums en handgeklap, elke post een andere variatie.
Gebruik: python3 tools/muziek.py posts/<map>/reel.mp4 [zaadje]
Vervangt het geluid van de video en laat het beeld ongemoeid."""
import json, pathlib, re, subprocess, sys, tempfile, wave, zlib
import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 44100
MAJEUR = [0, 2, 4, 5, 7, 9, 11]
PENTA = [0, 2, 4, 7, 9]
SCHEMAS = [[0, 4, 5, 3], [5, 3, 0, 4], [0, 3, 5, 4], [0, 5, 3, 4]]  # I-V-vi-IV en varianten (trappen)
RITMES = [[0, 1, 1.5, 2.5, 3.5], [0, .5, 1.5, 2, 3], [0, 1, 2, 2.5, 3.5], [.5, 1, 2, 3, 3.5]]
STRUM = [(0, 1, 1.0), (1, 1, .7), (1.5, -1, .55), (2.5, -1, .6), (3, 1, .75), (3.5, -1, .55)]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def zet(spoor, signaal, start):
    i = int(max(start, 0) * SR)
    if i >= len(spoor):
        return
    j = min(len(spoor), i + len(signaal))
    spoor[i:j] += signaal[: j - i]


def laag(x, f):
    return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)


def hoog(x, f):
    return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)


_snaar = {}
def snaar(midi, rng):
    """Getokkelde snaar (Karplus-Strong), klinkt als een ukelele."""
    if midi not in _snaar:
        n = int(SR * 1.1)
        p = max(2, int(round(SR / hz(midi))))
        x = np.zeros(n)
        x[:p] = laag(rng.uniform(-1, 1, p), 5000)
        a = np.zeros(p + 2)
        a[0], a[p], a[p + 1] = 1, -.4975, -.4975
        y = lfilter([1], a, x)
        _snaar[midi] = y * np.exp(-3.2 * np.arange(n) / SR) * np.minimum((n - np.arange(n)) / 400, 1)
    return _snaar[midi]


def marimba(midi, sterkte):
    n = int(SR * .7)
    t = np.arange(n) / SR
    f = hz(midi)
    x = np.sin(2 * np.pi * f * t) * np.exp(-7 * t) + .32 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-24 * t) + .1 * np.sin(2 * np.pi * 9.2 * f * t) * np.exp(-60 * t)
    return x * np.minimum(t / .002, 1) * sterkte


def bas(midi, lengte, sterkte):
    n = int(SR * lengte)
    t = np.arange(n) / SR
    f = hz(midi)
    x = (np.sin(2 * np.pi * f * t) + .55 * np.sin(4 * np.pi * f * t) * np.exp(-4 * t) + .3 * np.sin(6 * np.pi * f * t) * np.exp(-7 * t)) * np.exp(-2.6 * t)
    return x * np.minimum(t / .004, 1) * np.minimum((lengte - t) / .03, 1) * sterkte


def kick(rng):
    n = int(SR * .26)
    t = np.arange(n) / SR
    fase = 2 * np.pi * np.cumsum(48 + 95 * np.exp(-t * 34)) / SR
    return np.sin(fase) * np.exp(-t * 14) + .25 * rng.normal(0, 1, n) * np.exp(-t * 400)


def klap(rng):
    n = int(SR * .2)
    t = np.arange(n) / SR
    ruis = hoog(laag(rng.normal(0, 1, n), 6500), 1100)
    uit = ruis * np.exp(-t * 26)
    for d in (.011, .022):  # meerdere handen net na elkaar
        i = int(d * SR)
        uit[i:] += ruis[:-i] * np.exp(-t[:-i] * 55) * .7
    return uit


def hihat(rng, lengte=.05):
    n = int(SR * lengte)
    t = np.arange(n) / SR
    return hoog(rng.normal(0, 1, n), 7500) * np.exp(-t * (6 / lengte))


def galm(droog, lengte, zaad):
    n = int(SR * lengte)
    rng = np.random.default_rng(zaad)
    ruis = rng.standard_normal(n) * np.exp(-6 * np.arange(n) / n)
    ruis = laag(ruis, 4500)
    ruis /= np.sqrt((ruis ** 2).sum())
    return fftconvolve(droog, ruis)[: len(droog)]


def componeer(duur, zaad):
    rng = np.random.default_rng(zaad)
    bpm = [120, 116, 124, 118][zaad % 4]
    grond = [60, 62, 57, 65, 59][zaad % 5]  # C, D, A, F, B
    schema = SCHEMAS[zaad % len(SCHEMAS)]
    tel = 60 / bpm
    maat = 4 * tel
    n = int(SR * (duur + 2))
    uke_l, uke_r, mar, bs, dr, kl = (np.zeros(n) for _ in range(6))
    kk, sn, hh = kick(rng), klap(rng), hihat(rng)
    open_hat = hihat(rng, .12)
    # laatste volle maat eindigt op een hele maat, daarna nog één slotakkoord
    eind = np.floor((duur - .85) / tel) * tel
    maten = int(np.ceil(eind / maat))
    oud_zet = zet
    def zet_tot(spoor, signaal, start):
        if start < eind - .01:
            oud_zet(spoor, signaal, start)

    def toon(trap, octaaf=0):
        return grond + MAJEUR[trap % 7] + 12 * (trap // 7) + 12 * octaaf

    def akkoord(trap):
        return [toon(trap), toon(trap + 2), toon(trap + 4)]

    def strum(trap, start, richting, sterkte):
        noten = [akkoord(trap)[2] - 12, akkoord(trap)[0], akkoord(trap)[1], akkoord(trap)[2]]
        for i, m in enumerate(noten[::richting]):
            x = snaar(m + 12, rng)[: int(SR * .7)] * sterkte * (1 - .08 * i)
            s = start + i * .009
            zet(uke_l, x * .62, s)
            zet(uke_r, x * .38, s)

    # hoe de melodie gaat: per maat een ritme, sterke tellen op akkoordtonen, daarna herhaling
    motief = []
    vorige = grond + 16
    for b, trap in enumerate(schema):
        ritme = RITMES[(zaad + b) % len(RITMES)]
        regel = []
        for tijd in ritme:
            if tijd in (0, 2):
                opties = [m + 12 * o for m in akkoord(trap) for o in (0, 1)]
            else:
                opties = [grond + p + 12 * o for p in PENTA for o in (0, 1)]
            opties = [m for m in opties if grond + 7 <= m <= grond + 24 and abs(m - vorige) <= 7] or [vorige]
            vorige = int(rng.choice(opties))
            regel.append((tijd, vorige))
        motief.append(regel)

    for m in range(maten):
        b = m * maat
        trap = schema[m % len(schema)]
        for tijd, richting, st in STRUM:
            (strum(trap, b + tijd * tel + rng.normal(0, .003), richting, .62 * st) if b + tijd * tel < eind - .01 else None)
        wortel = toon(trap, -2)
        for tijd, lengte, st in [(0, .45, 1), (1.5, .3, .8), (2, .4, .95), (3.5, .25, .75)]:
            zet_tot(bs, bas(wortel, lengte, .36 * st), b + tijd * tel)
        for tijd in (0, 1.5, 2):  # dansbare kick
            zet_tot(dr, kk * .46, b + tijd * tel)
        for tijd in (1, 3):
            zet_tot(kl, sn * .55, b + tijd * tel)
        for i in range(8):
            st = .24 if i % 2 else .13
            zet_tot(dr, (open_hat if i == 7 else hh) * st, b + i * .5 * tel)
        if m >= 1:  # melodie komt er na één maat bij
            for tijd, noot in motief[m % len(motief)]:
                zet_tot(mar, marimba(noot, .85 * rng.uniform(.88, 1.05)), b + tijd * tel + rng.normal(0, .004))
                if m >= len(schema):  # tweede keer een octaaf erboven, voor meer energie
                    zet_tot(mar, marimba(noot + 12, .3), b + tijd * tel)

    # slotakkoord
    strum(0, eind, 1, .8)
    zet(bs, bas(toon(0, -2), .9, .42), eind)
    zet(dr, kk * .46, eind)
    zet(kl, sn * .6, eind)
    zet(mar, marimba(grond + 24, .85), eind)

    midden = bs + dr + kl * .9
    links = midden + uke_l + mar * .42
    rechts = midden + uke_r + mar * .58
    nat = galm(uke_l + uke_r + mar + kl, .9, zaad + 3)
    stereo = np.stack([links + .16 * nat, rechts + .16 * nat], axis=1)
    stereo = sosfilt(butter(2, 35, "high", fs=SR, output="sos"), stereo, axis=0)[: int(SR * duur)]
    tt = np.arange(len(stereo)) / SR
    stereo *= (np.minimum(tt / .02, 1) * np.minimum((duur - tt) / .25, 1))[:, None]
    return stereo


def schrijf(pad, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(pad), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())


def luidheid(pad):
    uit = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pad), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    samen = uit[uit.rfind("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", samen).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", samen).group(1))


def maak(duur, uit, zaad, doel=-15.0):
    stereo = componeer(duur, zaad)
    stereo /= np.abs(stereo).max()
    schrijf(uit, stereo * .5)
    lufs, _ = luidheid(uit)
    stereo = stereo * .5 * 10 ** ((doel - lufs) / 20)
    # pieken zacht afronden, nooit harder dan -1 dB
    stereo = .89 * np.tanh(stereo / .89)
    schrijf(uit, stereo)
    return luidheid(uit)


def zet_onder(video, zaad=None):
    video = pathlib.Path(video).resolve()
    zaad = zlib.crc32(video.parent.name.encode()) % 1000 if zaad is None else zaad
    duur = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout)
    with tempfile.TemporaryDirectory() as td:
        wav = pathlib.Path(td) / "muziek.wav"
        lufs, piek = maak(duur, wav, zaad)
        tmp = video.with_suffix(".tmp.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(tmp)], check=True)
        tmp.rename(video)
    print(json.dumps({"zaad": zaad, "duur": round(duur, 2), "lufs": lufs, "piek_dbfs": piek}))


if __name__ == "__main__":
    zet_onder(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
