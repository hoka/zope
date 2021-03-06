##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
# This package is developed by the Zope Toolkit project, documented here:
# http://docs.zope.org/zopetoolkit
# When developing and releasing this package, please follow the documented
# Zope Toolkit policies as described by this documentation.
##############################################################################
"""Setup for zope.schema package
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

def _modname(path, base, name=''):
    if path == base:
        return name
    dirname, basename = os.path.split(path)
    return _modname(dirname, base, basename + '.' + name)

def alltests():
    import logging
    import pkg_resources
    import unittest

    class NullHandler(logging.Handler):
        level = 50

        def emit(self, record):
            pass

    logging.getLogger().addHandler(NullHandler())

    suite = unittest.TestSuite()
    base = pkg_resources.working_set.find(
        pkg_resources.Requirement.parse('zope.schema')).location
    for dirpath, dirnames, filenames in os.walk(base):
        if os.path.basename(dirpath) == 'tests':
            for filename in filenames:
                if filename.endswith('.py') and filename.startswith('test'):
                    mod = __import__(
                        _modname(dirpath, base, os.path.splitext(filename)[0]),
                        {}, {}, ['*'])
                    suite.addTest(mod.test_suite())
        elif 'tests.py' in filenames:
            continue
            mod = __import__(_modname(dirpath, base, 'tests'), {}, {}, ['*'])
            suite.addTest(mod.test_suite())
    return suite

setup(name='zope.schema',
      version = '3.8.0',
      url='http://pypi.python.org/pypi/zope.schema',
      license='ZPL 2.1',
      description='zope.interface extension for defining data schemas',
      author='Zope Foundation and Contributors',
      author_email='zope-dev@zope.org',
      long_description=(read('src', 'zope', 'schema', 'README.txt')
                        + '\n\n' +
                        read('src', 'zope', 'schema', 'fields.txt')
                        + '\n\n' +
                        read('src', 'zope', 'schema', 'sources.txt')
                        + '\n\n' +
                        read('src', 'zope', 'schema', 'validation.txt')
                        + '\n\n' +
                        read('CHANGES.txt')),
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['zope',],
      extras_require={'test': ['zope.testing'],
                      'docs': ['z3c.recipe.sphinxdoc']},
      install_requires=['setuptools',
                        'zope.interface',
                        'zope.event',
                       ],
      include_package_data = True,
      zip_safe = False,
      test_suite='__main__.alltests',
      tests_require='zope.testing',
      )
