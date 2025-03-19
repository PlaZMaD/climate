@echo off
%CONDA_ENVS%\ipynb-3-11\python.exe -m jupytext --update --to notebook ..\FluxFilter.py
del ..\FluxFilter.py