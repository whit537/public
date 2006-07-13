#!/usr/bin/env python
"""This is the main httpyd callable. It configures and starts a server.
"""
import os
import sys

from httpy.couplers.standalone import StandAlone
from _httpyd import configure, ConfigError, Website


def main(argv):

    try:
        address, threads, uid, mode, paths  = configure(argv[1:])
    except ConfigError, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "`man 1 httpyd' for usage."
        raise SystemExit(2)
    else:
        os.environ['HTTPY_MODE'] = mode
        website = Website(paths)
        StandAlone(website, address, threads, uid).go()

if __name__ == '__main__':
    main(sys.argv)