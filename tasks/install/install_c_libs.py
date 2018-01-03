"""
Tasks for compiling C libs that are needed by various runtimes (R, perl etc.)
All of these will try to install to the C_LIBS directory (using PREFIX) so that C_LIBS contains an
include, lib, bin etc. These will then be set to the path
"""

from tasks.common import *
from tasks.nectar.nectar_util import *


# def task_install_bzip2():
#     return {
#         'actions': [
#             cmd(''' conda install -y bzip2'''),
#             (add_to_manifest, ['bzip2'])
#         ],
#         'setup': ['download_bzip2'],
#         'targets': [Path(CONDA_BIN, 'bzip2')],
#         'uptodate': [not nectar_asset_needs_update('bzip2')],
#         'getargs': {'bzip2_dir': ('download_bzip2', 'dir')},
#     }


# def task_install_xz():
#     return {
#         'actions': [
#             cmd('''
#                 cd %(xz_dir)s
#                 ./configure --prefix={}
#                 make
#                 make install
#             '''.format(INSTALL_ROOT)),
#             (add_to_manifest, ['xz'])
#         ],
#         'targets': [Path(INSTALL_BIN, 'xz')],
#         'setup': ['download_xz'],
#         'uptodate': [not nectar_asset_needs_update('xz')],
#         'getargs': {'xz_dir': ('download_xz', 'dir')},
#     }


# def task_install_pcre():
#     return {
#         'actions': [
#             cmd('''
#                 cd %(pcre_dir)s
#                 ./configure --enable-utf8 --prefix={} > /dev/null
#                 make --quiet
#                 make install --quiet
#            '''.format(INSTALL_ROOT)),
#             (add_to_manifest, ['pcre'])
#         ],
#         'setup': ['download_pcre'],
#         'targets': [Path(INSTALL_BIN, 'pcregrep')],
#         'uptodate': [not nectar_asset_needs_update('pcre')],
#         'getargs': {'pcre_dir': ('download_pcre', 'dir')},
#     }


# def task_install_libcurl():
#     return {
#         'actions': [
#             cmd('''
#                 cd %(libcurl_dir)s
#                 ./configure --prefix={}
#                 make
#                 make install
#             '''.format(INSTALL_ROOT)),
#             (add_to_manifest, ['libcurl'])
#         ],
#         'setup': ['download_libcurl'],
#         'targets': [Path(INSTALL_BIN, 'curl')],
#         'uptodate': [not nectar_asset_needs_update('libcurl')],
#         'getargs': {'libcurl_dir': ('download_libcurl', 'dir')},
#     }


# def task_install_zlib():
#     return {
#         'actions': [
#             cmd('''
#                 cd %(zlib_dir)s
#                 ./configure --prefix={}
#                 make
#                 make install
#             '''.format(INSTALL_ROOT)),
#             (add_to_manifest, ['zlib'])
#         ],
#         'targets': [Path(INSTALL_ROOT, 'lib', 'libz.so')],
#         'setup': ['download_zlib'],
#         'uptodate': [not nectar_asset_needs_update('zlib')],
#         'getargs': {'zlib_dir': ('download_zlib', 'dir')},
#     }
