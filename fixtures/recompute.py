import json, glob, os
for f in sorted(glob.glob("fixtures/*.json")):
    d = json.load(open(f))
    agrees = [v["metadata"]["scores"] for r in d["results"]
              for v in r["verdicts"] if v["assertion"] == "agrees_with_mark"]
    cost = sum(v["metadata"]["total_cost_usd"] for r in d["results"]
               for v in r["verdicts"] if v["assertion"] == "cost_budget")
    agg = {a["assertion"]: a["score"] for a in d["aggregate"]}
    split = sum(1 for s in agrees if 0 < sum(s) < len(s))
    print(f"{os.path.basename(f)[:19]}  schema {d['schema_version']:>2}  "
          f"accuracy {agg['accuracy']:.6f} ({round(agg['accuracy'] * len(agrees))}/{len(agrees)})  "
          f"precision {agg['precision']:.6f}  split {split}/{len(agrees)}  ${cost:.4f}")
