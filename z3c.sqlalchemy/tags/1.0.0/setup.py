##########################################################################
# z3c.sqlalchemy - A SQLAlchemy wrapper for Python/Zope
#
# (C) Zope Corporation and Contributor
# Written by Andreas Jung for Haufe Mediengruppe, Freiburg, Germany
# and ZOPYX Ltd. & Co. KG, Tuebingen, Germany
##########################################################################


import os
from setuptools import setup, find_packages


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Zope Public License',
    'Operating System :: OS Independent',
    'Framework :: Zope2',
    'Framework :: Zope3',
    'Programming Language :: Python',
    'Topic :: Database :: Front-Ends',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

version_file = os.path.join('src', 'z3c', 'sqlalchemy', 'version.txt')
version = open(version_file).read().strip()

readme_file = os.path.join('src', 'z3c', 'sqlalchemy', 'README.txt')
desc = open(readme_file).read() 

changes_file = os.path.join('src', 'z3c', 'sqlalchemy', 'CHANGES.txt')
changes = open(changes_file).read()

long_description = desc + '\nChanges:\n========\n\n' + changes


setup(name='z3c.sqlalchemy',
      version=version,
      license='ZPL (see LICENSE.txt)',
      author='Andreas Jung',
      author_email='info@zopyx.com',
      maintainer='Andreas Jung',
      maintainer_email='info@zopyx.com',
      classifiers=CLASSIFIERS,
      url='http://svn.zope.org/z3c.sqlalchemy/tags/%s' % version,
      description='A SQLAlchemy wrapper for Zope 2 and Zope 3',
      long_description=long_description,
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data = True,
      zip_safe=True,
      install_requires=['setuptools',
                        'SQLAlchemy',
                        'zope.component',
                        'zope.interface',
                        'zope.schema',
                       ],
      extras_require = dict(test=['pysqlite']))
