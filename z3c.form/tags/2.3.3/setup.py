##############################################################################
#
# Copyright (c) 2007-2009 Zope Foundation and Contributors.
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
"""Setup

$Id$
"""
import os
import xml.sax.saxutils
from setuptools import setup, find_packages

def read(*rnames):
    text = open(os.path.join(os.path.dirname(__file__), *rnames)).read()
    text = unicode(text, 'utf-8').encode('ascii', 'xmlcharrefreplace')
    return xml.sax.saxutils.escape(text)

chapters = '\n'.join(
    [read('src', 'z3c', 'form', name)
    for name in ('README.txt',
                 'form.txt',
                 'group.txt',
                 'subform.txt',
                 'field.txt',
                 'button.txt',
                 'zcml.txt',
                 'validator.txt',
                 'widget.txt',
                 'action.txt',
                 'value.txt',
                 'datamanager.txt',
                 'converter.txt',
                 'term.txt',
                 'util.txt')])


setup (
    name='z3c.form',
    version = '2.3.3',
    author = "Stephan Richter, Roger Ineichen and the Zope Community",
    author_email = "zope-dev@zope.org",
    description = "An advanced form and widget framework for Zope 3",
    long_description=(
        read('README.txt')
        + '\n\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' + chapters
        + '\n\n' +
        read('CHANGES.txt')
        ),
    license = "ZPL 2.1",
    keywords = "zope3 form widget",
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
    url = 'http://pypi.python.org/pypi/z3c.form',
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['z3c'],
    extras_require = dict(
        extra = [
            'z3c.pt >= 1.0b4',
            'z3c.ptcompat',
        ],
        test = [
            'lxml >= 2.1.1',
            'z3c.coverage',
            'z3c.template',
            'zc.sourcefactory',
            'zope.app.component',
            # zope.app.container pulls in zope.container, if newer version
            'zope.app.container',
            'zope.app.pagetemplate',
            'zope.app.security',
            'zope.app.testing',
            'zope.testing',
            ],
        zope34 = [
            'zope.app.component',
            ],
        latest = [
            'zope.site',
            ],
        adding = ['zope.app.container'],
        docs = ['z3c.recipe.sphinxdoc'],
        ),
    install_requires = [
        'setuptools',
        'zope.browser',
        'zope.component',
        'zope.configuration',
        'zope.event',
        'zope.i18n',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.lifecycleevent',
        'zope.location',
        'zope.pagetemplate',
        'zope.publisher',
        'zope.schema >= 3.6.0',
        'zope.security',
        # Since the required package depends on the versions of the other
        # packages, so not require it directly.
        #'zope.site' or 'zope.app.component',
        'zope.traversing',
        ],
    zip_safe = False,
    )
