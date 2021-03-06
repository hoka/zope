from setuptools import setup, find_packages, find_packages


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Zope Public License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
]

desc = open('README.txt').read().strip()
changes = open('CHANGES.txt').read().strip()
long_description = desc + '\n\nChanges\n=======\n\n'  + changes

setup(
    name='z3c.pypimirror',
    version='0.2.8',
    author='Daniel Kraft, Andreas Jung et al.',
    author_email='dk@d9t.de',
    description='A module for building a complete or a partial PyPI mirror',
    long_description=long_description,
    maintainer='Andreas Jung',
    maintainer_email='lists@zopyx.com',
    classifiers=CLASSIFIERS,
    package_dir = {'': 'src'},
    namespace_packages=['z3c'] ,
    packages=find_packages('src'),
    include_package_data=True,
    package_data={
        '' : ['*.txt', '*.sample'],
    },
    zip_safe=False,
    install_requires = ['setuptools',
                        'zc.lockfile',
                        'BeautifulSoup'],
    extras_require = {
        'test': [ 'zc.buildout' ],
    },
    entry_points = dict(console_scripts=[
        'pypimirror = z3c.pypimirror.mirror:run',
        ])
    )
