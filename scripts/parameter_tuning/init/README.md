# ftINIT parameter studies

Scripts for the ftINIT pages of the parameter-tuning documentation on Human-GEM: solver benchmark, parameter calibration (`mip_gap`, `big_m`, `force_on`, scaling), validation against RAVEN `ftINIT` on five cell lines, and determinism of the solution. `bigm/` holds the first three, `det/` the determinism study.

## Inputs and environment

All inputs except the prepared models come from a Human-GEM commit (`model/`, `data/datasets/`, `data/metabolicTasks/`, `code/test/`): `38567ab8` for `bigm/` and `1ea27d8b` (v2.0.0-38) for `det/`. The commit is exported with `git archive` into a scratch folder, as in the commands below. The preparations (`prep`, `preptask`, `ml_prep`, `det/prep.py`) take 26 to 72 min each and write the prepared models.

| Variable | Meaning |
| --- | --- |
| `WORK` | work folder with `out/` (results), `shared/` (prepared models) and `logs/` |
| `OUT`, `SHARED` | `bigm/`: result and prepared-model folders; default `$WORK/out` and `$WORK/shared` |
| `TOOLBOX_ROOT` | raven-toolbox checkout (`94f3940`); its `src` goes on `PYTHONPATH` |
| `RAVEN_ROOT` | RAVEN checkout (`2d0630e`, MATLAB side) |
| `HUMANGEM_ROOT` | extracted Human-GEM tree (see the commands) |
| `CELL` | `bigm/ml_cell.m`: cell line |
| `GUROBI_HOME` | Gurobi 13.0.1 installation; `GRB_LICENSE_FILE` points to its `gurobi.lic` and `$GUROBI_HOME/lib` is on `LD_LIBRARY_PATH` |
| `MATLAB_PREFDIR` | MATLAB: scratch preference folder, so that the `RAVEN/ravenPath` preference set by `ml_common.m` leaves the user preferences unchanged |

Python needs cobra 0.32.1, optlang 1.9.1 and gurobipy. The Python and MATLAB runs of `bigm/` use 4 cores and 64 GB each. The `det/` builds use 2 cores and 24 GB each (4 cores for the `--threads 4` builds).

## Commands

Calibration, solver benchmark and validation. Every command of the block runs from the `bigm/` folder; the preparations come first, the other runs read the prepared models in `$SHARED`.

```bash
export WORK=... TOOLBOX_ROOT=... RAVEN_ROOT=... GUROBI_HOME=... MATLAB=matlab
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic LD_LIBRARY_PATH=$GUROBI_HOME/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$TOOLBOX_ROOT/src
export OUT=$WORK/out SHARED=$WORK/shared HUMANGEM_ROOT=$WORK/hg
mkdir -p $OUT $SHARED $WORK/logs $HUMANGEM_ROOT
git -C <Human-GEM clone> archive 38567ab8 model data/datasets data/metabolicTasks code | tar -x -C $HUMANGEM_ROOT
cd <this folder>/bigm
python bm.py prep > $WORK/logs/prep.out
python bm.py preptask > $WORK/logs/preptask.out
$MATLAB -batch "run('ml_prep.m')" > $WORK/logs/mlprep.out
# after the preparations:
python bm.py step0 --cell HCT116
python bm.py scale --cell HCT116
python bm.py solver --solvers gurobi,hybrid
python bm.py solver --solvers glpk
python bm.py solver --solvers scipy
python bm.py full --gap 0.001 --big-m 1000 --tag g001-bm1000
python bm.py full --gap 0.003 --big-m 1000 --tag g003-bm1000
python bm.py full --gap 0.01  --big-m 1000 --tag g01-bm1000
for b in 25 50 100 250 500; do python bm.py full --gap 0.003 --big-m $b --tag g003-bm$b; done
python bm.py full --gap 0.001 --big-m 100 --tag g001-bm100
python bm.py full --gap 0.003 --big-m 1000 --scale off --tag g003-bm1000-scaleoff
python bm.py full --gap 0.003 --big-m 100  --scale off --tag g003-bm100-scaleoff
for g in 0.001 0.003 0.01; do python bm.py full --gap $g --big-m 1000 --noabs --tag noabs-g$g-bm1000; done
python bm.py full --gap 0.001 --big-m 100 --noabs --tag noabs-g0.001-bm100
python bm.py full --gap 0.003 --big-m 250 --noabs --tag noabs-g0.003-bm250
python bm.py full --gap 0.003 --big-m 50  --noabs --tag noabs-g0.003-bm50
for c in DLD1 GBM HCT116 HELA RPE1; do
  python bm.py val --cell $c
  CELL=$c $MATLAB -batch "run('ml_cell.m')" > $WORK/logs/ml-$c.out
done
python summ.py $OUT
python compare.py --out $OUT --shared $SHARED --logs $WORK/logs --json tables.json
```

The runs are independent of each other once the preparations are done and can run in parallel. `compare.py` reads the preparation times from the `*.out` files in `$WORK/logs`, which the redirections above write.

