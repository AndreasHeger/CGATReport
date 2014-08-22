#!/usr/bin/env bash

# message to display when the OS is not correct
sanity_check_os() {
   echo
   echo " Unsupported operating system "
   echo " " $OS
   echo " Installation aborted "
   echo
   exit 1;
} # sanity_check_os


# function to detect the Operating System
detect_os(){

if [ -f /etc/os-release ]; then

   OS=$(cat /etc/os-release | awk '/VERSION_ID/ {sub("="," "); print $2;}' | sed 's/\"//g' | awk '{sub("\\."," "); print $1;}')
   if [ "$OS" != "12" ] ; then

      echo       
      echo " Ubuntu version not supported "
      echo
      echo " Only Ubuntu 12.x has been tested so far "
      echo 
      exit 1;

   fi

   OS="ubuntu"

elif [ -f /etc/system-release ]; then

   OS=$(cat /etc/system-release | awk ' {print $4;}' | awk '{sub("\\."," "); print $1;}')
   if [ "$OS" != "6" ] ; then
      echo
      echo " Scientific Linux version not supported "
      echo
      echo " Only 6.x Scientific Linux has been tested so far "
      echo
      exit 1;
   fi

   OS="sl"

else

   sanity_check_os

fi
} # detect_os


# function to install operating system dependencies
install_os_packages() {

if [ "$OS" == "ubuntu" -o "$OS" == "travis" ] ; then

   echo
   echo " Installing packages for Ubuntu "
   echo

   sudo apt-get install -y gcc g++ zlib1g-dev libssl-dev libbz2-dev libfreetype6-dev libpng12-dev libblas-dev libatlas-dev liblapack-dev gfortran libpq-dev r-base-dev libreadline-dev libmysqlclient-dev libboost-dev libsqlite3-dev mercurial;

elif [ "$OS" == "sl" ] ; then

   echo 
   echo " Installing packages for Scientific Linux "
   echo

   yum -y install gcc zlib-devel openssl-devel bzip2-devel gcc-c++ freetype-devel libpng-devel blas atlas lapack gcc-gfortran postgresql-devel R-core-devel readline-devel mysql-devel boost-devel sqlite-devel mercurial

   # additional configuration for scipy
   ln -s /usr/lib64/libblas.so.3 /usr/lib64/libblas.so
   ln -s /usr/lib64/libatlas.so.3 /usr/lib64/libatlas.so
   ln -s /usr/lib64/liblapack.so.3 /usr/lib64/liblapack.so;

else

   sanity_check_os $OS

fi # if-OS
} # install_os_packages

# funcion to install Python dependencies
install_python_deps() {

if [ "$OS" == "ubuntu" -o "$OS" == "sl" ] ; then

   echo
   echo " Installing Python dependencies for $1 "
   echo

   # Go to CGAT_HOME to continue with installation
   if [ -z "$CGAT_HOME" ] ; then
      # install in default location
      CGAT_HOME=$HOME/CGATREPORT
   fi

   # Build Python 2.7.5
   mkdir -p $CGAT_HOME
   cd $CGAT_HOME
   mkdir python_build
   cd python_build
   wget http://www.python.org/ftp/python/2.7.5/Python-2.7.5.tgz
   tar xzvf Python-2.7.5.tgz
   rm Python-2.7.5.tgz
   cd Python-2.7.5
   ./configure --prefix=$CGAT_HOME/Python-2.7.5
   make
   make install
   cd $CGAT_HOME
   rm -rf python_build/

   # Create virtual environment
   wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.1.tar.gz
   tar xvfz virtualenv-1.10.1.tar.gz
   rm virtualenv-1.10.1.tar.gz
   cd virtualenv-1.10.1
   $CGAT_HOME/Python-2.7.5/bin/python virtualenv.py cgat-venv
   source cgat-venv/bin/activate

   # Install Python prerequisites
   echo "installing cython"
   pip -q install cython
   echo "installing numpy"
   pip -q install numpy
   echo "installing matplotlib"
   pip -q install matplotlib
   echo "installing scipy"
   # do not go quiet, as it takes too long and travis aborts
   pip -q install scipy
   echo "installing patsy"
   pip -q install patsy
   echo "installing pandas"
   pip -q install pandas
   echo "installing remaining dependencies"
   pip install -r https://raw.github.com/AndreasHeger/sphinx-report/master/requires.txt
   echo "upgrading setuptools"
   pip -q install --upgrade setuptools ;
   echo "installing ipython"
   pip install ipython

   sudo Rscript install.R

   # Print help message
   echo
   echo
   echo "To start using the Python virtual environment with the CGAT code collection, type:"
   echo "-> source $CGAT_HOME/virtualenv-1.10.1/cgat-venv/bin/activate"
   echo "-> cgat --help"
   echo
   echo "To finish the Python virtual environment, type:"
   echo "->deactivate"
   echo
   echo ;

elif [ "$OS" == "travis" ] ; then
   # Travis-CI provides a virtualenv with Python 2.7
   echo 
   echo " Installing Python dependencies in travis "
   echo

   # do not go quiet, as travis aborts if no output from script
   # for 10 mins.

   # Install Python prerequisites
   echo "installing cython"
   pip install cython
   echo "installing numpy"
   pip install numpy
   echo "installing matplotlib"
   pip install matplotlib
   echo "installing scipy"

   pip install scipy
   echo "installing patsy"
   pip install patsy
   echo "installing pandas"
   pip install pandas
   echo "installing remaining dependencies"
   pip install -r https://raw.github.com/AndreasHeger/sphinx-report/master/requires.txt
   echo "upgrading setuptools"
   pip install --upgrade setuptools ;
   echo "installing ipython"
   pip install ipython

   sudo Rscript install.R


else

   sanity_check_os $OS

fi # if-OS
} # install_python_deps

