#!/usr/bin/env bash

# Fail on error
set -e

# Set variables
unset PYTHONPATH
TOOLNAME="cpipe"
PYTHON_VERSION='3.6.0'
PYTHON_INTERPRETER='python3.6'
ROOT=$(dirname $(readlink -f ${BASH_SOURCE}))
SCRIPTPATH=$ROOT
SCRIPT="$0"

# Printing utilities
if [[ $- == *i* ]]; then
    bold=$(tput bold)
    normal=$(tput sgr0)
else
    bold=
    normal=
fi

# Usage function
function usage {
  echo "${bold}Cpipe Installer"
  echo "  ${bold}--help, --usage"
  echo "    ${normal}Print this help page to stdout"
  echo "  ${bold}-n, --processes <process number>"
  echo "    ${normal}Set the maximum number of processes to use for the install. The higher number the faster the install, but the more memory used. Defaults to the output of 'nproc --all', the number of available processing units (currently `nproc --all` on your system)"
  echo "  ${bold}-i, --noninteractive"
  echo "    ${normal}Disables the interactive installation prompting, e.g. for automated installs"
  echo "  ${bold}-c, --credentials </path/to/swift_credentials.sh>"
  echo "    ${normal}Use the specified swift credentials file to download assets from NECTAR. Defaults to looking in the cpipe root directory"
  echo "  ${bold}-v, --verbose"
  echo "    ${normal}Print everything to stdout instead of just errors. Good for debugging an install"
  echo "  ${bold}-s, --no-swift"
  echo "    ${normal}Do a manual install instead of downloading assets from NECTAR. Strongly NOT recommended as this will potentially take days to complete"
  echo "  ${bold}-t, --task <taskname>"
  echo "    ${normal}Specify one or more tasks to run instead of a full install. Each time you use this flag it will add another task. Don't use this unless you know what you're doing"
  echo "  ${bold}-p, --no-pip"
  echo "    ${normal}Don't update pip modules. Don't use this unless you know what you're doing"
}

# Parse arguments
ARGS=$(getopt -o visc:n:t:p:d: --long "verbose,noninteractive,no-swift,help,usage,credentials:,processes:,task:,no-pip:target-dir" -n $(basename $0) -- "$@")
eval set -- "$ARGS"

PROCESSES=`nproc --all`
VERBOSITY=1
USE_PIP=1
TASKS='install'
CUSTOM_TASKS=''
CREDENTIALS="${ROOT}/swift_credentials.sh"
USE_SWIFT=1
BPIPE_CONF_ARGS='--executor torque --queue batch'
MODE='auto'
TARGET_DIR=${ROOT}/cpipex

while true ; do
    case "$1" in
        -n|--processes)
          PROCESSES=$2
          shift 2;;
        -v|--verbose)
          VERBOSITY=2
          shift 1 ;;
        -i|--noninteractive)
          export ARGPARSE_PROMPT_AUTO=True
          BPIPE_CONF_ARGS='--executor none'
          shift 1 ;;
        -p|--no-pip)
          USE_PIP=0
          shift 1 ;;
        --usage|--help)

            usage
          exit 0;;
        -t|--task)
          CUSTOM_TASKS="${CUSTOM_TASKS} $2"
          shift 2;;
        -c|--credentials)
          CREDENTIALS=$2
          shift 2;;
        -s|--no-swift)
          USE_SWIFT=0
          shift 1;;
        -d|--target-dir)
            export TARGET_DIR=$2
            export CPIPE_ROOT=$TARGET_DIR
            shift 2;;
        --)
          break ;;
        *)
          >&2 echo "Invalid argument \"$1\""
          usage
          exit 1 ;;
    esac
done

CONTAINING_DIR="$TARGET_DIR"
TOOLDIR="$TOOLNAME"
CONDA_ENV_BASENAME="conda-env"
CONDA_ENV_CACHE="conda-cache"
MINICONDA_DIR="mc3"

export CONDA_ENV_PATH="$CONTAINING_DIR/$MINICONDA_DIR/envs/$CONDA_ENV_BASENAME"
CPIPE_PATH="$CONTAINING_DIR"
MINICONDA_PATH="$CONTAINING_DIR/$MINICONDA_DIR"

mkdir -p ${TARGET_DIR}/tmpdata
export TMPDIR=${TARGET_DIR}/tmpdata # Write temporary files to tmpdata


###### FUNCTIONS ######
function prepend_miniconda(){
    if [ -d "$MINICONDA_PATH/bin" ]; then
        echo "Miniconda installed."

        echo "Prepending miniconda to PATH..."
        export PATH="$MINICONDA_PATH/bin:$TARGET_DIR/tools/bin:$PATH"
        hash -r

        # update to the latest conda this way, since the shell script
        # is often months out of date
        #if [ -z "$SKIP_CONDA_UPDATE" ]; then
        #    echo "Updating conda..."
        #    conda update -y conda
        #fi
    else
        echo "Miniconda directory not found."
        if [[ $sourced -eq 0 ]]; then
            exit 1
        else
            return 1
        fi
    fi
}

