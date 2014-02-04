#!/usr/bin/env bash

pip install virtualenv
virtualenv cgat-venv --system-site-packages
source cgat-venv/bin/activate

# Install some Python prerequisites
#pip install numpy
#pip install scipy
#pip install matplotlib
#pip install pandas
pip install patsy
pip install statsmodels
pip install seaborn
pip install -r https://raw.github.com/AndreasHeger/sphinx-report/master/requires.txt
pip install --upgrade setuptools


