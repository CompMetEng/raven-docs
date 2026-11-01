#!/bin/bash
#SBATCH -c 2
#SBATCH --mem=8G
#SBATCH -t 00:30:00
#SBATCH -J bench_mat
# Submit with STUDY set to this folder (sbatch --export=ALL -A <account>).
# Needs R (RAVEN checkout) and COBRA_DATA (cobra/data folder with textbook.xml.gz).
module purge
module load MATLAB/2024b Gurobi/13.0.1-GCCcore-14.3.0
echo "EBROOTGUROBI=$EBROOTGUROBI"
export MATLAB_PREFDIR=$TMPDIR/matprefs; mkdir -p $MATLAB_PREFDIR
export MODEL=$TMPDIR/e_coli_core.xml R
gunzip -c $COBRA_DATA/textbook.xml.gz > $MODEL
matlab -nodisplay -nosplash -batch "run('$STUDY/mat_small.m')"
