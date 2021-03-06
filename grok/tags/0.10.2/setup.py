from setuptools import setup, find_packages
import os

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.txt')
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    'Download\n'
    '********\n'
    )

setup(
    name='grok',
    version='0.10.2',
    author='Grok Team',
    author_email='grok-dev@zope.org',
    url='http://grok.zope.org',
    download_url='http://cheeseshop.python.org/pypi/grok/',
    description='Grok: Now even cavemen can use Zope 3!',
    long_description=long_description,
    license='ZPL',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    include_package_data = True,
    zip_safe=False,
    install_requires=['setuptools',
                      'martian',
                      'simplejson',
                      'pytz',
                      'ZODB3',
                      'zope.annotation',
                      'zope.app.apidoc',
                      'zope.app.applicationcontrol',
                      'zope.app.appsetup',
                      'zope.app.authentication',
                      'zope.app.catalog',
                      'zope.app.component',
                      'zope.app.container',
                      'zope.app.folder',
                      'zope.app.intid',
                      'zope.app.keyreference',
                      'zope.app.pagetemplate',
                      'zope.app.publication',
                      'zope.app.publisher',
                      'zope.app.renderer',
                      'zope.app.security',
                      'zope.app.securitypolicy',
                      'zope.app.testing',
                      'zope.app.twisted',
                      'zope.app.zcmlfiles',
                      'zope.component',
                      'zope.configuration',
                      'zope.dottedname',
                      'zope.deprecation',
                      'zope.event',
                      'zope.formlib',
                      'zope.hookable',
                      'zope.i18nmessageid',
                      'zope.interface',
                      'zope.lifecycleevent',
                      'zope.pagetemplate',
                      'zope.proxy',
                      'zope.publisher',
                      'zope.schema',
                      'zope.security',
                      'zope.testing',
                      'zope.traversing',
                      'zope.testbrowser',
                      'zc.catalog',
                      'z3c.flashmessage',
                      ],
)
