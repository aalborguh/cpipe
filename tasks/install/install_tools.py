from __future__ import print_function
from pathlib import Path
import os
import glob
import sys
from tasks.nectar.nectar_util import *
from tasks.common import install_binaries
from tasks.install.install_c_libs import *

def task_install_perl():
    return {
        'actions': [
            cmd('''
               conda install -y perl
            '''),
            (add_to_manifest, ['perl'])
        ],
        'targets': [Path(CONDA_BIN, 'perl')],
        'uptodate': [not nectar_asset_needs_update('perl')],
    }


def task_install_r():
    return {
        'actions': [
            cmd('''
                conda install -y r={}
            '''.format(R_VERSION)),
            (add_to_manifest, ['r'])
        ],
        'targets': [Path(CONDA_BIN, 'R')],
        'uptodate': [not nectar_asset_needs_update('r')],
    }


def task_install_bwa():
    return {
        'actions': [
            cmd('''
                conda install -y bwa={}
            '''.format(BWA_VERSION)),
            (add_to_manifest, ['bwa'])
        ],
        'targets': [Path(CONDA_BIN, 'bwa')],
        'uptodate': [not nectar_asset_needs_update('bwa')],
    }


def task_install_htslib():
    return {
        'actions': [
            cmd('''
            conda install -y htslib={}
                '''.format(HTSLIB_VERSION)),
            (add_to_manifest, ['htslib'])
        ],
        'targets': [Path(CONDA_BIN, 'htsfile')],
        'uptodate': [not nectar_asset_needs_update('htslib')],
    }


def task_install_samtools():
    return {
        'task_dep': ['install_htslib'],
        'actions': [
            cmd('''
            conda install -y samtools={}
            '''.format(SAMTOOLS_VERSION)),
            (add_to_manifest, ['samtools'])
        ],
        'targets': [Path(CONDA_BIN, 'samtools')],
        'uptodate': [not nectar_asset_needs_update('samtools')],
    }


def task_install_bcftools():
    return {
        'actions': [
            cmd('''
            conda install -y bcftools={}
            '''.format(BCFTOOLS_VERSION)),
            (add_to_manifest, ['bcftools'])
        ],
        'targets': [Path(CONDA_BIN, 'bcftools')],
        'uptodate': [not nectar_asset_needs_update('bcftools')],
    }


def task_install_bedtools():
    return {
        'actions': [
            cmd('''
            conda install -y bedtools={version}
            '''.format(version=BEDTOOLS_VERSION)),
            (add_to_manifest, ['bedtools'])
        ],
        'targets': [Path(CONDA_BIN, 'bedtools')],
        'uptodate': [not nectar_asset_needs_update('bedtools')],
    }


def task_install_gatk():
    # If they're part of Melbourne Genomics they can use our licensed copy of GATK. Otherwise they have to install it
    # themselves
    if manual_install() or has_swift_auth():
        return {
            'actions': [
                lambda: JAVA_LIBS_ROOT.mkdir(exist_ok=True, parents=True),
                cmd('''
                    cd %(gatk_dir)s
                    GATK_JAR=`readlink -f target/GenomeAnalysisTK.jar`\
                    cp GenomeAnalysisTK.jar {}
                '''.format(JAVA_LIBS_ROOT)),
                (add_to_manifest, ['gatk'])
            ],
            'getargs': {'gatk_dir': ('download_gatk', 'dir')},
            'setup': ['download_gatk'],
            'targets': [JAVA_LIBS_ROOT / 'GenomeAnalysisTK.jar'],
            'uptodate': [not nectar_asset_needs_update('gatk')],
        }
    else:
        def action():
            print('''
                It looks like you aren't a member of Melbourne Genomics (since you don't have a swift_credentials.sh
                file in your cpipe directory). In this case, you'll have to obtain your own copy of the
                GenomeAnalysisTK.jar and place it in cpipe/tools/java_libs. You'll be able to obtain a copy from the
                Broad website: https://software.broadinstitute.org/gatk/download/
            ''', file=sys.stderr)

        return {
            'actions': [action],
            'targets': [JAVA_LIBS_ROOT / 'GenomeAnalysisTK.jar'],
            'uptodate': [not nectar_asset_needs_update('gatk')]
        }


def task_install_vep():
    def action():

        cmd("""
        conda search ensembl-vep
        conda install -y ensembl-vep={version}
        """.format(version=VEP_VERSION))
        add_to_manifest('vep')

    return {
        'actions': [action],
        'targets': [CONDA_BIN/ 'vep_install'],
        # 'uptodate': [not nectar_asset_needs_update('vep')],
    }


