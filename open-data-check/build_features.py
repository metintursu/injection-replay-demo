import numpy as np
import pandas as pd

SRC = "dataset_V2.parquet"
PROCESS = ("QUA_", "DXP_", "TCE_", "TCN_", "DOS_", "DRY_", "ENV_", "CALC_")
TARGETS = ["LBL_NOK", "LBL_Underfilled", "LBL_SinkMarks"]
DXP_DT = 0.005


def is_array(x):
    return isinstance(x, (list, tuple, np.ndarray))


def clean(x):
    if not is_array(x):
        return None
    a = np.asarray(x, dtype=float)
    return a[np.isfinite(a)]


def summarise(col, series):
    arrs = [clean(x) for x in series]
    if not any(a is not None and a.size for a in arrs):
        return {}
    pick = lambda fn: [fn(a) if a is not None and a.size else np.nan for a in arrs]
    out = {col + "__mean": pick(np.mean), col + "__std": pick(np.std),
           col + "__min": pick(np.min), col + "__max": pick(np.max)}
    if col.startswith("DXP_Trig"):
        out[col + "__seconds"] = pick(lambda a: float((a > 0).sum()) * DXP_DT)
    return out


d = pd.read_parquet(SRC)
feat = {}
for c in d.columns:
    if not c.startswith(PROCESS):
        continue
    s = d[c]
    first = next((x for x in s if is_array(x) or (x is not None and not pd.isna(x))), None)
    if is_array(first):
        feat.update(summarise(c, s))
    else:
        num = pd.to_numeric(s, errors="coerce")
        if num.notna().mean() >= 0.9:
            feat[c] = num.to_numpy()
F = pd.DataFrame(feat)
built = F.shape[1]
keep = (F.isna().mean() <= 0.2) & (F.nunique(dropna=True) > 1)
F = F.loc[:, keep]

date = pd.to_datetime(d["MET_TimeCycleStart"]).dt.strftime("%Y-%m-%d")
out = pd.DataFrame({"_group": date + "_" + d["MET_ExperimentNumber"].astype(str),
                    "_material": d["MET_MaterialName"].astype(str),
                    "_cycle": d["MET_MachineCycleID"]})
for t in TARGETS:
    out[t] = d[t].fillna(0).astype(int)
for c in d.columns:
    if c.startswith("SET_"):
        out[c] = pd.to_numeric(d[c], errors="coerce")
out = pd.concat([out, F.add_prefix("F_")], axis=1)
out.to_parquet("features.parquet")

g = out.groupby("_group")["LBL_NOK"].agg(["size", "sum"])
print("Rows:", len(out), "| groups (date + experiment):", len(g))
print("Rows per group min/median/max:", g["size"].min(), "/", g["size"].median(), "/", g["size"].max())
print("Groups only OK:", int((g["sum"] == 0).sum()), "| only NOK:", int((g["sum"] == g["size"]).sum()),
      "| mixed:", int(((g["sum"] > 0) & (g["sum"] < g["size"])).sum()))
print("NOK rate: %.1f%%" % (100 * out["LBL_NOK"].mean()))
kept = pd.Series([c[2:].split("_")[0] for c in F.columns]).value_counts().to_dict()
print("Features built:", built, "| kept:", F.shape[1], "| dropped:", built - F.shape[1])
print("Kept per source:", kept)
print("SET columns:", [c for c in out.columns if c.startswith("SET_")])
print("Saved features.parquet")
