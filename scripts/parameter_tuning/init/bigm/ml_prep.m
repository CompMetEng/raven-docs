% RAVEN template preparation for the Human-GEM validation.
% Reads $HUMANGEM_ROOT/model/Human-GEM.yml, runs prepHumanModelForftINIT with the
% essential tasks and reactions.tsv, writes $SHARED/matlab_ref_reactions.txt and
% $SHARED/matlab_prepData.mat. Command line: sbatch ... mljob.sh ml_prep
run(fullfile(fileparts(mfilename('fullpath')),'ml_common.m'));
HGD = getenv('HUMANGEM_ROOT');
tic; model = readYAMLmodel(fullfile(HGD,'model','Human-GEM.yml')); fprintf('read %d rxns %.0fs\n', numel(model.rxns), toc);
tic;
prepData = prepHumanModelForftINIT(model, false, fullfile(HGD,'data','metabolicTasks','metabolicTasks_Essential.txt'), fullfile(HGD,'model','reactions.tsv'));
fprintf('prep %.0fs\n', toc);
rm = prepData.refModel; fprintf('refModel rxns %d\n', numel(rm.rxns));
fid = fopen(fullfile(getenv('SHARED'),'matlab_ref_reactions.txt'),'w'); fprintf(fid,'%s\n',rm.rxns{:}); fclose(fid);
save(fullfile(getenv('SHARED'),'matlab_prepData.mat'),'prepData','-v7.3');
run(fullfile(fileparts(mfilename('fullpath')),'ml_restore_pref.m'));
