#!/usr/bin/env python
"""A little script for smoke testing the httpy library.

This script is designed to be run from the root of an httpy bundle. It uses the
bundle's version of httpy rather than any currently-installed version. Besides
an initial "welcome" screen, this server publishes the bundled documentation in
HTML format.

"""
import os
import sys

if __name__ == '__main__':
    sys.path.insert(0, os.path.realpath('site-packages'))

import httpy
from httpy.couplers.standalone import StandAlone
from httpy.responders.static import Static


class Responder(Static):
    """The homepage is defined below; all else is static from doc/.
    """
    def respond(self, request):
        if request.path == '/':
            return httpy.Response(200, HOMEPAGE)
        return self.serve_static(request)


HOMEPAGE = """\
<html>
<head>
  <title>Success!</title>
  <style type="text/css">
    body {
        background: green;
        font-family: "Comic Sans MS", sans-serif;
        margin: 0;
        padding: 20px;
        text-align: center;
        }
    #hack {
        position: relative;
        width: 525px;
        height: 420px;
        background: white url("/doc/success.gif") bottom center no-repeat;
        text-align: center;
        margin: 0 auto;
        padding: 0.5em 0 0;
        }
    h1 {
        margin: 0;
        padding: 0;
        height: 70px;
        }
    p {
        margin: 0;
        padding: 0;
        }
    #version {
        position: absolute;
        bottom: 0;
        right: 0;
        padding: 2px 4px;
        background: black;
        color: white;
        font: normal 12px/14px monospace;
        }
  </style>

<body><div id="hack">
<h1>BLAM!!!!!!!!!!!!!!!!!!!!!!!!!1</h1>
<p>
  Welcome to <a href="http://www.zetadev.com/software/httpy/">httpy</a>, a sane Python HTTP library.<br />
  <a href="/doc/html/">Documentation</a>
</p>
<div id="version">
    version <b>%(version)s</b> |
    revision <b>%(revision)s</b>
</div>
</div>
</body>
</html>
""" % { 'version':httpy.__version__
      , 'revision':httpy.__revision__ or 'n/a'
       }



if __name__ == "__main__":
    StandAlone(Responder).go()
