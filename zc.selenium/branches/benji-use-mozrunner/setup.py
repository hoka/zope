from setuptools import setup, find_packages

setup(
    name='zc.selenium',
    version='0',
    author='Zope Corporation',
    author_email='info@zope.com',
    url='http://svn.zope.org/zc.seleinum',
    description="Selenium integration for Zope 3",
    long_description=(open('README.txt').read()
                        + '\n\n'
                        + open('CHANGES.txt').read()),
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    namespace_packages = ['zc'],
    install_requires =[
        'mozrunner',
        'setuptools',
        'wsgiref',
        'z3c.zrtresource',
        'zope.component',
        'zope.interface',
        'zope.publisher',
        'zope.testing>=3.7.4',
    ]
)
