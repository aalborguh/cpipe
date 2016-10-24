'''
The download_* tasks are different from the install tasks because they
 - Do something that is platform independent (no compiling C code)
 - Remain all in one directory so we can zip it up
'''
from doit.tools import create_folder
import tempfile
import glob
import re
from urllib import urlopen, urlretrieve
from doit.tools import run_once

from tasks.common import *
from tasks.nectar_util import *


def download_task(url, param_name, type='tgz'):
    def action():
        temp_dir = tempfile.mkdtemp()
        return {
            param_name: download_zip(url, temp_dir, type=type)
        }

    return {
        'action': [action],
        'uptodate': [run_once]
    }


def task_tool_assets():
    """
    Downloads all the tools needed to run cpipe and install other tools
    :return:
    """
    return {
        'actions': None,
        'task_dep': [
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
        ],
    }


def task_download_maven():
    return download_task(
        'http://apache.mirror.serversaustralia.com.au/maven/maven-3/{version}/binaries/apache-maven-{version}-bin.tar.gz'.format(
            version=MAVEN_VERSION),
        'maven_dir')


def task_download_cpanm():
    if has_swift_auth():
        return nectar_task('cpanm')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
                    curl -L https://cpanmin.us/ -o cpanm
                    chmod +x cpanm
            ''', cwd=temp_dir)

        return {
            'actions': [action],
            'uptodate': [run_once]
        }


def task_download_perl():
    if has_swift_auth():
        return nectar_task('perl')
    else:
        return download_task("http://www.cpan.org/src/5.0/perl-{0}.tar.gz".format(PERL_VERSION),
                             'perl_dir')


def task_download_r():
    if has_swift_auth():
        return nectar_task('r')
    else:
        return download_task("http://cran.csiro.au/src/base/R-3/R-{0}.tar.gz".format(R_VERSION), R_ROOT)


def task_download_groovy():
    if has_swift_auth():
        return nectar_task('groovy')
    else:
        return download_task("https://dl.bintray.com/groovy/maven/apache-groovy-binary-{0}.zip".format(GROOVY_VERSION),
                             'groovy_dir')


def task_download_bwa():
    if has_swift_auth():
        return nectar_task('bwa')
    else:
        return download_task("https://codeload.github.com/lh3/bwa/tar.gz/v{0}".format(BWA_VERSION), 'bwa_dir')


def task_download_htslib():
    if has_swift_auth():
        return nectar_task('htslib')
    else:
        return download_task("https://github.com/samtools/htslib/releases/download/{0}/htslib-{0}.tar.bz2".format(
            HTSLIB_VERSION), 'htslib_dir')


def task_download_samtools():
    if has_swift_auth():
        return nectar_task('samtools')
    else:
        return download_task("https://github.com/samtools/samtools/releases/download/{0}/samtools-{0}.tar.bz2".format(
            HTSLIB_VERSION), 'samtools_dir')


def task_download_bcftools():
    if has_swift_auth():
        return nectar_task('bcftools')
    else:
        return download_task('https://github.com/samtools/bcftools/releases/download/{0}/bcftools-{0}.tar.bz2'.format(
            HTSLIB_VERSION),
            'bcftools_dir')


def task_download_bedtools():
    if has_swift_auth():
        return nectar_task('bedtools')
    else:
        return download_task("https://codeload.github.com/arq5x/bedtools2/tar.gz/v{0}".format(BEDTOOLS_VERSION),
                             'bedtools_dir')


# VEP_SUBDIR = os.path.join(VEP_TEMP, 'scripts', 'variant_effect_predictor')

def task_download_vep():
    if has_swift_auth():
        return nectar_task('vep')
    else:
        return download_task("https://github.com/Ensembl/ensembl-tools/archive/release/{0}.zip".format(VEP_VERSION),
                             'vep_dir')


def task_download_fastqc():
    if has_swift_auth():
        return nectar_task('fastqc')
    else:
        return download_task(
            "http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v{0}.zip".format(FASTQC_VERSION),
            'fastqc_dir')


def task_download_bpipe():
    if has_swift_auth():
        return download_task('bpipe', 'bpipe_dir')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
            git clone -c advice.detachedHead=false -b {bpipe_ver} --depth 1 https://github.com/ssadedin/bpipe {bpipe_dir}
            cd {bpipe_dir}
            ./gradlew dist
            '''.format(bpipe_ver=BPIPE_VERSION, bpipe_dir=temp_dir))
            return {'bpipe_dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [run_once]
        }


def task_download_gatk():
    if has_swift_auth():
        return nectar_task('gatk')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            download_zip("https://codeload.github.com/broadgsa/gatk-protected/tar.gz/{}".format(GATK_VERSION),
                         temp_dir,
                         type='tgz')
            sh('''
                mvn verify -P\!queue
           ''', cwd=temp_dir)
            return {'gatk_dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [run_once]
        }


