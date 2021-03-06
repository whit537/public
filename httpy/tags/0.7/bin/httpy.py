#!/usr/bin/env python
"""httpy -- a straightforward Python webserver. `man 1 httpy' for details.

The main() function below is inspired by Guido's:

  http://www.artima.com/weblogs/viewpost.jsp?thread=4829

"""

__version__ = (0, 7)
__author__ = 'Chad Whitacre <chad@zetaweb.com>'

import logging
import os
import signal
import sys
import time

from httpy.Config import ConfigError
from httpy.Config import Config
from httpy.Server import Server
from httpy.Server import RestartingServer

def main(argv=None):

    # Read in configuration options.
    # ==============================

    if argv is None:
        argv = sys.argv[1:]
    try:
        config = Config(argv)
    except ConfigError, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "`man 1 httpy' for usage."
        return 2


    # Set up top-level logging.
    # =========================

    format = "%(name)-16s %(levelname)-8s %(message)s"
    logging.basicConfig( level=logging.DEBUG
                       , format=format
                        )


    # Instantiate and start a server.
    # ===============================

    plain_jane = (  (os.environ['HTTPY_MODE'] == 'deployment')
                 or (sys.platform == 'win32')
                 or ('HTTPY_PLAIN_JANE' in os.environ)
                   )
    ServerClass = plain_jane and Server or RestartingServer
    server = ServerClass(config)
    server.start()


if __name__ == "__main__":
    sys.exit(main())
