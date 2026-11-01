% Common MATLAB set-up of ml_prep.m and ml_cell.m: RAVEN checkout, Gurobi MATLAB
% interface, Human-GEM code. Environment: RAVEN_ROOT (RAVEN checkout, commit
% 2d0630e3), GUROBI_HOME (Gurobi installation), HUMANGEM_ROOT (extracted Human-GEM
% tree). The RAVEN/ravenPath preference is set to RAVEN_ROOT so that findRAVENroot
% returns this checkout and restored by ml_restore_pref.m at the end;
% mljob.sh also keeps the preferences in $TMPDIR.
RV = getenv('RAVEN_ROOT');
GM = fullfile(getenv('GUROBI_HOME'), 'matlab');
HGD = getenv('HUMANGEM_ROOT');
restoredefaultpath; addpath(genpath(RV)); addpath(GM);
addpath(genpath(fullfile(HGD,'code')));
if ispref('RAVEN','ravenPath'), oldRavenPath = getpref('RAVEN','ravenPath'); else, oldRavenPath = []; end
setpref('RAVEN','ravenPath',RV);
assert(strcmp(findRAVENroot(), RV) || strcmp([findRAVENroot() filesep], [RV filesep]), 'RAVEN root %s', findRAVENroot());
setRavenSolver('gurobi');
