from ftplib import FTP
import sys
from tasks.common import *
from doit.tools import create_folder
import pymysql
from tasks.nectar.nectar_util import *
from doit.tools import run_once
from os import path

def download_ftp_list(ftp, files, target_dir, file_prefix=''):
    for file in files:
        output = os.path.join(target_dir, file)

        if not path.isfile(output):
            ftp.retrbinary(
                'RETR {}'.format(os.path.join(file_prefix, file)),
                open(output, 'wb').write
            )


def task_download_dbnsfp():
    targets = [os.path.join(DATA_ROOT, 'dbnsfp', 'dbNSFP.gz')]
    if swift_install():
        return nectar_install('dbnsfp', {'targets': targets})
    else:
        DBNSFP_ROOT = os.path.join(DATA_ROOT, 'dbnsfp')

        return {
            'targets': targets,
            'actions': [
                lambda: download_zip("ftp://dbnsfp:dbnsfp@dbnsfp.softgenetics.com/dbNSFPv{}.zip".format(DBNSFP_VERSION),
                                     DBNSFP_ROOT),
                cmd('''
                mkdir -p dbnsfp\
                && pushd {data_dir}/dbnsfp\
                    && head -n1 dbNSFP*chr1 > h\
                    && cat dbNSFP*chr* | grep -v ^#chr | sort -k1,1 -k2,2n - | cat h - | bgzip -c > dbNSFP.gz\
                    && tabix -s 1 -b 2 -e 2 dbNSFP.gz\
                    && bash -O extglob -c 'rm -rf !(dbNSFP.gz*)'
                '''.format(data_dir=DATA_ROOT), cwd=DATA_ROOT, executable='bash')
            ],
            'task_dep': [
                'install_htslib',
                'copy_config'
            ],
            'uptodate': [run_once],
        }


VEP_CACHE = os.path.join(DATA_ROOT, 'vep_cache')
def task_install_vep_cache():
    targets = [VEP_CACHE]
    if swift_install():
        return nectar_install('vep_cache', {'targets': targets})
    else:
        return {
            'targets': targets,
            'actions': [
                lambda: create_folder(VEP_CACHE),
                '''perl {tools_dir}/vep/INSTALL.pl\
                --NO_HTSLIB\
                --CACHEDIR {cache}\
                --AUTO cf\
                --SPECIES homo_sapiens_refseq\
                --ASSEMBLY GRCh37'''.format(tools_dir=TOOLS_ROOT, cache=VEP_CACHE)
            ],
            'task_dep': [
                'install_htslib',
                'install_perl_libs',
                'copy_config'
            ],
            'uptodate': [run_once],
        }

UCSC_ROOT = os.path.join(DATA_ROOT, 'ucsc')
def task_obtain_ucsc():
    if swift_install():
        return nectar_install('ucsc', {'targets': [UCSC_ROOT]})#, UCSC_SAMTOOLS_INDEX, UCSC_BWA_INDEX]})
    else:
        return {
            'actions': None,
            'targets': [UCSC_ROOT],
            'task_dep': ['download_ucsc', 'index_reference_files']
        }

def task_download_ucsc():
        return {
            'actions': [
                lambda: download_ftp_list(
                    FTP("ftp.broadinstitute.org",
                        user="gsapubftp-anonymous"),
                    ["ucsc.hg19.dict.gz", "ucsc.hg19.fasta.gz", "ucsc.hg19.fasta.fai.gz"],
                    UCSC_ROOT,
                    'bundle/hg19/'
                )
            ],
            'uptodate': [run_once],
        }


def task_download_mills_and_1000g():
    MILLS_ROOT = DATA_ROOT / 'mills_and_1000g'
    mills_files = ["Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.gz", "Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.idx.gz"]
    targets = [(MILLS_ROOT / file).with_suffix('') for file in mills_files]

    if swift_install():
        return nectar_install('mills_and_1000g', {'targets': targets})
    else:
        def action():
            download_ftp_list(
                    FTP("ftp.broadinstitute.org", user="gsapubftp-anonymous"), 
                    mills_files,
                    MILLS_ROOT,
                    'bundle/hg19/'
            )

        return {
            'targets': targets,
            'actions': [
                # Download all the files
                action,
                # Then unzip them
                f'gunzip {MILLS_ROOT}/*.gz --force'
            ],
            'uptodate': [True],
        }

DBSNP_ROOT = os.path.join(DATA_ROOT, 'dbsnp')
dbsnp_files = ["dbsnp_138.hg19.vcf.gz", "dbsnp_138.hg19.vcf.idx.gz"]
def task_download_dbsnp():
    targets = [os.path.join(DBSNP_ROOT, file) for file in dbsnp_files]
    if swift_install():
        return nectar_install('dbsnp', {'targets': targets})
    else:
        return {
            'targets': targets,
            'actions': [
                lambda: download_ftp_list(
                    FTP("ftp.broadinstitute.org",
                        user="gsapubftp-anonymous"),
                    dbsnp_files,
                    DBSNP_ROOT,
                    'bundle/hg19/'
                )
            ],
            'uptodate': [run_once],
        }


TRIO_REFINEMENT_FILE = '{data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.hg19.vcf.gz'.format(data_dir=DATA_ROOT)

def task_obtain_trio_refinement():
    if swift_install():
        return nectar_install('1000G_phase3', {'targets': [TRIO_REFINEMENT_FILE]})
    else:
        return {
            'actions': None,
            'task_dep': ['convert_trio_refinement'],
            'targets': [TRIO_REFINEMENT_FILE],
        }

