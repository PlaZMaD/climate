@echo off
%CONDA_ENVS%\ipynb-3-11-13\python.exe -m jupytext --to py ..\FluxFilter*.ipynb

@echo FluxFilter*.ipynb will be deleted...
pause
del ..\FluxFilter*.ipynb