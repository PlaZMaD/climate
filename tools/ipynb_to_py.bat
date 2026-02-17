@echo off
%PY_ENVS%\fluxfilter\Scripts\python.exe -m jupytext --to py ..\FluxFilter*.ipynb

@echo FluxFilter*.ipynb will be deleted...
pause
del ..\FluxFilter*.ipynb