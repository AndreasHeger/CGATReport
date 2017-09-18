#!/bin/bash -xe

ROOT_DIR="$( dirname "${BASH_SOURCE[0]}" )"

if [[ -z "$CONDA_PY" ]]; then
    CONDA_PY=3.6
fi

if [[ -z "$CONDA_INSTALL_DIR" ]]; then
    CONDA_INSTALL_DIR=$(readlink -f env)
fi

if [[ -z "$TRAVIS_BUILD_DIR" ]]; then
    TRAVIS_BUILD_DIR="."
fi

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

CONDA="${CONDA_INSTALL_DIR}"/bin/conda

"$CONDA" update conda --yes
"$CONDA" info -a
"$CONDA" env create -f ${ROOT_DIR}/conda_env.yml

set +o nounset
source "$CONDA_INSTALL_DIR"/bin/activate cgat-report
set -o nounset

# log "installing pure R dependencies"
R -f "$ROOT_DIR"/install.R

log "setting up CGATReport"
cd "$ROOT_DIR"
python setup.py develop

# log "building report"
# cd doc && make html

# cd $TRAVIS_BUILD_DIR
# cat doc/cgatreport.log | cut -d " " -f 3 | sort | uniq -c
