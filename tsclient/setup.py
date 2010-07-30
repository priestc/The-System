#!/usr/bin/env python

from distutils.core import setup

setup(
      name='tsclient',
      version='1.0',
      description='The System uploader clent',
      scripts=['tsclient/tsup'],
      packages=['tsclient', 'tsclient.mutagen', 'tsclient.colorama'],
     )
