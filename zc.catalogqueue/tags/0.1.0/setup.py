##############################################################################
#
# Copyright (c) Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import os
from setuptools import setup, find_packages

entry_points = """
"""

def read(rname):
    return open(os.path.join(os.path.dirname(__file__), *rname.split('/')
                             )).read()

long_description = (
        read('src/zc/catalogqueue/README.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src/zc/catalogqueue/queue.txt')
        + '\n' +
        'Download\n'
        '********\n'
        )

setup(
    name = 'zc.catalogqueue',
    version = '0.1.0',
    author = 'Jim Fulton',
    author_email = 'jim@zope.com',
    description = '',
    long_description=long_description,
    license = 'ZPL 2.1',
    
    packages = find_packages('src'),
    namespace_packages = ['zc'],
    package_dir = {'': 'src'},
    install_requires = [
        'setuptools',
        'ZODB3',
        ],
    zip_safe = False,
    entry_points=entry_points,
    include_package_data = True,
    )