def task_download_picard():
    if has_swift_auth():
        return download_task('picard', 'picard_dir')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            urlretrieve(
                'https://github.com/broadinstitute/picard/releases/download/{0}/picard.jar'.format(PICARD_VERSION),
                temp_dir)
            return {'picard_dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [run_once]
        }


def task_download_perl_libs():
    """
    Downloads all cpan libs into the cpan directory. Each dependency is a subtask
    :return:
    """
    if has_swift_auth():
        return nectar_task('perl_libs')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
            # Module::Build has to be installed to even work out the dependencies of perl modules, so we do that first
            # (while also saving the archive so Module::Build will be bundled on NECTAR)
            cpanm -l {perl_lib} --save-dists {cpan} Module::Build
            # Now, download archives of everything we need without installing them
            cpanm --save-dists {cpan} -L /dev/null --scandeps --installdeps .
            '''.format(cpan=temp_dir, perl_lib=PERL_LIB_ROOT))
            return {'perl_libs_dir': temp_dir}

        return {
            'task_dep': ['copy_config', 'download_perl', 'compile_perl', 'download_cpanm'],
            'uptodate': [True],
            'actions': [action]
        }


def task_download_vep_libs():
    if has_swift_auth():
        return nectar_task('vep_libs')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('perl {vep_dir}/INSTALL.pl --NO_HTSLIB --AUTO a --DESTDIR {vep_libs}'.format(vep_dir=VEP_ROOT,
                                                                                            vep_libs=temp_dir))
            return {'vep_libs_dir': temp_dir}
    return {
        'task_dep': ['copy_config', 'install_perl_libs', 'install_perl', 'install_vep'],
        'actions': [action],
        'uptodate': [run_once]
    }


def task_download_vep_plugins():
    if has_swift_auth():
        return nectar_task('vep_plugins')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
                git init
                git remote add origin https://github.com/Ensembl/VEP_plugins
                git fetch
                git checkout -t origin/master
                git reset --hard {vep_plugin_commit}
                rm -rf .git
            '''.format(vep_plugin_commit=VEP_PLUGIN_COMMIT), cwd=temp_dir)
            return {'vep_plugins_dir': temp_dir}
    return {
        'actions': [action],
        'task_dep': ['copy_config'],
        'uptodate': [run_once]
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
    def action():
        temp_dir = tempfile.mkdtemp()
        sh('''
                git clone https://github.com/barrypitman/JUnitXmlFormatter
                pushd JUnitXmlFormatter
                mvn install
            ''', cwd=temp_dir)
        return {'junit_xml_dir': temp_dir}
    return {
        'action': [action],
        'task_dep': ['copy_config', 'make_java_libs_dir', 'download_maven'],
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
        'task_dep': ['copy_config', 'make_java_libs_dir', 'download_maven'],
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
        'task_dep': ['copy_config', 'make_java_libs_dir', 'download_maven'],
        'uptodate': [
            lambda: len(glob.glob(os.path.join(JAVA_LIBS_ROOT, 'takari-cpsuite*'))) > 0
        ],
    }


def task_download_c_libs():
    return {
        'actions': None,
        'task_dep': ['download_bzip2', 'download_xz', 'download_pcre', 'download_libcurl', 'download_zlib'],
    }


def task_download_bzip2():
    def action():
        create_folder(BZIP_ROOT)
        download_zip(
            'http://www.bzip.org/{0}/bzip2-{0}.tar.gz'.format(BZIP_VERSION),
            BZIP_ROOT
        )

    return {
        'targets': [BZIP_ROOT],
        'actions': [action],
        'uptodate': [True]
    }


def task_download_xz():
    def action():
        create_folder(XZ_ROOT)
        download_zip(
            'http://tukaani.org/xz/xz-{}.tar.gz'.format(XZ_VERSION),
            XZ_ROOT
        )

    return {
        'targets': [XZ_ROOT],
        'actions': [action],
        'uptodate': [True]
    }


def task_download_pcre():
    def action():
        create_folder(PCRE_ROOT)
        download_zip(
            'ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/pcre-{}.tar.gz'.format(PCRE_VERSION),
            PCRE_ROOT
        )

    return {
        'targets': [PCRE_ROOT],
        'actions': [action],
        'uptodate': [True]
    }


def task_download_libcurl():
    def action():
        create_folder(LIBCURL_ROOT)
        download_zip(
            'https://curl.haxx.se/download/curl-{}.tar.gz'.format(LIBCURL_VERSION),
            LIBCURL_ROOT
        )

    return {
        'targets': [LIBCURL_ROOT],
        'actions': [action],
        'uptodate': [True]
    }


def task_download_zlib():
    def action():
        create_folder(ZLIB_ROOT)
        download_zip(
            'https://codeload.github.com/madler/zlib/tar.gz/v{}'.format(ZLIB_VERSION),
            ZLIB_ROOT,
            type='tgz'
        )

    return {
        'targets': [ZLIB_ROOT],
        'actions': [action],
        'uptodate': [True]
    }
