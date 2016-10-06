from doit.tools import create_folder
import tempfile
import glob
import re

from tasks.common import *


def task_tool_assets():
    """
    Downloads all the tools needed to run cpipe and install other tools
    :return:
    """
    return {
        'actions': None,
        'task_dep': [
            'download_cpanm',
            'download_perl',
            'download_r',
            'download_groovy',
            'download_bwa',
            'download_htslib',
            'download_samtools',
            'download_bcftools',
            'download_bedtools',
            'download_vep',
            'download_fastqc',
            'download_bpipe',
            'download_gatk',
            'download_picard',
            'download_perl_libs',
            'download_vep_libs',
            'download_vep_plugins',
            'download_java_libs',
            'download_maven'
        ],
    }

def task_download_maven():
    return {
        'targets': [MAVEN_ROOT],
        'actions': [
            lambda: create_folder(MAVEN_ROOT),
            lambda: download_zip(
                'http://apache.mirror.serversaustralia.com.au/maven/maven-3/{version}/binaries/apache-maven-{version}-bin.tar.gz'.format(version=MAVEN_VERSION),
                MAVEN_ROOT
            )
        ],
        'uptodate': [True]
    }


def task_download_cpanm():
    return {
        'targets': [CPANM_ROOT],
        'actions': [
            lambda: create_folder(CPANM_ROOT),
            cmd('''
                curl -L https://cpanmin.us/ -o cpanm
                chmod +x cpanm
            ''', cwd=CPANM_ROOT),
        ],
        'uptodate': [True]
    }

def task_download_perl():
    return {
        'targets': [PERL_ROOT],
        'actions': [
            lambda: download_zip("http://www.cpan.org/src/5.0/perl-{0}.tar.gz".format(PERL_VERSION), PERL_ROOT),
            "mv {0}/configure.gnu {0}/configure.sh".format(PERL_ROOT),
        ],
        'uptodate': [True]
    }


def task_download_r():
    return {
        'targets': [R_ROOT],
        'actions': [
            lambda: download_zip("http://cran.csiro.au/src/base/R-3/R-{0}.tar.gz".format(R_VERSION), R_ROOT),
        ],
        'uptodate': [True]
    }


def task_download_groovy():
    return {
        'targets': [GROOVY_ROOT],
        'actions': [
            lambda: download_zip(
                "https://dl.bintray.com/groovy/maven/apache-groovy-binary-{0}.zip".format(GROOVY_VERSION), GROOVY_ROOT)
        ],
        'uptodate': [True]
    }


