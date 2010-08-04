#!/usr/bin/env python

from setuptools import setup
from tsclient.core import VERSION

setup(
      name='tsclient',
      version=str(VERSION),
      description='The System uploader clent',
      scripts=['tsclient/tsup', 'tsclient/tsup-gui'],
      #install_requires=['wxpython', 'colorama'],
      packages=['tsclient', 'poopagen', 'colorama'],
     )
