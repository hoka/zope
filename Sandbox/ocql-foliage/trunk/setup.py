"""Setup

$Id$
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup (
    name='OCQL',
    version='0.0.1',
    author = "Adam Groszer & Attila Gobi",
    author_email = "agroszer@gmail.com",
    description = "OCQL",
    long_description=(""),
    license = "ZPL V2.1",
    keywords = "",
    classifiers = [
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: Zope3'
        ],
    url = '',
    packages = find_packages('src'),
    package_dir = {'':'src'},
    namespace_packages = ['ocql'],
    extras_require = dict(
        test = [
            ],
        ),
    install_requires = [
        'setuptools',
        'ply',
        ],
    
    include_package_data = True,
    zip_safe = False,
    )
