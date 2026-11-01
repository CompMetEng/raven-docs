% removeGenes on e_coli_core with RAVEN.
%
% Environment variables: R = RAVEN checkout (commit 2d0630e), MODEL = e_coli_core SBML
% (cobrapy textbook.xml.gz, gunzipped). Puts R on the path, sets the RAVEN/ravenPath
% preference to R and asserts findRAVENroot()==R, sets the solver to Gurobi, imports
% the model, solves it, then removeGenes(m,{'b1779'},'removeBlockedRxns',rb) for rb
% false and true, printing reactions left, growth and GAPD bounds. The previous
% ravenPath preference is restored at the end.
% Command line (see sbatch_mat_small.sh):
%   matlab -nodisplay -nosplash -batch "run('<scripts>/mat_small.m')"
R = getenv('R');
hadPref = ispref('RAVEN','ravenPath');
if hadPref, oldPref = getpref('RAVEN','ravenPath'); end
restoredefaultpath; addpath(genpath(R)); addpath(fullfile(getenv('EBROOTGUROBI'),'matlab'));
setpref('RAVEN','ravenPath',R);
root = findRAVENroot();
assert(isequal(strip(root,'right',filesep), strip(R,'right',filesep)), 'root mismatch %s', root);
setRavenSolver('gurobi');
fprintf('solver %s\n', getpref('RAVEN','solver','none'));
fprintf('MATLAB %s\n', version);
try, gv = gurobi_version(); disp(gv); catch, end
[~, c] = system(['git -C ' R ' rev-parse HEAD']); fprintf('RAVEN commit %s', c);
m = importModel(getenv('MODEL'));
fprintf('e_coli_core: %d rxns obj=%s\n', numel(m.rxns), strjoin(m.rxns(m.c~=0)));
sol = solveLP(m); fprintf('unmodified growth %.4f (printed as -sol.f)\n', -sol.f);
fprintf('unmodified growth %.4f (biomass flux)\n', sol.x(m.c~=0));
for rb = [false true]
    r = removeGenes(m, {'b1779'}, 'removeBlockedRxns', rb);
    sol = solveLP(r);
    i = find(strcmp(r.rxns,'GAPD'));
    if isempty(i), bnd='removed'; else, bnd=sprintf('[%g %g]', r.lb(i), r.ub(i)); end
    fprintf('removeGenes removeBlockedRxns=%d: %d rxns, growth %.4f, GAPD %s\n', rb, numel(r.rxns), -sol.f, bnd);
end
if hadPref, setpref('RAVEN','ravenPath',oldPref); else, rmpref('RAVEN','ravenPath'); end
