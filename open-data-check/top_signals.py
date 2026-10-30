import warnings
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
d = pd.read_parquet("features.parquet")
SIG = [c for c in d.columns if c.startswith("F_")]
SET = [c for c in d.columns if c.startswith("SET_")]
E = d.groupby("_group").agg({**{c: "mean" for c in SIG + SET}, "LBL_NOK": "max", "_material": "first"})
y = E["LBL_NOK"].to_numpy()
print(f"Deney sayisi: {len(E)} | NOK: {int(y.sum())}\n")


def auc_table(cols, frame, yy):
    rows = []
    for c in cols:
        x = frame[c]
        if x.notna().sum() < len(x) * 0.8 or x.nunique() < 3:
            continue
        a = roc_auc_score(yy, x.fillna(x.median()))
        rows.append((c.replace("F_", ""), a, abs(a - 0.5) * 2, "NOK'ta YUKSEK" if a > 0.5 else "NOK'ta DUSUK"))
    return pd.DataFrame(rows, columns=["Sinyal", "AUC", "Guc", "Yon"]).sort_values("Guc", ascending=False)


print("== En ayirici 15 makine sinyali (deney ortalamasi, 1.0 = mukemmel, 0.5 = sans) ==")
t = auc_table(SIG, E, y)
print(t.head(15).assign(AUC=lambda s: s.AUC.round(2), Guc=lambda s: s.Guc.round(2)).to_string(index=False))
print("\nKaynak bazinda en iyi sinyal gucu:")
t["Kaynak"] = t.Sinyal.str.split("_").str[0]
print(t.groupby("Kaynak")["Guc"].max().round(2).sort_values(ascending=False).to_string())
print("\n== Ayarlar (SET) tek tek ==")
print(auc_table(SET, E, y).assign(AUC=lambda s: s.AUC.round(2), Guc=lambda s: s.Guc.round(2)).to_string(index=False))
print("\n== Ayni test sadece PP deneylerinde (malzeme etkisi olmasin) ==")
m = E["_material"].astype(str).str.upper().str.contains("PP|HE125") & ~E["_material"].astype(str).str.upper().str.contains("ABS|TERLURAN")
if m.sum() > 8 and E.loc[m, "LBL_NOK"].nunique() == 2:
    print(f"PP deney: {int(m.sum())}, NOK: {int(E.loc[m, 'LBL_NOK'].sum())}")
    print(auc_table(SIG, E[m], E.loc[m, "LBL_NOK"].to_numpy()).head(8).assign(AUC=lambda s: s.AUC.round(2), Guc=lambda s: s.Guc.round(2)).to_string(index=False))
else:
    print("PP icin yeterli veri yok")
