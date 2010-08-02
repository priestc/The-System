#!/usr/bin/env python

from distutils.core import setup

setup(
      name='tsclient',
      version='0.4',
      description='The System uploader clent',
      scripts=['tsclient/tsup'],
      packages=['tsclient', 'poopagen', 'colorama'],
     )