def task_install_fastqc():
    script_bin = Path(CONDA_BIN, 'fastqc')

    def action():
       cmd('conda install -y fastqc={version}'.format(version=FASTQC_VERSION))
       add_to_manifest('fastqc')

    return {
        'actions': [action],
        'targets': [script_bin],
        'uptodate': [not nectar_asset_needs_update('fastqc')],
    }

def task_install_vcfanno():

    def action():
        cmd('conda install -y vcfanno={version}'.format(version=VCFANNO_VERSION))
        add_to_manifest('vcfanno')

    return {
        'actions': [action],
        'targets': [CONDA_BIN / 'vcfanno'],
        'uptodate': [not nectar_asset_needs_update('vcfanno')],
    }

def task_install_bpipe():
    def action(bpipe_dir):
        delete_and_copy(bpipe_dir, BPIPE_ROOT)
        add_to_manifest('bpipe')

    return {
        'actions': [action],
        'targets': [BPIPE_ROOT, BPIPE_ROOT / 'bin' / 'bpipe'],
        'setup': ['download_bpipe'],
        'uptodate': [not nectar_asset_needs_update('bpipe')],
        'getargs': {'bpipe_dir': ('download_bpipe', 'dir')},
    }


def task_install_picard():
    picard_target = JAVA_LIBS_ROOT / 'picard.jar'

    def action(picard_dir):
        picard_jar = Path(picard_dir) / 'picard.jar'
        delete_and_copy(picard_jar, picard_target)
        add_to_manifest('picard')

    return {
        'actions': [action],
        'targets': [picard_target],
        'setup': ['download_picard'],
        'uptodate': [not nectar_asset_needs_update('picard')],
        'getargs': {'picard_dir': ('download_picard', 'dir')},
    }


def task_install_groovy():
    groovy_target = INSTALL_BIN / 'groovy'
    groovy_bin = GROOVY_ROOT / 'bin'
    def action(groovy_dir):
        # Make the groovy directory
        delete_and_copy(groovy_dir, GROOVY_ROOT)

        # Symlink all binaries to this directory
        for bin_file in os.listdir(groovy_bin):
            bin_target = groovy_bin / bin_file
            symlink = INSTALL_BIN / bin_file
            replace_symlink(bin_target, symlink)
            make_executable(bin_target)

        add_to_manifest('groovy')

    return {
        'actions': [action],
        'targets': [groovy_target, GROOVY_ROOT],
        'uptodate': [not nectar_asset_needs_update('groovy')],
        'task_dep': ['download_groovy'],
        'getargs': {'groovy_dir': ('download_groovy', 'dir')},
    }


def task_install_vep_libs():
    def action(vep_libs_dir):
        delete_and_copy(vep_libs_dir, VEP_LIBS_ROOT)
        add_to_manifest('vep_libs')

    return {
        'actions': [action],
        'uptodate': [not nectar_asset_needs_update('vep_libs')],
        'targets': [VEP_LIBS_ROOT, VEP_LIBS_ROOT / 'Bio' / 'TreeIO.pm'],
        'setup': ['download_vep_libs'],
        'getargs': {'vep_libs_dir': ('download_vep_libs', 'dir')},
    }

def task_install_java_libs():
    def action(java_libs_dir):
        JAVA_LIBS_ROOT.mkdir(parents=True, exist_ok=True)
        for file in Path(java_libs_dir).iterdir():
            delete_and_copy(file, JAVA_LIBS_ROOT)
        add_to_manifest('java_libs')

    return {
        'actions': [action],
        'uptodate': [
            not nectar_asset_needs_update('java_libs'), 
            lambda: len(list(JAVA_LIBS_ROOT.glob('*.jar'))) >= 4
        ],
        'targets': [JAVA_LIBS_ROOT],
        'setup': ['download_java_libs'],
        'getargs': {'java_libs_dir': ('download_java_libs', 'dir')},
    }


def task_install_vep_plugins():
    def action(vep_plugins_dir):
        # Copy the contents of the plugins directory to the vep_plugins dir because
        # we want to preserve the Grantham plugin that's there.
        copy_contents(vep_plugins_dir, VEP_PLUGIN_ROOT)
        add_to_manifest('vep_plugins')

    return {
        'actions': [action],
        'uptodate': [not nectar_asset_needs_update('vep_plugins')],
        'setup': ['download_vep_plugins'],
        'targets': [VEP_PLUGIN_ROOT, VEP_PLUGIN_ROOT / 'GO.pm'],
        'getargs': {'vep_plugins_dir': ('download_vep_plugins', 'dir')},
    }


def task_install_maven():
    target = CONDA_BIN / 'mvn'

    def action():
        cmd('conda install -y maven={version}'.format(version=MAVEN_VERSION))
        add_to_manifest('maven')

    return {
        'actions': [action],
        'targets': [target],
        'uptodate': [True],
    }