def task_convert_trio_refinement():
    """
    This task will perform a complete install of the trio refinement file from scratch, no need to include download_trio_refinment and
    download_refinement_liftover in your task_dep since this already declares these as dependencies
    :return:
    """
    return {
        'actions': [
            cmd(
                '''
                 java -jar $TOOLS_ROOT/picard/picard.jar LiftoverVcf \
                        I={data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.vcf \
                        O={data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.hg19.vcf \
                        CHAIN={data_dir}/1000G_phase3/b37tohg19.chain \
                        REJECT={data_dir}/1000G_phase3/liftover.rejected_variants.vcf \
                        R={data_dir}/ucsc/ucsc.hg19.fasta\
                    && bgzip {data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.hg19.vcf \
                    && tabix -p vcf {data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.hg19.vcf.gz

                bash -O extglob -c "rm -rf {data_dir}/1000G_phase3/!(1000G_phase3_v4_20130502.sites.hg19.vcf.gz*)"
                '''.format(data_dir=DATA_ROOT),
                executable='bash'
            ),
            ''.format(DATA_ROOT)
        ],
        'task_dep': [
            'download_trio_refinement',
            'download_refinement_liftover',
            'install_htslib',
            'copy_config'
        ],
        'uptodate': [run_once]
    }


def task_download_trio_refinement():
    RAW_VCF = '{}/1000G_phase3/1000G_phase3_v4_20130502.sites.vcf'.format(DATA_ROOT)

    return {
        'actions': [
            '''
            mkdir -p {data_dir}/1000G_phase3\
            && curl \
                --user gsapubftp-anonymous:cpipe.user@cpipeline.org \
                 ftp://ftp.broadinstitute.org/bundle/b37/1000G_phase3_v4_20130502.sites.vcf.gz \
                 | gunzip > {data_dir}/1000G_phase3/1000G_phase3_v4_20130502.sites.vcf
            '''.format(data_dir=DATA_ROOT)
        ],
        #'targets': [RAW_VCF],
        # The task is up to date if the final refinement file exists or if just this step's product exists
        'uptodate': [lambda: os.path.exists(TRIO_REFINEMENT_FILE) or os.path.exists(RAW_VCF)]
    }


def task_download_refinement_liftover():
    LIFTOVER_FILE = '{}/b37tohg19.chain'.format(DATA_ROOT)

    return {
        'actions': [
            '''
           wget \
                    --user gsapubftp-anonymous:cpipe.user@cpipeline.org \
                     -P {data_dir}/1000G_phase3 \
                     ftp://gsapubftp-anonymous@ftp.broadinstitute.org/Liftover_Chain_Files/b37tohg19.chain
            '''.format(data_dir=DATA_ROOT)
        ],
        #'targets': [LIFTOVER_FILE],
        # The task is up to date if the final refinement file exists or if just this step's product exists
        'uptodate': [lambda: os.path.exists(TRIO_REFINEMENT_FILE) or os.path.exists(LIFTOVER_FILE)]
    }


CHROMOSOME_DIR = os.path.join(DATA_ROOT, 'chromosomes')
CHROMOSOME_FILE = os.path.join(CHROMOSOME_DIR, 'hg19.genome')

def task_download_chromosome_sizes():
    targets = [CHROMOSOME_DIR, CHROMOSOME_FILE]
    if swift_install():
        return nectar_install('chromosomes', {'targets': targets})
    else:
        def download_chromosome_size():
            create_folder(CHROMOSOME_DIR)

            connection = pymysql.connect(host='genome-mysql.cse.ucsc.edu', user='genome')
            with connection.cursor() as cursor, open(CHROMOSOME_FILE, 'w') as chrom_file:
                cursor.execute('select chrom, size from hg19.chromInfo')
                for line in cursor.fetchall():
                    chrom_file.write('\t'.join([str(el) for el in line]) + '\n')

        return {
            'targets': targets,
            'actions': [
                download_chromosome_size
            ],
            'uptodate': [run_once]
        }


def task_index_reference_files():
    return {
        'task_dep': [
            'bwa_index_ucsc_reference',
            'samtools_index_ucsc_reference'
        ],
        'actions': None
    }


UCSC_BWA_INDEX = '{data}/ucsc/ucsc.hg19.fasta.bwt'.format(data=DATA_ROOT)
def task_bwa_index_ucsc_reference():
    return {
        'targets': [UCSC_BWA_INDEX],
        'actions': [
            '{tools}/bwa/bwa index -a bwtsw {data}/ucsc/ucsc.hg19.fasta'.format(tools=TOOLS_ROOT, data=DATA_ROOT)
        ],
        'task_dep': [
            'install_bwa',
            'download_ucsc',
            'copy_config'
        ],
        'uptodate': [True]
    }


UCSC_SAMTOOLS_INDEX = '{data}/ucsc/ucsc.hg19.fasta.fai'.format(data=DATA_ROOT)
def task_samtools_index_ucsc_reference():
    return {
        'targets': [UCSC_SAMTOOLS_INDEX],
        'actions': [
            '{tools}/samtools/samtools faidx {data}/ucsc/ucsc.hg19.fasta'.format(tools=TOOLS_ROOT, data=DATA_ROOT)
        ],
        'task_dep': [
            'install_samtools',
            'download_ucsc',
            'copy_config'
        ],
        'uptodate': [True]
    }