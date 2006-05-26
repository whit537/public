"""This module implements a basic httpy application.
"""
import mimetypes
import rfc822
import os
import stat
import time

from httpy import Response
from httpy.utils import mode, translate


class Responder:

    root = ''                   # The filesystem path of the document root.
    defaults = ( 'index.html'   # a sequence of names of default resources.
               , 'index.htm'
                )

    def __init__(self, root='', defaults=None):
        """Takes a filesystem path and a list of default names.
        """
        root = root or os.getcwd()
        if not os.path.isdir(root):
            raise ValueError("root '%s' does not point to a directory" % root)
        self.root = os.path.realpath(root)
        self.defaults = defaults or self.defaults


    def respond(self, request):
        return self.serve_static(request)


    def serve_static(self, request):
        """Serve a static file off of the filesystem.

        In staging and deployment modes, we honor any 'If-Modified-Since'
        header, an HTTP header used for caching.

        """

        translated = translate(request.path, self.root, self.defaults)
        ims = request.headers.get('If-Modified-Since', '')


        # Get basic info from the filesystem and start building a response.
        # =================================================================

        stats = os.stat(translated)
        mtime = stats[stat.ST_MTIME]
        size = stats[stat.ST_SIZE]
        content_type = mimetypes.guess_type(translated)[0] or 'text/plain'
        response = Response(200)


        # Support 304s, but only in deployment mode.
        # ==========================================

        if mode.IS_DEPLOYMENT or mode.IS_STAGING:
            if ims:
                mod_since = rfc822.parsedate(ims)
                last_modified = time.gmtime(mtime)
                if last_modified[:6] <= mod_since[:6]:
                    response.code = 304


        # Finish building the response and return it.
        # ===========================================

        response.headers['Last-Modified'] = rfc822.formatdate(mtime)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Length'] = size
        if response.code != 304:
            response.body = open(translated).read()
        return response


Static = Responder