Determinism (about 100 core-hours at 2 cores per build). The Human-GEM tree is the `1ea27d8b` (v2.0.0-38) export, and its `code/test` goes on `PYTHONPATH`. Every build is one `build.py` call per seed; the arguments after the name are the build settings.

```bash
export WORK=... TOOLBOX_ROOT=... GUROBI_HOME=... DET=<this folder>/det
export GRB_LICENSE_FILE=$GUROBI_HOME/gurobi.lic LD_LIBRARY_PATH=$GUROBI_HOME/lib:$LD_LIBRARY_PATH
export HGT=$WORK/hg P=$WORK/prep FTINIT_DEBUG=1
mkdir -p $HGT $P $WORK/out $WORK/logs
git -C <Human-GEM clone> archive 1ea27d8b model/Human-GEM.yml model/reactions.tsv data/datasets/Hart2015_RNAseq.txt data/metabolicTasks code/test | tar -x -C $HGT
export PYTHONPATH=$TOOLBOX_ROOT/src:$HGT/code/test

# base template preparation (about 2000 s)
python $DET/prep.py --model $HGT/model/Human-GEM.yml --out $P/prep-base.pkl

# one build: name, seeds, build.py arguments
S() { n=$1; seeds=$2; shift 2
  for s in $seeds; do
    python $DET/build.py --prep $P/prep-base.pkl --seed $s --out $WORK/out/$n-s$s.json "$@"
  done > $WORK/logs/$n.log 2>&1; }

# A: full pipeline, gap fill and essential genes
for sd in 1234 7; do
  S A-base-$sd   "$sd" --rt 0 --essential 1
  S A-rt-$sd     "$sd" --rt 1 --essential 1
  S A-rtp1-$sd   "$sd" --rt 1 --pag 1.0 --essential 1
  S A-rtp005-$sd "$sd" --rt 1 --pag 0.05 --essential 1
done
S A-base-rep 1234 --rt 0 --essential 1 --repeat 2
S A-rt-rep   1234 --rt 1 --essential 1 --repeat 2
# B: first-stage probe
S B-base-t1 "1234 7 1 2 3 4" --rt 0 --nsteps 1 --fill-gaps 0
S B-rt-t1   "1234 7 1 2 3 4" --rt 1 --nsteps 1 --fill-gaps 0
S B-base-t4 "1234 7 1 2 3 4" --rt 0 --nsteps 1 --fill-gaps 0 --threads 4
S B-rt-t4   "1234 7 1 2 3 4" --rt 1 --nsteps 1 --fill-gaps 0 --threads 4
# C: prove_abs_gap sweep (resolve_ties on), both stages, no gap fill
for sd in 1234 7 1 2; do
  S C-none-$sd "$sd" --rt 1 --fill-gaps 0
  for g in 5.0 2.0 1.0 0.5 0.1 0.05; do S C-$g-$sd "$sd" --rt 1 --pag $g --fill-gaps 0; done
done

# template-edit arm, after A-rtp1-1234 has finished
python $DET/select_edit.py $P/prep-base.pkl $WORK/out/A-rtp1-1234-s1234.json $WORK/out/edit-list.json
python $DET/prep.py --model $HGT/model/Human-GEM.yml --remove $WORK/out/edit-list.json --out $P/prep-edit.pkl
for cfg in "E-base --rt 0" "E-rt --rt 1" "E-rtp1 --rt 1 --pag 1.0"; do
  set -- $cfg; n=$1; shift
  python $DET/build.py --prep $P/prep-edit.pkl --seed 1234 --out $WORK/out/$n-s1234.json --essential 1 "$@" > $WORK/logs/$n.log 2>&1
done

python $DET/ties.py $P/prep-base.pkl
python $DET/analyse.py $WORK/out
python $DET/det_extra.py $WORK/out $WORK/logs --json det_extra.json
```

The builds are independent and can run in parallel; the template-edit arm needs `A-rtp1-1234-s1234.json`. The function `S` writes the build logs that `det_extra.py` reads to `$WORK/logs/<name>.log`.

## Outputs

| File | Content |
| --- | --- |
| `bigm/bm.py` | Subcommands `prep`, `preptask`, `step0`, `scale`, `full`, `val`, `solver`; each writes `step0.json`, `scale.json`, `full-<tag>.json`, `val-<cell>.json` or `solver-<interfaces>.json` with the kept reaction sets into `$WORK/out`. |
| `bigm/ml_prep.m`, `bigm/ml_cell.m` | RAVEN `prepHumanModelForftINIT` and `ftINIT` for the validation; `ml_cell.m` writes `matlab-<cell>.txt`. |
| `bigm/summ.py`, `bigm/compare.py` | Summaries and all tables of the solver, calibration and validation studies. |
| `det/prep.py`, `det/build.py`, `det/select_edit.py`, `det/ties.py` | Template preparation, one or several `ftinit` builds (one JSON per build), the template edit, tied-score blocks. |
| `det/analyse.py`, `det/det_extra.py` | Tables of the determinism study from the build outputs and logs. |
