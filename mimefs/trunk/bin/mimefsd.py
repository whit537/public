#!/usr/bin/env python
"""mimefsd -- a MIME filesystem XMLRPC server.
"""

__version__ = (0, 3)
__author__ = 'Chad Whitacre <chad@zetaweb.com>'

import logging
import os
import sha
import signal
import subprocess
import sys
import time
from StringIO import StringIO
from email import message_from_string
from email.Generator import Generator
from email.Message import Message

import psycopg
from httpy.Config import ConfigError
from httpy.Config import Config
from httpy.Server import Server
from httpy.Server import RestartingServer
from httpy.apps.XMLRPC import XMLRPCApp


format = "%(name)-16s %(levelname)-8s %(message)s"
logging.basicConfig( level=logging.DEBUG
                   , format=format
                    )
logger = logging.getLogger('mimefsd')


# TODO: add check for ownership and permissions
KEY = open('/etc/mimefs.key').read()


# Monkey-patch Task since we don't have anything on the filesystem.
# =================================================================

from httpy.Task import Task
def _validate(self):
    pass
Task.validate = _validate


# Define our Application class.
# =============================

class mimefsServerError(StandardError):
    """
    """

class Application(XMLRPCApp):

    uri_root = '/' # To play nice with httpy until it is more library-friendly.


    # Fundaments
    # ==========

    def echo(self, foo=''):
        return foo

    def _connect(self):
        """Given a database name, return a database connection.
        """
        return psycopg.connect('dbname=mimefsd_0')

    def _verify(self, key):
        """Given the master key, verify that it is correct.
        """
        if key != KEY:
            raise mimefsServerError("Bad key: '%s'" % key)

    def _uuid(self):
        """Return a universally unique 32-byte string.

        Currently we depend on uuid(1) in the OS.

        """
        p = subprocess.Popen(('uuid','-v4'), stdout=subprocess.PIPE)
        return p.stdout.read().replace('-','').strip('\n')


    # Volumes
    # ========

    def v_create(self, key):
        """Given the master key, return the vid of a new volume.
        """
        self._verify(key)
        conn = self._connect()
        curs = conn.cursor()

        vid = self._uuid()
        SQL = "INSERT INTO volume (vid) VALUES (%s);"
        curs.execute(SQL, (vid,))

        conn.commit()
        conn.close()
        return vid


    def v_destroy(self, key, vid):
        """Takes the master key and a vid.

        The tables are wired such that when a volume is destroyed, all
        messages in that volume are automatically destroyed, and their
        metadata is unindexed.

        """
        self._verify(key)
        conn = self._connect()
        curs = conn.cursor()

        SQL = "DELETE FROM volume WHERE vid=%s;"
        curs.execute(SQL, (vid,))

        conn.commit()
        conn.close()


    def v_dump(self, key):
        """Given the master key, return a bzip2'd psql script.
        """
        self._verify(key)
        raise NotImplementedError


    def v_list(self, key):
        """Return a list of all message IDs.
        """
        self._verify(key)
        conn = self._connect()
        curs = conn.cursor()

        SQL = "SELECT vid FROM volume;"
        curs.execute(SQL)
        vids = [row[0] for row in curs.fetchall()]

        conn.commit()
        conn.close()
        return vids


    def v_load(self, key, sql):
        """Takes a bzip2'd psql script.
        """
        self._verify(key)
        raise NotImplementedError


    # Messages
    # ========
    # The following all operate on a single volume.

    def m_destroy(self, vid, mid):
        """Given a message ID, destroy the message.

        The metadata unindexing is handled by a constraint in the table
        definition.

        """
        conn = self._connect()
        conn.close()

        SQL = "DELETE FROM message WHERE mid=%s;"
        curs.execute(SQL, (mid,))

        conn.commit()
        conn.close()


    def m_find(self, vid, criteria):
        """Given criteria, return mids of matching messages.
        """
        conn = self._connect()
        conn.close()
        raise NotImplementedError


    def m_headers(self, vid, mid):
        """Given a message ID, return the message's headers.

        We don't actually use the vid here, since the mid is globally unique.

        """
        conn = self._connect()
        curs = conn.cursor()

        SQL = "SELECT headers FROM message WHERE mid=%s;"
        curs.execute(SQL, (mid,))

        if curs.rowcount == -1:
            raise mimefsServerError("Error running query.")
        if curs.rowcount == 0:
            raise mimefsServerError("No message found.")
        elif curs.rowcount > 1:
            raise mimefsServerError( "mid matched %s " % str(curs.rowcount) +
                                     "messages; possible data corruption!"
                                    )

        headers = curs.fetchone()[0]

        conn.commit()
        conn.close()
        return headers


    def m_list(self, vid):
        """Return a list of all message IDs.
        """
        conn = self._connect()
        curs = conn.cursor()

        SQL = "SELECT mid FROM message;"
        curs.execute(SQL)
        mids = [row[0] for row in curs.fetchall()]

        conn.commit()
        conn.close()
        return mids


    def m_open(self, vid, mid):
        """Given a message ID, return a MIME message.
        """
        conn = self._connect()
        curs = conn.cursor()

        SQL = "SELECT headers, body FROM message WHERE mid=%s;"
        curs.execute(SQL, (mid,))

        if curs.rowcount == -1:
            raise mimefsServerError("Error running query.")
        if curs.rowcount == 0:
            raise mimefsServerError("No message found.")
        elif curs.rowcount > 1:
            raise mimefsServerError( "mid matched %s " % str(curs.rowcount) +
                                     "messages; possible data corruption!"
                                    )

        message = '\n\n'.join(curs.fetchone())

        conn.commit()
        conn.close()
        return message


    def m_store(self, vid, msg, mid=''):
        """Given a MIME message, store it.

        If a mid is given, we file the message under that mid. Otherwise we
        store and index under a new mid. In both cases we return the mid.

        """
        conn = self._connect()
        curs = conn.cursor()


        # Sanitize the message.
        # =====================
        # Convert all newlines to \n, and make sure a bodyless message has
        # two newlines at the end.

        msg = '\n'.join(msg.splitlines())
        if '\n\n' not in msg:
            msg += '\n\n'


        # Determine the mid.
        # ==================
        # If given a valid mid, just destroy the old message.

        if not mid:
            mid = self._uuid()
        else:
            SQL = "SELECT mid FROM message WHERE mid=%s;"
            curs.execute(SQL, (mid,))
            if curs.rowcount == 1:
                SQL = "DELETE FROM message WHERE mid=%s;"
                curs.execute(SQL, (mid,))
            else:
                raise mimefsServerError("Bad mid: '%s'" % mid)


        # Now store and index the message.
        # ================================

        headers, body = msg.split('\n\n', 1)

        SQL = ( "INSERT INTO message (vid, mid, headers, body) " +
                "VALUES (%s, %s, %s, %s);"
               )
        curs.execute(SQL, (vid, mid, headers, body))

        for name, body in message_from_string(headers).items():
            name = name.lower() # case insensitive
            SQL = "INSERT INTO field (mid, name, body) VALUES (%s, %s, %s);"
            curs.execute(SQL, (mid, name, body))


        # Wrap up and return.
        # ===================

        conn.commit()
        conn.close()
        return mid



# Define a callable to start the server.
# ======================================

def main(argv=None):

    # Read in configuration options.
    # ==============================
    # We override the default port number

    Config.address = ('', 5370)

    if argv is None:
        argv = sys.argv[1:]
    try:
        config = Config(argv)
    except ConfigError, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "`man 1 mimed' for usage."
        return 2


    # Instantiate and start a server.
    # ===============================

    plain_jane = (  (os.environ['HTTPY_MODE'] == 'deployment')
                 or (sys.platform == 'win32')
                 or ('HTTPY_PLAIN_JANE' in os.environ)
                   )
    ServerClass = plain_jane and Server or RestartingServer
    server = ServerClass(config)
    server.apps = [Application()]
    server.start()


if __name__ == "__main__":
    sys.exit(main())