# function to run tests
run_tests() {

if [ "$OS" == "travis" ] ; then

   python setup.py install
   cd doc
   # make html	

elif [ "$OS" == "ubuntu" -o "$OS" == "sl" ] ; then

   # prepare external dependencies
   tests_external_deps $OS

   # Set up other environment variables
   source $CGAT_HOME/virtualenv-1.10.1/cgat-venv/bin/activate

   python setup.py install
   cd doc
   # make html

else

   sanity_check_os $OS

fi # if-OS

} # run_tests

# function to display help message
help_message() {
echo
echo " Use this script as follows: "
echo
echo " 1) Become root and install the operating system* packages: "
echo " ./install-CGAT-tools.sh --install-os-packages"
echo
echo " 2) Now, as a normal user (non root), install the Python dependencies** in the default folder ($HOME/CGAT-DEPS): "
echo " ./install-CGAT-tools.sh --install-python-deps"
echo
echo " or specify a custom folder with --cgat-deps-dir option, as follows: "
echo " ./install-CGAT-tools.sh --install-python-deps --cgat-deps-dir /path/to/folder"
echo
echo " At this stage the CGAT Code Collection is ready to go and you do not need further steps. Please type the following for more information:"
if [ -z "$CGAT_HOME" ] ; then
   echo " source $HOME/CGAT-DEPS/virtualenv-1.10.1/cgat-venv/bin/activate"
else
   echo " source $CGAT_HOME/virtualenv-1.10.1/cgat-venv/bin/activate"
fi 
echo " cgat --help "
echo
echo " The CGAT Code Collection tests the software with tests. If you are interested in running those, please continue with the following steps:"
echo
echo " 3) Become root to install external tools and set up the environment: "
echo " ./install-CGAT-tools.sh --install-tests-deps"
echo
echo " 4) Then, back again as a normal user (non root), run tests as follows:"
echo " ./install-CGAT-tools.sh --run-tests"
echo 
echo " This will clone the CGAT repository from GitHub to: $HOME/CGAT-GITHUB by default. If you want to change that use --git-hub-dir as follows:"
echo " ./install-CGAT-tools.sh --run-tests --git-hub-dir /path/to/folder"
echo
echo " NOTES: "
echo " * Supported operating systems: Ubuntu 12.x and Scientific Linux 6.x "
echo " ** An isolated virtual environment will be created to install Python dependencies "
echo
exit 1;
} # help_message

# the script starts here

if [ $# -eq 0 ] ; then

   help_message

fi

# these variables will store the information about input parameters
# travis execution
TRAVIS=
# install operating system's dependencies
OS_PKGS=
# install Python dependencies
PY_PKGS=
# install dependencies to run tests
NT_PKGS=
# run tests
NT_RUN=
# variable to actually store the input parameters
INPUT_ARGS=$(getopt -n "$0" -o ht1234g:c: --long "help,
                                                  travis,
                                                  install-os-packages,
                                                  install-python-deps,
                                                  install-tests-deps,
                                                  run-tests,
                                                  git-hub-dir:,
                                                  cgat-deps-dir:"  -- "$@")
eval set -- "$INPUT_ARGS"

# process all the input parameters first
while [ "$1" != "--" ]
do

  if [ "$1" == "-h" -o "$1" == "--help" ] ; then

    help_message

  elif [ "$1" == "-t" -o "$1" == "--travis" ] ; then
      
      TRAVIS=1
      shift ;

  elif [ "$1" == "-1" -o "$1" == "--install-os-packages" ] ; then
      
      OS_PKGS=1
      shift ;

  elif [ "$1" == "-2" -o "$1" == "--install-python-deps" ] ; then
      
      PY_PKGS=1
      shift ;

  elif [ "$1" == "-3" -o "$1" == "--install-tests-deps" ] ; then

      NT_PKGS=1
      shift ;

  elif [ "$1" == "-4" -o "$1" == "--run-tests" ] ; then

      NT_RUN=1
      shift ;

  elif [ "$1" == "-g" -o "$1" == "--git-hub-dir" ] ; then

      CGAT_GITHUB="$2"
      shift 2 ;

  elif [ "$1" == "-c" -o "$1" == "--cgat-deps-dir" ] ; then

      CGAT_HOME="$2"
      shift 2 ;

  else

    help_message

  fi # if-args
  

done # while-loop

# perform actions according to the input parameters processed
if [ "$TRAVIS" == "1" ] ; then

  OS="travis"
  install_os_packages
  install_python_deps
  run_tests

else 

  detect_os
  
  if [ "$OS_PKGS" == "1" ] ; then

    install_os_packages

  fi

  if [ "$PY_PKGS" == "1" ] ; then

    install_python_deps

  fi

  if [ "$NT_PKGS" == "1" ] ; then

    install_tests_deps

  fi

  if [ "$NT_RUN" == "1" ] ; then

    run_tests

  fi


fi # if-variables

