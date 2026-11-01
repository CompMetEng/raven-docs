% RAVEN ftINIT for one Hart2015 cell line ($CELL) on $SHARED/matlab_prepData.mat,
% default settings (series 1+1), transcrData threshold 1. Writes the reaction ids to
% $OUT/matlab-<CELL>.txt. Command line: sbatch ... mljob.sh ml_cell <CELL>
run(fullfile(fileparts(mfilename('fullpath')),'ml_common.m'));
HGD = getenv('HUMANGEM_ROOT'); cell_ = getenv('CELL');
s = load(fullfile(getenv('SHARED'),'matlab_prepData.mat')); prepData = s.prepData;
T = readtable(fullfile(HGD,'data','datasets','Hart2015_RNAseq.txt'),'Delimiter','\t','FileType','text');
tr.genes = T.gene; tr.tissues = {cell_}; tr.celltypes = {cell_};
tr.levels = T.(cell_); tr.threshold = 1;
tic; [model] = ftINIT(prepData, cell_, [], [], 'transcrData', tr);
fprintf('ftINIT %s %.0fs rxns %d\n', cell_, toc, numel(model.rxns));
fid = fopen(fullfile(getenv('OUT'),['matlab-' cell_ '.txt']),'w'); fprintf(fid,'%s\n',model.rxns{:}); fclose(fid);
run(fullfile(fileparts(mfilename('fullpath')),'ml_restore_pref.m'));
