#!/usr/bin/env bash

pip install virtualenv
python virtualenv cgat-venv
source cgat-venv/bin/activate

# Install some Python prerequisites
pip install numpy
pip install scipy
pip install matplotlib
pip install pandas
pip install seaborn
pip install -r https://raw.github.com/AndreasHeger/sphinx-report/master/requires.txt
pip install --upgrade setuptools


