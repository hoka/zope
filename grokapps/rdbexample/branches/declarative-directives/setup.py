from setuptools import setup, find_packages

version = '0.0'

setup(name='rdbexample',
      version=version,
      description="",
      long_description="""\
""",
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[], 
      keywords="",
      author="",
      author_email="",
      url="",
      license="",
      package_dir={'': 'src'},
      packages=find_packages('src'),
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'grok',
                        'megrok.rdb',
                        'psycopg2',
                        ],
      entry_points="""
      # Add entry points here
      """,
      )
