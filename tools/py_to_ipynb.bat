@echo off
%PY_ENVS%\fluxfilter\Scripts\python.exe -m jupytext --update --to notebook ..\FluxFilter.py

@echo Reminder: change branch pointer for release from main to v1.*.*
@echo FluxFilter.py will be deleted on exit
pause

del ..\FluxFilter.py