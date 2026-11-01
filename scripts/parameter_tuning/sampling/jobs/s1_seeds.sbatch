#!/bin/bash
# S1 seed spread: one ACHR chain per seed 1..3 and thinning 20/100/500 on the 4102-reaction yeast-GEM,
# run sequentially; rho only (wall times are not comparable with the timed seed-0 jobs).
#SBATCH -N 1
#SBATCH -c 12
#SBATCH --mem=16G
set -euo pipefail
source "${STUDY:?set STUDY}/jobs/env.sh"
cd $STUDY
echo "cpus $SLURM_CPUS_PER_TASK, start $(date -Is)"
for seed in 1 2 3; do for t in 20 100 500; do
  $PY $STUDY/single_chain_autocorr.py --model $Y4102 --thinning $t --n-samples 300 --warmup 1000 --seed $seed \
      --out $DATA/s1_seeds > /dev/null
done; done
$PY - <<'PY'
import json, glob, os
rows = []
for f in sorted(glob.glob(os.environ["DATA"] + "/s1_seeds/*.json")) + sorted(glob.glob("results/s1_achr_t*_seed0.json")):
    d = json.load(open(f))
    rows.append([d["thinning"], d["seed"], d["n_nonconstant"], d["rho_mean_pearson"], d["rho_median_pearson"],
                 d["rho_mean_acf"], d["rho_median_acf"], d["ess_from_mean_rho"], d["ess_from_median_rho"], d["t_total_s"]])
rows.sort()
with open("results/s1_seed_spread.tsv", "w") as fh:
    fh.write("thinning\tseed\tn_nonconstant\trho_mean_pearson\trho_median_pearson\trho_mean_acf\trho_median_acf\tess_from_mean_rho\tess_from_median_rho\tt_total_s\n")
    for r in rows:
        fh.write("\t".join(str(round(x, 4)) if isinstance(x, float) else str(x) for x in r) + "\n")
print(open("results/s1_seed_spread.tsv").read())
PY
echo "end $(date -Is)"
