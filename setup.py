# -*- coding: utf-8 -*-
from setuptools import setup

__author__ = "Martin Uhrin"
__license__ = "GPLv3 and MIT, see LICENSE file"

about = {}
with open('minkipy/version.py') as f:
    exec(f.read(), about)

setup(name='minkipy',
      version=about['__version__'],
      description="Job and workflow submission made simple",
      long_description=open('README.rst').read(),
      url='https://github.com/muhrin/minkipy.git',
      author='Martin Uhrin',
      author_email='martin.uhrin.10@ucl.ac.uk',
      license=__license__,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      keywords='workflows schedulers',
      install_requires=[
          'beautifultable',
          'click',
          'mincepy[gui]>=0.12, <0.16',
          'kiwipy[rmq]~=0.6',
      ],
      extras_require={
          'dev': [
              'pip',
              'pytest>4',
              'pytest-cov',
              'pre-commit',
              'yapf',
              'prospector',
              'pylint',
              'twine',
          ],
          'docs': [
              'nbsphinx',
              'sphinx',
              'sphinx-autobuild',
          ]
      },
      packages=[
          'minkipy',
          'minkipy.cli',
      ],
      include_package_data=True,
      test_suite='test',
      entry_points={
          'console_scripts': ['minki = minkipy.cli.main:minki'],
          'mincepy.plugins.types': ['minkipy_types = minkipy.provides:get_types',]
      })
