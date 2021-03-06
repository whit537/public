#!/usr/bin/env python
from distutils.core import setup

classifiers = [
    'Development Status :: 4 - Beta'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: Freeware'
  , 'Natural Language :: English'
  , 'Operating System :: Unix'
  , 'Programming Language :: Python'
  , 'Topic :: Software Development :: Testing'
                ]

setup( name = 'pytest'
     , version = '0.3.0'
     , package_dir = {'':'site-packages'}
     , packages = ['ASTutils','PyTest']
     , description = 'Pytest is a testing interpreter for Python.'
     , author = 'Chad Whitacre'
     , author_email = 'chad [at] zetaweb [dot] com'
     , url = 'http://www.zetadev.com/software/pytest/'
     , classifiers = classifiers
      )
