import os
import tarfile
import shutil
import subprocess
import tempfile
import stat
import sys
from urllib.request import urlopen, urlretrieve
from io import StringIO
from doit.action import CmdAction
from doit.tools import create_folder
from doit import get_var
from zipfile import ZipFile

# General paths
HERE = os.path.dirname(__file__)  # The cpipe root directory
ROOT = os.path.dirname(HERE)
TOOLS_ROOT = os.path.join(ROOT, 'tools')
DATA_ROOT = os.path.join(ROOT, 'data')
TMPDATA = os.path.join(ROOT, 'tmpdata')

# Versions
BWA_VERSION = "0.7.13"
BPIPE_VERSION = "0.9.9.2"
HTSLIB_VERSION = "1.3"  # Samtools and Bcftools also use this
BEDTOOLS_VERSION = "2.25.0"
GATK_VERSION = "3.6"
VEP_VERSION = "85"
PYTHON_VERSION = "2.7.12"
PERL_VERSION = "5.24.0"
R_VERSION = "3.3.1"
GROOVY_VERSION = "2.4.7"
CPSUITE_VERSION = "1.2.7"
GROOVY_NGS_COMMIT = "fa1ad5f"
JUNIT_XML_COMMIT = "9893370"
FASTQC_VERSION = "0.11.5"
PICARD_VERSION = "2.6.0"
DBNSFP_VERSION = "2.9.1"  # Use the latest v2 version. v3 of dbNSFP uses HG38
VEP_PLUGIN_COMMIT = "3be3889"
MAVEN_VERSION = '3.3.9'
BZIP_VERSION = '1.0.6'
XZ_VERSION = '5.2.2'
PCRE_VERSION = '8.39'
LIBCURL_VERSION = '7.50.3'
ZLIB_VERSION = '1.2.8'

# Tool paths
INSTALL_ROOT = TOOLS_ROOT
INSTALL_BIN = os.path.join(INSTALL_ROOT, 'bin')
INSTALL_LIB = os.path.join(INSTALL_ROOT, 'lib')
PYTHON_ROOT = os.path.join(TOOLS_ROOT, 'python')
JAVA_LIBS_ROOT = os.path.join(TOOLS_ROOT, 'java_libs')
VEP_ROOT = os.path.join(TOOLS_ROOT, 'vep')
VEP_LIBS_ROOT = os.path.join(TOOLS_ROOT, 'vep_libs')
VEP_PLUGIN_ROOT = os.path.join(TOOLS_ROOT, 'vep_plugins')
PERL_LIB_ROOT = os.path.join(TOOLS_ROOT, 'perl_lib')
CPAN_ROOT = os.path.join(TOOLS_ROOT, 'cpan')
BPIPE_ROOT = os.path.join(TOOLS_ROOT, 'bpipe')
MAVEN_ROOT = os.path.join(TOOLS_ROOT, 'maven')
FASTQC_ROOT = os.path.join(TOOLS_ROOT, 'fastqc')
GROOVY_ROOT = os.path.join(TOOLS_ROOT, 'groovy')

ENVIRONMENT_FILE = os.path.join(ROOT, 'environment.sh')

# Utility variables
bash_header = '''
    set -e
    source {}
'''.format(ENVIRONMENT_FILE)
MANUAL_INSTALL = get_var('mode', 'auto')
PIPELINE_ID = get_var('id', subprocess.check_output(['hostname'], encoding='utf-8').strip())


def replace_symlink(target, link):
    if os.path.islink(link) or os.path.isfile(link):
        os.unlink(link)
    os.symlink(target, link)


def make_executable(file):
    st = os.stat(file)
    os.chmod(file, st.st_mode | stat.S_IEXEC)


def delete_and_copy(src, dest):
    if os.path.isdir(src):
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy(src, dest)


