% Restore the RAVEN/ravenPath preference saved by ml_common.m.
if isempty(oldRavenPath), rmpref('RAVEN','ravenPath'); else, setpref('RAVEN','ravenPath',oldRavenPath); end