function install_miniconda(){
    if [ -d "$MINICONDA_PATH/bin" ]; then
        echo "Miniconda directory exists."
    else
        mkdir -p "$MINICONDA_PATH"
        cd "$(dirname $MINICONDA_PATH)"
        echo "Downloading and installing Miniconda..."

        if [[ "$(python -c 'import os; print(os.uname()[0])')" == "Darwin" ]]; then
            miniconda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
        else
            miniconda_url=https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
        fi

        wget -q $miniconda_url -O Miniconda3-latest-x86_64.sh -P $(dirname $MINICONDA_PATH)/

        chmod +x $(dirname $MINICONDA_PATH)/Miniconda3-latest-x86_64.sh
        $(dirname $MINICONDA_PATH)/Miniconda3-latest-x86_64.sh -b -f -p "$MINICONDA_PATH"

        $MINICONDA_PATH/bin/conda config --append channels bioconda
        $MINICONDA_PATH/bin/conda config --append channels r
        $MINICONDA_PATH/bin/conda config --append channels conda-forge
        # $MINICONDA_PATH/bin/conda install -q -y doit

        rm $(dirname $MINICONDA_PATH)/Miniconda3-latest-x86_64.sh
    fi

    if [ -d "$MINICONDA_PATH/bin" ]; then
        prepend_miniconda

    else
        echo "It looks like the Miniconda installation failed"
        if [[ $sourced -eq 0 ]]; then
            exit 1
        else
            return 1
        fi
    fi
}

function activate_env(){
    if [ -d "$SCRIPTPATH/$CONTAINING_DIR" ]; then
        echo "$TOOLNAME parent directory found"
    else
        echo "$TOOLNAME parent directory not found: $SCRIPTPATH/$CONTAINING_DIR not found."
        echo "Have you run the setup?"
        echo "Usage: $0 setup"
        return 1
    fi

    if [ -d "$CONDA_ENV_PATH" ]; then
        if [ -z "$CONDA_DEFAULT_ENV" ]; then
            echo "Activating $TOOLNAME environment..."
            prepend_miniconda
            source activate $CONDA_ENV_BASENAME
            if [[ ! -z $TARGET_DIR ]]; then
                export PATH="$TARGET_DIR/tools/bin:$PATH"
            fi
            # override $PS1 to have a shorter prompt
            export PS1="($TOOLNAME)\$ "
        else
            if [[ "$CONDA_DEFAULT_ENV" != "$CONDA_ENV_PATH" ]]; then
                echo "It looks like a conda environment is already active,"
                echo "however it is not the cpipe environment."
                echo "To use $TOOLNAME with your project, deactivate the"
                echo "current environment and then source this file."
                echo "Example: source deactivate && source $(basename $SCRIPT) load"
            else
                echo "The $TOOLNAME environment is already active."
            fi
            return 0
        fi
    else
        echo "$CONDA_ENV_PATH/ does not exist. Exiting."
        return 1
    fi
}

function setup_env(){
    mkdir -p $SCRIPTPATH/$CONTAINING_DIR
    cd $SCRIPTPATH/$CONTAINING_DIR

    install_miniconda

    if [ ! -d "${CONDA_ENV_PATH}" ]; then
        # provide an option to use Python version in the conda environment
        conda create -y -p "${CONDA_ENV_PATH}" python=${PYTHON_VERSION} || exit 1
        # Install pip dependencies
        if (( USE_PIP )); then
            pip install --upgrade setuptools pip
            pip install doit
            pip install -e ${ROOT}/lib -q
        fi ;
    else
        echo "${CONDA_ENV_PATH}/ already exists. Skipping conda env setup."
    fi
    activate_env

}
###### /FUNCTIONS ######

# If the user specified any tasks, do them instead of install
if [[ -n $CUSTOM_TASKS ]] ; then
    TASKS=$CUSTOM_TASKS
fi

# If credentials were specified, load them
if (( USE_SWIFT )); then

    # If the credentials exist, load them. Otherwise, warn the user they don't have credentials
    if [[ ! -f $CREDENTIALS ]]; then
        >&2 echo "Credentials file doesn't exist at the path specified ($CREDENTIALS). Cpipe will perform an incomplete\
 installation. If you are part of MGHA you probably want to obtain download credentials and place them in the path above."
    else
        >&2 echo "Credentials file found in path specified ($CREDENTIALS). Performing full install."
        # Load swift credentials
        source ${ROOT}/swift_credentials.sh
    fi
else
    MODE='manual'
fi

# Output stream
if [[ $VERBOSITY == 2 ]] ; then
    OUTPUT_STREAM="/dev/stdout"
else
    OUTPUT_STREAM="/dev/null"
fi

   setup_env
   if [[ "x$ROOT" != "x$TARGET_DIR" ]]; then
   cp -a $ROOT/{batches,pipeline,designs,cpipe,_env,build.gradle,version.txt} $TARGET_DIR/
   cp -a $ROOT/tools/vep_plugins/* $TARGET_DIR/tools/vep_plugins/
   fi
   if (( USE_PIP )); then
       pip install --upgrade setuptools pip
       pip install -e ${ROOT}/lib -q
   fi ;

# Run the interactive scripts first
if [[ ! -f ${TARGET_DIR}/pipeline/bpipe.config ]] ; then
    create_bpipe_config ${BPIPE_CONF_ARGS}
fi

# Now run the full install, which is all automated
doit -d $TARGET_DIR -f $ROOT/dodo.py -n $PROCESSES --verbosity $VERBOSITY $TASKS mode=${MODE}
