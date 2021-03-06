#############################################################################
#
# Copyright (c) 2011 Zope Foundation and Contributors.
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

from setuptools import setup, find_packages


setup(
    name='gocept.xmlrpcskin',
    version='1.1dev',
    author='gocept',
    author_email='mail@gocept.com',
    url='http://pypi.python.org/pypi/gocept.xmlrpcskin',
    description="""\
An extension to ``zope.publisher`` that provides a ZCML
directive for XML-RPC views that supports a ``layer`` parameter.""",
    long_description=(
        open('README.txt').read()
        + '\n\n'
        + open('CHANGES.txt').read()),
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL',
    namespace_packages=['gocept'],
    install_requires=[
        'setuptools',
        'zope.app.publisher',
        'zope.component[zcml]',
        'zope.configuration',
        'zope.interface',
        'zope.publisher>=3.6.0',
        'zope.security',
        'zope.traversing',
    ],
    extras_require=dict(test=[
        'unittest2',
        'zope.app.appsetup',
        'zope.app.publication',
        'zope.app.testing',
        'zope.browserpage',
        'zope.location',
        'zope.principalregistry',
        'zope.securitypolicy',
        'zope.testbrowser[zope-functional-testing]',
    ]),
)
