import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
d = pd.read_parquet("features.parquet")
y = d["LBL_NOK"].to_numpy()
g = d["_group"].to_numpy()
d["_isABS"] = (d["_material"].str.upper().str.contains("ABS|TERLURAN")).astype(int)
SET = [c for c in d.columns if c.startswith("SET_")] + ["_isABS"]
SIG = [c for c in d.columns if c.startswith("F_")]
sets = {"SET (ayarlar) tek basina": SET, "Sadece makine sinyalleri": SIG + ["_isABS"],
        "SET + sinyaller": SET + SIG}
models = {
    "Lojistik": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                      LogisticRegression(C=0.05, class_weight="balanced", max_iter=2000)),
    "Random Forest": lambda: make_pipeline(SimpleImputer(strategy="median"),
                                           RandomForestClassifier(300, min_samples_leaf=3, class_weight="balanced",
                                                                  random_state=0, n_jobs=-1)),
}
ng = len(set(g))
print(f"Parca: {len(d)} | deney: {ng} | NOK deney: {int(d.groupby('_group')['LBL_NOK'].max().sum())}")
print("NOK orani malzemeye gore:", d.groupby("_material")["LBL_NOK"].mean().round(2).to_dict())
print("Test: her seferinde 1 deney tamamen disarida birakilir (47 tur)\n")
rows = []
for sn, cols in sets.items():
    for mn, mk in models.items():
        p = cross_val_predict(mk(), d[cols], y, groups=g, cv=LeaveOneGroupOut(), method="predict_proba")[:, 1]
        pred = (p >= 0.5).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum()); fn = int(((pred == 0) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
        gp = pd.Series(p).groupby(g).mean(); gy = pd.Series(y).groupby(g).max()
        gpred = (gp >= 0.5).astype(int)
        gt = int(((gpred == 1) & (gy == 1)).sum()); gn = int(gy.sum()); gf = int(((gpred == 1) & (gy == 0)).sum())
        rows.append((sn, mn, f"{tp}/{tp+fn}", f"{100*tp/max(tp+fn,1):.0f}%", f"{100*fp/max(fp+tn,1):.0f}%",
                     f"{gt}/{gn}", f"{gf}/{ng-gn}"))
print(pd.DataFrame(rows, columns=["Girdi", "Model", "NOK yakalanan", "Yakalama", "Yanlis alarm",
                                  "NOK deney bulundu", "Yanlis alarm deney"]).to_string(index=False))
print("\nNot: hep 'OK' deseydik %.0f%% dogru olurduk ama hic NOK yakalayamazdik." % (100 * (1 - y.mean())))