def task_download_bwa():
    BWA_ROOT = os.path.join(TOOLS_ROOT, 'bwa')
    return {
        'targets': [BWA_ROOT],
        'actions': [
            lambda: download_zip(
                "https://codeload.github.com/lh3/bwa/tar.gz/v{0}".format(BWA_VERSION), BWA_ROOT, type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_htslib():
    HTSLIB_ROOT = os.path.join(TOOLS_ROOT, 'htslib')
    return {
        'targets': [HTSLIB_ROOT],
        'actions': [
            lambda: download_zip(
                "https://codeload.github.com/samtools/htslib/tar.gz/{0}".format(HTSLIB_VERSION), HTSLIB_ROOT,
                type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_samtools():
    SAMTOOLS_ROOT = os.path.join(TOOLS_ROOT, 'samtools')
    return {
        'targets': [SAMTOOLS_ROOT],
        'actions': [
            lambda: download_zip(
                "https://codeload.github.com/samtools/samtools/tar.gz/{0}".format(HTSLIB_VERSION), SAMTOOLS_ROOT,
                type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_bcftools():
    BCFTOOLS_ROOT = os.path.join(TOOLS_ROOT, 'bcftools')
    return {
        'targets': [BCFTOOLS_ROOT],
        'actions': [
            lambda: download_zip(
                "https://codeload.github.com/samtools/bcftools/tar.gz/{0}".format(HTSLIB_VERSION), BCFTOOLS_ROOT,
                type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_bedtools():
    BEDTOOLS_ROOT = os.path.join(TOOLS_ROOT, 'bedtools')
    return {
        'targets': [BEDTOOLS_ROOT],
        'actions': [
            lambda: download_zip(
                "https://codeload.github.com/arq5x/bedtools2/tar.gz/v{0}".format(BEDTOOLS_VERSION), BEDTOOLS_ROOT,
                type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_vep():
    def extract_vep():
        """Download ensembl tools and move VEP out of the tools directory"""

        VEP_TEMP = tempfile.mkdtemp()
        VEP_SUBDIR = os.path.join(VEP_TEMP, 'scripts', 'variant_effect_predictor')

        download_zip("https://github.com/Ensembl/ensembl-tools/archive/release/{0}.zip".format(VEP_VERSION), VEP_TEMP)
        os.rename(VEP_SUBDIR, VEP_ROOT)
        shutil.rmtree(VEP_TEMP)

    return {
        'targets': [VEP_ROOT],
        'actions': [extract_vep],
        'uptodate': [True]
    }


def task_download_fastqc():
    FASTQC_ROOT = os.path.join(TOOLS_ROOT, 'fastqc')
    FASTQC_EXE = os.path.join(FASTQC_ROOT, 'fastqc')

    return {
        'targets': [FASTQC_ROOT],
        'actions': [
            lambda: download_zip(
                "http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v{0}.zip".format(FASTQC_VERSION),
                FASTQC_ROOT),
            'chmod +x {fastqc}'.format(fastqc=FASTQC_EXE)
        ],
        'uptodate': [True]
    }


def task_download_bpipe():
    BPIPE_ROOT = os.path.join(TOOLS_ROOT, 'bpipe')
    return {
        'targets': [BPIPE_ROOT],
        'actions': [
            cmd('''
            git clone -c advice.detachedHead=false -b {bpipe_ver} --depth 1 https://github.com/ssadedin/bpipe {bpipe_dir}\
            && cd {bpipe_dir}\
            && ./gradlew dist
            '''.format(bpipe_dir=BPIPE_ROOT, bpipe_ver=BPIPE_VERSION), cwd=TOOLS_ROOT)
        ],
        'uptodate': [True]
    }


def task_download_gatk():
    GATK_ROOT = os.path.join(TOOLS_ROOT, 'gatk')
    return {
        'targets': [GATK_ROOT],
        'actions': [
            lambda: download_zip("https://codeload.github.com/broadgsa/gatk-protected/tar.gz/{}".format(GATK_VERSION),
                                 GATK_ROOT,
                                 type='tgz')
        ],
        'uptodate': [True]
    }


def task_download_picard():
    PICARD_ROOT = os.path.join(TOOLS_ROOT, 'picard')

    def action():
        create_folder(PICARD_ROOT)
        urlretrieve(
            'https://github.com/broadinstitute/picard/releases/download/{0}/picard.jar'.format(PICARD_VERSION),
            os.path.join(PICARD_ROOT, 'picard.jar')
        )

    return {
        'targets': [os.path.join(PICARD_ROOT, 'picard.jar')],
        'actions': [action],
        'uptodate': [True]
    }


def task_download_perl_libs():
    """
    Downloads all cpan libs into the cpan directory. Each dependency is a subtask
    :return:
    """

    def cpan_exists(dependency):
        """
        Returns true if the CPAN_ROOT directory contains the given cpan module
        :param dependency:
        :return:
        """
        module_name = dependency.split('::')[-1]
        for root, dirnames, filenames in os.walk(CPAN_ROOT):
            for filename in filenames:
                if module_name in filename:
                    return True

        return False

    CPAN_TEMP = os.path.join(TOOLS_ROOT, 'cpan_temp')

    # This first subtask creates the cpan root
    yield {
        'name': 'create_cpan_root',
        'targets': [CPAN_ROOT],
        'actions': [
            lambda: create_folder(CPAN_ROOT),
            lambda: create_folder(CPAN_TEMP),
        ],
        'uptodate': [True]
    }

    # Subsequent tasks download a cpan module and its dependencies by reading the cpanfile
    with open(os.path.join(INSTALL_ROOT, 'cpanfile'), 'r') as cpanfile:
        for line in cpanfile:
            dependency = re.match("requires '(.+)';", line).group(1)
            yield {
                'name': dependency,
                'task_dep': ['download_perl', 'compile_perl', 'download_cpanm'],
                'uptodate': [lambda: cpan_exists(dependency)],
                'actions': [
                    # 'cpanm -L /dev/null --save-dists /home/michael/Programming/cpipe_installer/cpipe/tools/cpan --scandeps Archive::Zip'
                    'perl {cpanm} -L /dev/null --save-dists {libs} --scandeps {module}'.format(libs=CPAN_TEMP, module=dependency, cpanm=CPANM_EXE),
                    'rsync -av {src}/ {dest}/'.format(src=CPAN_TEMP, dest=CPAN_ROOT),
                    'rm -rf {tmp}/*'.format(tmp=CPAN_TEMP)
                ]
            }

    # This last subtask deletes the temporary cpan dir
    yield {
        'name': 'delete_cpan_temp',
        'actions': [
            lambda: shutil.rmtree(CPAN_TEMP),
        ],
        'uptodate': [lambda: not os.path.exists(CPAN_TEMP)]
    }


def task_download_vep_libs():
    return {
        'targets': [os.path.join(PERL_LIB_ROOT, 'lib/perl5/Bio/EnsEMBL')],
        'task_dep': ['install_perl_libs'],
        'actions': [
            cmd('yes | perl {vep_dir}/INSTALL.pl --NO_HTSLIB --AUTO a --DESTDIR {perl5}'.format(
                vep_dir=VEP_ROOT,
                perl5=os.path.join(PERL_LIB_ROOT, 'lib/perl5')
            ))
        ],
        'uptodate': [True]
    }


def task_download_vep_plugins():
    VEP_PLUGIN_ROOT = os.path.join(TOOLS_ROOT, 'vep_plugins')
    return {
        'targets': [os.path.join(VEP_PLUGIN_ROOT, 'Condel.pm')],
        'actions': [
            cmd('''
            git init\
            && git remote add origin https://github.com/Ensembl/VEP_plugins\
            && git fetch\
            && git checkout -t origin/master\
            && git reset --hard $VEP_PLUGIN_COMMIT\
            && rm -rf .git
            ''', cwd=VEP_PLUGIN_ROOT)
        ],
        'uptodate': [True]
    }


def task_download_java_libs():
    return {
        'actions': None,
        'task_dep': [
            'download_junit_xml_formatter',
            'download_groovy_ngs_utils',
            'download_takari_cpisuite'
        ]
    }

def task_make_java_libs_dir():
    return {
        'actions': [
            create_folder(JAVA_LIBS_ROOT),
        ],
        'targets': [JAVA_LIBS_ROOT],
        'uptodate': [True]
    }

def task_download_junit_xml_formatter():
    return {
        'actions': [
            cmd('''
                git clone https://github.com/barrypitman/JUnitXmlFormatter\
                && pushd JUnitXmlFormatter\
                    && mvn install\
                    && mv target/JUnitXmlFormatter* {java_libs_dir}\
                && popd\
                && rm -rf JUnitXmlFormatter
            '''.format(java_libs_dir=JAVA_LIBS_ROOT), cwd=JAVA_LIBS_ROOT)
        ],
        'task_dep': ['make_java_libs_dir', 'download_maven'],
        'uptodate': [
            lambda: len(glob.glob(os.path.join(JAVA_LIBS_ROOT, 'JUnitXmlFormatter*.jar'))) > 0
        ]
    }


def task_download_groovy_ngs_utils():
    return {
        'targets': [os.path.join(JAVA_LIBS_ROOT, 'groovy-ngs-utils.jar')],
        'actions': [
            cmd('''
              git clone https://github.com/ssadedin/groovy-ngs-utils -b upgrade-biojava --depth=1 --quiet\
                && pushd groovy-ngs-utils\
                && ./gradlew jar \
                && popd\
                && mv {java_libs_dir}/groovy-ngs-utils/build/libs/groovy-ngs-utils.jar {java_libs_dir}\
                && rm -rf groovy-ngs-utils
            '''.format(java_libs_dir=JAVA_LIBS_ROOT), cwd=JAVA_LIBS_ROOT)
        ],
        'task_dep': ['make_java_libs_dir', 'download_maven'],
        'uptodate': [True],
    }


def task_download_takari_cpisuite():
    return {
        'actions': [
            cmd('''
             mvn dependency:copy \
                    -Dartifact=io.takari.junit:takari-cpsuite:{cpsuite_version}\
                    -DoutputDirectory={java_libs_dir}\
                    -DstripVersion=true
            '''.format(cpsuite_version=CPSUITE_VERSION, java_libs_dir=JAVA_LIBS_ROOT), cwd=JAVA_LIBS_ROOT)
        ],
        'task_dep': ['make_java_libs_dir', 'download_maven'],
        'uptodate': [
            lambda: len(glob.glob(os.path.join(JAVA_LIBS_ROOT, 'takari-cpsuite*'))) > 0
        ],
    }
