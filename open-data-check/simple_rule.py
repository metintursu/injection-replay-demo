import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
d = pd.read_parquet("features.parquet")
SIG = [c for c in d.columns if c.startswith("F_")]
E = d.groupby("_group").agg({**{c: "mean" for c in SIG + ["SET_HoldingPressure1"] if c in d.columns}, "LBL_NOK": "max"})
y = E["LBL_NOK"].to_numpy().astype(int)
n = len(E)
CUSH, CAVP = "F_QUA_CushionVolume", "F_QUA_CavityPressure1Max"


def best_threshold(x, yy, only=None):
    """Best cut for 'x high => NOK' or 'x low => NOK' by balanced accuracy. Returns (score, cut, high_is_nok)."""
    best = (-1, None, True)
    v = np.unique(x)
    cuts = (v[:-1] + v[1:]) / 2
    for cut in cuts:
        hi = x > cut
        tpr = hi[yy == 1].mean(); tnr = (~hi)[yy == 0].mean()
        for score, high in (((tpr + tnr) / 2, True), (((1 - tpr) + (1 - tnr)) / 2, False)):
            if only is not None and high != only:
                continue
            if score > best[0]:
                best = (score, cut, high)
    return best


def fire(x, cut, high):
    return (x > cut) if high else (x <= cut)


def report(name, pred):
    tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
    ok = int((y == 0).sum()); nk = int((y == 1).sum())
    bal = (tp / nk + (ok - fp) / ok) / 2
    print(f"{name:<52} NOK yakalanan {tp:>2}/{nk} | yanlis alarm {fp:>2}/{ok} | dengeli dogruluk %{100*bal:.0f}")


print(f"Deney: {n} | NOK: {int(y.sum())} | her turda 1 deney disarida, esikler sadece kalan {n-1} deneyden ogrenilir\n")
res = {k: np.zeros(n, int) for k in ("auto", "or", "and", "set")}
picked = {}
for i in range(n):
    tr = np.arange(n) != i
    ytr = y[tr]
    bs = (-1, None, None, True)
    for c in SIG:
        x = E[c].to_numpy()[tr]
        if np.isnan(x).any() or np.unique(x).size < 3:
            continue
        s, cut, high = best_threshold(x, ytr)
        if s > bs[0]:
            bs = (s, c, cut, high)
    _, c, cut, high = bs
    picked[c] = picked.get(c, 0) + 1
    res["auto"][i] = int(fire(E[c].to_numpy()[i], cut, high))
    if CUSH in E and CAVP in E:
        s1, k1, hh1 = best_threshold(E[CUSH].to_numpy()[tr], ytr, only=True)
        s2, k2, hh2 = best_threshold(E[CAVP].to_numpy()[tr], ytr, only=False)
        a = fire(E[CUSH].to_numpy()[i], k1, True); b = fire(E[CAVP].to_numpy()[i], k2, False)
        res["or"][i] = int(a or b); res["and"][i] = int(a and b)
    if "SET_HoldingPressure1" in E:
        s3, k3, hh3 = best_threshold(E["SET_HoldingPressure1"].to_numpy()[tr], ytr)
        res["set"][i] = int(fire(E["SET_HoldingPressure1"].to_numpy()[i], k3, hh3))

print("Sonuc (deney bazinda):")
report("A) Otomatik: en iyi TEK sinyal + esik", res["auto"])
if CUSH in E and CAVP in E:
    report("B) Yastik YUKSEK veya kalip basinci DUSUK", res["or"])
    report("B') Yastik YUKSEK ve kalip basinci DUSUK", res["and"])
report("C) Sadece ayar: utuleme basinci (SET) esigi", res["set"])
print("\nHep 'OK' desek: NOK yakalanan 0/%d | dengeli dogruluk %%50" % int(y.sum()))
print("\nOtomatik secimde turlarda en cok secilen sinyaller:")
for k, v in sorted(picked.items(), key=lambda kv: -kv[1])[:5]:
    print(f"  {k.replace('F_', '')}: {v}/{n} tur")
if CUSH in E and CAVP in E:
    s1, k1, _ = best_threshold(E[CUSH].to_numpy(), y, only=True); s2, k2, _ = best_threshold(E[CAVP].to_numpy(), y, only=False)
    print(f"\nTum veriden ogrenilen kural (sadece bilgi icin): yastik > {k1:.2f} VEYA kalip basinci <= {k2:.1f}")
