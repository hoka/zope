from setuptools import setup, find_packages

setup(
    name="zc.catalog",
    version="0.1",
    packages=find_packages('src', exclude=["*.tests", "*.ftests"]),
    
    package_dir= {'':'src'},
    
    namespace_packages=['zc'],
    package_data = {
    '': ['*.txt', '*.zcml'],
    },

    zip_safe=False,
    author='Zope Project',
    author_email='zope3-dev@zope.org',
    description="""\
zc.catalog contains a number of extensions to the Zope 3 catalog,
such as some new indexes, improved globbing and stemming support,
and an alternative catalog implementation.
""",
    license='ZPL',
    keywords="zope zope3",
    )