def unzip_todir(input, directory, type):
    """
    Extracts an archive, either a .tar.gz or a .zip file into the given directory, removing any root-level
    directories inside the archive to do so
    :param input: Input file-like object
    :param directory:
    :param type: Either 'zip' or 'tgz', for specifying the type of archive in case the URL does not identify it
    :return:
    """

    # Create output if not exists
    create_folder(directory)

    # Pick a temporary directory to extract into
    tempdir = tempfile.mkdtemp()

    # Extract the files into the temp dir
    if type == 'zip':
        zip = ZipFile(input)
        zip.extractall(tempdir)
    elif type == 'tgz':
        tar = tarfile.open(fileobj=input, mode='r:gz')
        tar.extractall(tempdir)
    elif type == 'tbz2':
        tar = tarfile.open(fileobj=input, mode='r:bz2')
        tar.extractall(tempdir)
    else:
        raise ValueError('Can only download .tar.gz, .tar.bz2, or .zip file')

    # If there is only one subdirectory, take the files inside that
    files = [os.path.join(tempdir, f) for f in os.listdir(tempdir)]
    if len(files) == 1 and os.path.isdir(tempdir[0]):
        subdir = files[0]
        for subfile in [os.path.join(subdir, f) for f in os.listdir(subdir)]:
            new_file = os.path.join(directory, os.path.basename(subfile))
            shutil.move(subfile, new_file)
    # If there is no subdirectory, just files, move them directly into the destination dir
    else:
        for subfile in files:
            new_file = os.path.join(directory, os.path.basename(subfile))
            shutil.move(subfile, new_file)

    shutil.rmtree(tempdir)


# Utility functions
def download_zip(url_str, directory, type=None):
    """
    Downloads the .tar.gz or .zip file from the given URL and extracts it into the given directory, removing any root-level
    directories inside the archive to do so
    :param url_str:
    :param directory:
    :param type: either 'zip' or 'tgz', for specifying the type of archive in case the URL does not identify it
    :return:
    """

    url = urlopen(url_str)
    input = StringIO(url.read())

    # Try to deduce the type from the URL
    if not type:
        [name, ext2] = os.path.splitext(url_str)
        [name, ext1] = os.path.splitext(name)

        if ext2 == '.zip':
            type = 'zip'
        elif (ext1 == '.tar' and ext2 == '.gz') or ext2 == '.tgz':
            type = 'tgz'
        elif (ext1 == '.tar' and ext2 == '.bz2') or ext2 == '.tbz2':
            type = 'tbz2'

    unzip_todir(input, directory, type)


def cmd(command, **kwargs):
    """
    Creates a doit CmdAction with certain default parameters used by cpipe, namely using bash as the default shell,
    using the cpipe root as the working directory, and sourcing the environment file before use. Using the environment
    file instead of simply setting the subprocess's env is done to prevent the environment file becoming out of sync
    with the actual environment variables we need set
    :param command: The bash command to run
    :param kwargs: And additional arguments to pass to CmdAction or popen
    :return: A doit CmdAction
    """

    # Set default options and override then with the user specified options
    defaults = {
        'executable': 'bash',
        'shell': True,
        'cwd': ROOT
    }
    defaults.update(kwargs)

    return CmdAction(
        bash_header + command,
        **defaults
    )


def sh(command, **kwargs):
    # Set default options and override then with the user specified options
    defaults = {
        'executable': 'bash',
        'shell': True,
        'cwd': ROOT,
        'stdout': sys.stdout
    }
    defaults.update(kwargs)
    subprocess.check_call(bash_header + command, **defaults)


def has_swift_auth():
    swift_credentials = {
        'OS_AUTH_URL',
        'OS_TENANT_ID',
        'OS_TENANT_NAME',
        'OS_PROJECT_NAME',
        'OS_USERNAME',
        'OS_PASSWORD'
    }

    # If the user has all the necessary environment variables set, let them download the cached assets
    # from the object store
    return swift_credentials.issubset(list(os.environ.keys()))


def manual_install():
    return MANUAL_INSTALL == 'manual'


def swift_install():
    return MANUAL_INSTALL == 'auto'


def in_docker():
    return os.path.exists('/.dockerenv')


def is_root():
    return os.geteuid() == 0
