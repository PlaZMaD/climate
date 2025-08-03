@echo off
%CONDA_ENVS%\ipynb-3-11-13\python.exe -m jupytext --update --to notebook ..\FluxFilter.py

@echo Reminder: change branch pointer for release from main to v1.*.*
@echo FluxFilter.py will be deleted on exit
pause

del ..\FluxFilter.py