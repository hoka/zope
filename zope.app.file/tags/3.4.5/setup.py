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
"""Setup for zope.app.file package

$Id$
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(name='zope.app.file',
      version = '3.4.5',
      author='Zope Corporation and Contributors',
      author_email='zope3-dev@zope.org',
      description='File and Image -- Zope 3 Content Components',
      long_description=(
          read('README.txt')
          + '\n\n' +
          'Detailed Dcoumentation\n' +
          '----------------------\n'
          + '\n\n' +
          read('src', 'zope', 'app', 'file', 'browser', 'file.txt')
          + '\n\n' +
          read('src', 'zope', 'app', 'file', 'browser', 'url.txt')
          + '\n\n' +
          read('CHANGES.txt')
          ),
      keywords = "zope3 file image content",
      classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Zope Public License',
          'Programming Language :: Python',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: Zope3'],
      url='http://cheeseshop.python.org/pypi/zope.app.file',
      license='ZPL 2.1',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['zope', 'zope.app'],
      extras_require = dict(test=['zope.app.testing',
                                  'zope.app.securitypolicy',
                                  'zope.app.zcmlfiles',]),
      install_requires=['setuptools',
                        'ZODB3',
                        'zope.app.publication',
                        'zope.app.zapi',
                        'zope.contenttype',
                        'zope.datetime',
                        'zope.dublincore',
                        'zope.event',
                        'zope.exceptions',
                        'zope.i18nmessageid',
                        'zope.interface',
                        'zope.publisher',
                        'zope.schema',
                        'zope.size',
                        ],
      include_package_data = True,
      zip_safe = False,
      )
