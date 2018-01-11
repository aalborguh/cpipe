'''
The download_* tasks are different from the install tasks because they
 - Do something that is platform independent (no compiling C code)
 - Remain all in one directory so we can zip it up
'''
from tasks.common import *
from tasks.nectar.nectar_util import *


def download_task(url, type=None):
    def action():
        temp_dir = tempfile.mkdtemp()
        download_zip(url, temp_dir, type=type)
        return {
            'dir': temp_dir
        }

    return {
        'actions': [action],
        'uptodate': [False]
    }


def task_tool_assets():
    """
    Downloads all the tools needed to run cpipe and install other tools
    :return:
    """
    return {
        'actions': None,
        'task_dep': [
            'download_groovy',
            'download_vep',
            'download_bpipe',
            'download_gatk',
            'download_picard',
            'download_vep_libs',
            'download_vep_plugins',
            'download_java_libs',
            'download_vcfanno',
        ],
    }


def task_download_groovy():
    if swift_install():
        return nectar_download('groovy')
    else:
        return download_task("https://dl.bintray.com/groovy/maven/apache-groovy-binary-{0}.zip".format(GROOVY_VERSION), 'zip')


def task_download_vep():
   if swift_install():
        return nectar_download('vep')
   else:
        return download_task("https://github.com/Ensembl/ensembl-vep/archive/release/{0}.tar.gz".format(VEP_VERSION))

def task_download_bpipe():
    if swift_install():
        return nectar_download('bpipe')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
            git clone https://github.com/ssadedin/bpipe {bpipe_dir}
            cd {bpipe_dir}
            git checkout tags/{bpipe_ver}
            ./gradlew dist
            '''.format(bpipe_ver=BPIPE_VERSION, bpipe_dir=temp_dir))
            return {'dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [False]
        }


def task_download_gatk():
    if swift_install():
        return nectar_download('gatk')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            download_zip("https://codeload.github.com/broadgsa/gatk-protected/tar.gz/{}".format(GATK_VERSION),
                         temp_dir,
                         type='tgz')
            sh('''
                mvn verify -P\!queue
                GATK_JAR=`readlink -f target/GenomeAnalysisTK.jar`
                unlink target/GenomeAnalysisTK.jar
                mv $GATK_JAR ./GenomeAnalysisTK.jar
                bash -O extglob -O dotglob -c 'rm -rf !(GenomeAnalysisTK.jar)'
           ''', cwd=temp_dir)
            return {'dir': temp_dir}

        return {
            'actions': [action],
            'task_dep': ['install_maven'],
            'uptodate': [False]
        }


def task_download_picard():
    if swift_install():
       return nectar_download('picard')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            urlretrieve(
                'https://github.com/broadinstitute/picard/releases/download/{0}/picard.jar'.format(PICARD_VERSION),
                os.path.join(temp_dir, 'picard.jar')
            )
            return {'dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [False]
        }


def task_download_vep_libs():
    if swift_install():
        return nectar_download('vep_libs')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh(
                'vep_install --VERSION {version} --NO_HTSLIB --NO_TEST --AUTO a --DESTDIR {vep_libs}'.format(version=int(float(VEP_VERSION)),
                                                                                                                          vep_libs=temp_dir))
            return {'dir': temp_dir}
        return {
            'task_dep': ['copy_config', 'install_perl', 'install_vep'],
            'actions': [action],
            'uptodate': [False]
        }


def task_download_vep_plugins():
    if swift_install():
        return nectar_download('vep_plugins')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('''
                git init
                git remote add origin https://github.com/Ensembl/VEP_plugins
                git fetch
                git checkout -t origin release/{version}
                rm -rf .git
            '''.format(version=int(float(VEP_VERSION))), cwd=temp_dir)
            return {'dir': temp_dir}
        return {
            'actions': [action],
            'task_dep': ['copy_config'],
            'uptodate': [False]
        }


def task_download_java_libs():
    if swift_install():
        return nectar_download('java_libs')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            sh('gradle copyDeps -Pdir={}'.format(temp_dir))
            return {'dir': temp_dir}
            
        return {
            'actions': [action],
            'uptodate': [False]
        }

def task_download_vcfanno():
    if has_swift_auth():
        return nectar_download('vcfanno')
    else:
        def action():
            temp_dir = tempfile.mkdtemp()
            urlretrieve(
                'https://github.com/brentp/vcfanno/releases/download/v{}/vcfanno_linux64'.format(VCFANNO_VERSION),
                os.path.join(temp_dir, 'vcfanno'))
            return {'dir': temp_dir}

        return {
            'actions': [action],
            'uptodate': [False]
        }

