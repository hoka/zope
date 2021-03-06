import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

name = "zc.recipe.testrunner"
setup(
    name = name,
    version = "1.0.2",
    author = "Jim Fulton",
    author_email = "jim@zope.com",
    description = "ZC Buildout recipe for creating test runners",
    long_description = (
        read('README.txt')
         + '\n' +
        read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('src', 'zc', 'recipe', 'testrunner', 'README.txt')
        + '\n' +
        'Download\n'
        '**********************\n'
        ),
    license = "ZPL 2.1",
    keywords = "development build testing",
    url='http://svn.zope.org/zc.buildout',

    packages = find_packages('src'),
    include_package_data = True,
    package_dir = {'':'src'},
    namespace_packages = ['zc', 'zc.recipe'],
    install_requires = ['zc.buildout  >=1.0.0b12',
                        'zope.testing<=3.4.9999', 'setuptools',
                        'zc.recipe.egg  >=1.0.0a3',
                        ],
    test_suite = name+'.tests.test_suite',
    entry_points = {'zc.buildout': ['default = %s:TestRunner' % name]},
    classifiers = [
       'Development Status :: 5 - Production/Stable',
       'Framework :: Buildout',
       'Intended Audience :: Developers',
       'License :: OSI Approved :: Zope Public License',
       'Topic :: Software Development :: Build Tools',
       'Topic :: Software Development :: Libraries :: Python Modules',
       ],
    )
