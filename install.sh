#!/bin/bash -xe

ROOT_DIR="$( dirname "${BASH_SOURCE[0]}" )"

if [[ -z "$CONDA_PY" ]]; then
    CONDA_PY=3.6
fi

INSTALL_BRANCH=master

if [[ -z "$CONDA_INSTALL_DIR" ]]; then
    CONDA_INSTALL_DIR=$(readlink -f env)
fi

if [[ -z "$TRAVIS_BUILD_DIR" ]]; then
    TRAVIS_BUILD_DIR="."
fi

if [[ -z ${TRAVIS_BRANCH} ]]: then
   TRAVIS_BRANCH=${INSTALL_BRANCH}
fi

CONDA_CHANNELS="--channel defaults --channel conda-forge --channel bioconda --channel r"
CONDA_PACKAGES="pillow seaborn pandas seaborn scipy numpy matplotlib jpeg rpy2 r-ggplot2 r-gplots"

# log installation information
log() {
   echo "# CGATReport log | `hostname` | `date` | $1 "
}

# download and install conda
if [ ! -d "$CONDA_INSTALL_DIR" ]; then
    log "installing conda into $CONDA_INSTALL_DIR"
    rm -f Miniconda-latest-Linux-x86_64.sh
    wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
    rm -rf "$CONDA_INSTALL_DIR"
    bash Miniconda3-latest-Linux-x86_64.sh -b -p "$CONDA_INSTALL_DIR"
    hash -r
else
    log "using existing conda enviroment in $CONDA_INSTALL_DIR"
fi

# conda update conda --yes
# conda info -a

wget -O env.yml https://raw.githubusercontent.com/CGATOxford/cgat/${TRAVIS_BRANCH}/conda_env.yml
conda env create -f env.yml

# set +o nounset
source "$CONDA_INSTALL_DIR"/bin/activate cgat-report
# set -o nounset

log "installing R dependencies"
R -f "$ROOT_DIR"/install.R

log "installing conda dependencies"
which conda

# The following packages will be pulled in through pip:
# mpld3
log "installing ggplot upgrade"
pip install --upgrade --no-dependencies ggplot

echo "setting up CGATReport"
# setup CGATPipelines
cd "$TRAVIS_BUILD_DIR"
python setup.py develop

# log "building report"
# cd doc && make html

# cd $TRAVIS_BUILD_DIR
# cat doc/cgatreport.log | cut -d " " -f 3 | sort | uniq -c
