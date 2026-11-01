# ftINIT parameter studies

Scripts for the ftINIT pages of the parameter-tuning documentation on Human-GEM: solver benchmark, parameter calibration (`mip_gap`, `big_m`, `force_on`, scaling), validation against RAVEN `ftINIT` on five cell lines, and determinism of the solution. `bigm/` holds the first three, `det/` the determinism study.

## Inputs and environment

All inputs except the prepared models come from a Human-GEM commit (`model/`, `data/datasets/`, `data/metabolicTasks/`, `code/test/`): `38567ab8` for `bigm/` and `1ea27d8b` (v2.0.0-38) for `det/`. The wrappers export the commit with `git archive` into `$TMPDIR/hg`. The preparations (`prep`, `preptask`, `ml_prep`, `det/prep.py`) take 26 to 72 min each and write the prepared models.

| Variable | Meaning |
| --- | --- |
| `WORK` | work folder with `out/` (results), `shared/` (prepared models) and `logs/` |
| `TOOLBOX_ROOT` | raven-toolbox checkout (`94f3940`); its `src` goes on `PYTHONPATH` |
| `RAVEN_ROOT` | RAVEN checkout (`2d0630e`, MATLAB side) |
| `HUMANGEM_ROOT`, `HUMANGEM_COMMIT` | Human-GEM clone and commit |
| `PY` | Python interpreter with cobra, optlang and gurobipy |
| `BIGM_SCRIPTS`, `DET_SCRIPTS` | the `bigm/` and `det/` folders |
| `PREP_DIR` | `det/`: folder for `prep-base.pkl` and `prep-edit.pkl` on a shared file system (default `$WORK/prep`) |
| `GUROBI_HOME` | Gurobi 13.0.1 installation; the wrappers set `GRB_LICENSE_FILE` to its `gurobi.lic` |
| `MATLAB`, `MATLAB_PREFS` | `bigm/mljob.sh`: MATLAB R2024b executable; optional preference file to copy |

The module names in the wrappers are site-specific; other systems need an equivalent environment.

## Commands

Calibration, solver benchmark and validation:

```bash
export WORK=... TOOLBOX_ROOT=... RAVEN_ROOT=... HUMANGEM_ROOT=... PY=... GUROBI_HOME=... MATLAB=... BIGM_SCRIPTS=<this folder>/bigm
J="sbatch -A <account> -o $WORK/logs/%x-%j.out"
$J -J prep     $BIGM_SCRIPTS/job.sh prep
$J -J preptask $BIGM_SCRIPTS/job.sh preptask
$J -J mlprep   $BIGM_SCRIPTS/mljob.sh ml_prep
# after the preparations:
$J -J step0 $BIGM_SCRIPTS/job.sh step0 --cell HCT116
$J -J scale $BIGM_SCRIPTS/job.sh scale --cell HCT116
$J -J solver     $BIGM_SCRIPTS/job.sh solver --solvers gurobi,hybrid
$J -J solv-glpk  $BIGM_SCRIPTS/job.sh solver --solvers glpk
$J -J solv-scipy $BIGM_SCRIPTS/job.sh solver --solvers scipy
$J -J f-g001  $BIGM_SCRIPTS/job.sh full --gap 0.001 --big-m 1000 --tag g001-bm1000
$J -J f-g003  $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m 1000 --tag g003-bm1000
$J -J f-g01   $BIGM_SCRIPTS/job.sh full --gap 0.01  --big-m 1000 --tag g01-bm1000
for b in 25 50 100 250 500; do $J -J f-bm$b $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m $b --tag g003-bm$b; done
$J -J f-g001-100 $BIGM_SCRIPTS/job.sh full --gap 0.001 --big-m 100 --tag g001-bm100
$J -J f-off1000  $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m 1000 --scale off --tag g003-bm1000-scaleoff
$J -J f-off100   $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m 100  --scale off --tag g003-bm100-scaleoff
for g in 0.001 0.003 0.01; do $J -J fa-g$g $BIGM_SCRIPTS/job.sh full --gap $g --big-m 1000 --noabs --tag noabs-g$g-bm1000; done
$J -J fa-g001-100 $BIGM_SCRIPTS/job.sh full --gap 0.001 --big-m 100 --noabs --tag noabs-g0.001-bm100
$J -J fa-g003-250 $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m 250 --noabs --tag noabs-g0.003-bm250
$J -J fa-g003-50  $BIGM_SCRIPTS/job.sh full --gap 0.003 --big-m 50  --noabs --tag noabs-g0.003-bm50
for c in DLD1 GBM HCT116 HELA RPE1; do
  $J -J val-$c $BIGM_SCRIPTS/job.sh val --cell $c
  $J -J ml-$c  $BIGM_SCRIPTS/mljob.sh ml_cell $c
done
python $BIGM_SCRIPTS/summ.py $WORK/out
python $BIGM_SCRIPTS/compare.py --out $WORK/out --shared $WORK/shared --logs $WORK/logs --json tables.json
```

Determinism (about 100 core-hours at 2 CPUs per job):

```bash
export WORK=... TOOLBOX_ROOT=... HUMANGEM_ROOT=... PY=... GUROBI_HOME=... DET_SCRIPTS=<this folder>/det PREP_DIR=<shared folder>
export SBATCH_ACCOUNT=<account>
mkdir -p $WORK/logs
jid=$(sbatch --parsable -A $SBATCH_ACCOUNT -J det-prep -o $WORK/logs/prep.log $DET_SCRIPTS/prep.sbatch)
bash $DET_SCRIPTS/submit_all.sh $jid
# after A-rtp1-1234 has finished:
sbatch -A $SBATCH_ACCOUNT -J det-edit -o $WORK/logs/edit.log $DET_SCRIPTS/edit.sbatch
sbatch -A $SBATCH_ACCOUNT -c 2 --mem=24G -o $WORK/logs/ties.log --wrap "source $DET_SCRIPTS/env.sh; \$PY $DET_SCRIPTS/ties.py \$P/prep-base.pkl"
python $DET_SCRIPTS/analyse.py $WORK/out
python $DET_SCRIPTS/det_extra.py $WORK/out $WORK/logs --json det_extra.json
```

## Outputs

| File | Content |
| --- | --- |
| `bigm/bm.py` | Subcommands `prep`, `preptask`, `step0`, `scale`, `full`, `val`, `solver`; each writes `step0.json`, `scale.json`, `full-<tag>.json`, `val-<cell>.json` or `solver-<interfaces>.json` with the kept reaction sets into `$WORK/out`. |
| `bigm/ml_prep.m`, `bigm/ml_cell.m` | RAVEN `prepHumanModelForftINIT` and `ftINIT` for the validation; `ml_cell.m` writes `matlab-<cell>.txt`. |
| `bigm/summ.py`, `bigm/compare.py` | Summaries and all tables of the solver, calibration and validation studies. |
| `det/prep.py`, `det/build.py`, `det/select_edit.py`, `det/ties.py` | Template preparation, one or several `ftinit` builds (one JSON per build), the template edit, tied-score blocks. |
| `det/analyse.py`, `det/det_extra.py` | Tables of the determinism study from the build outputs and logs. |
