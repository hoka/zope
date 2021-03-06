##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Setup for zope.testbrowser package

$Id$
"""
import os
from setuptools import setup, find_packages

long_description = (
    '.. contents::\n\n'
    + open('README.txt').read()
    + '\n\n'
    + open(os.path.join('src', 'zope', 'testbrowser', 'README.txt')).read()
    )

setup(
    name = 'zope.testbrowser',
    version = '3.4.2dev',
    url = 'http://pypi.python.org/pypi/zope.testbrowser',
    license = 'ZPL 2.1',
    description = 'Programmable browser for functional black-box tests'
        ' (not Zope-specific)',
    author = 'Zope Corporation and Contributors',
    author_email = 'zope3-dev@zope.org',
    long_description = long_description,
    classifiers=['Environment :: Web Environment',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Zope Public License',
                 'Programming Language :: Python',
                 'Topic :: Software Development :: Testing',
                 'Topic :: Internet :: WWW/HTTP',
                 ],

    packages = find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['zope',],
    tests_require = ['zope.testing'],
    install_requires = [
        'setuptools',
        'mechanize',
        'ClientForm',
        'zope.interface',
        'zope.schema',
        ],
    extras_require = dict(
        zope = [
            'zope.app.testing',
            'zope.app.component',
            'zope.app.folder',
            'zope.app.testing',
            'zope.app.zcmlfiles',
            'zope.app.securitypolicy',
            ],
        ),
    include_package_data = True,
    zip_safe = False,
    )
