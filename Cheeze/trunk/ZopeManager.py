from AccessControl import ClassSecurityInfo
import os
from os.path import join

class ZopeManager:
    """ provides functionality to manage Zope instances """

    security = ClassSecurityInfo()

    def __init__(self):
        pass


    ##
    # info providers - these can be used in mgmt zpt's
    ##

    security.declareProtected('Manage Big Cheeze', 'zopes_list',
                                                   'skel_list',
                                                   'port_get',
                                                   )

    def zopes_list(self):
        """ return a list of available zope instances """
        return os.listdir(self.instance_root)

    def skel_list(self):
        """ return a list of available zope skel """
        if self.skel_root == '':
            return None
        else:
            return os.listdir(self.skel_root)

    def port_get(self, zope):
        """ given a zope instance, return its port number """
        import re

        # get path to zope.conf
        conf_path = join(self.instance_root, zope, 'etc/zope.conf')
        conf_file = file(conf_path).read()

        search = re.search('%define HTTP_PORT (.*)',conf_file)

        return search.group(1)


    ##
    # heavy lifters - these are only used by BigCheeze wrappers
    ##

    def _zope_create(self, name, skel, port):
        """ create a new zope instance """

        # initialize kw
        kw = self._initialize_kw()

        # import things
        import sys
        bin = join(kw['ZOPE_HOME'], 'bin')
        sys.path.append(bin)
        import copyzopeskel
        import mkzopeinstance

        # set skelsrc
        if skel == '|stock|':
            # default to using stock Zope skeleton source
            # NB: kw['HTTP_PORT'] will be meaningless!
            skelsrc = join(kw['ZOPE_HOME'], 'skel')
        else:
            skelsrc = join(self.skel_root, skel)

        # set skeltarget
        kw['INSTANCE_HOME'] = skeltarget \
                            = join(self.instance_root,name)

        # set port number
        if port == '':
            port = '80'
        else:
            port = str(port)
        kw['HTTP_PORT'] = port
        kw['FTP_PORT'] = '21' # will want to revisit this later

        # now make the zope!
        copyzopeskel.copyskel(skelsrc, skeltarget, None, None, **kw)

        # and finally create the inituser
        # username:password are hardcoded for now
        inituser = join(kw['INSTANCE_HOME'], "inituser")
        mkzopeinstance.write_inituser(inituser, 'admin', 'jesus')

        # if we are vhosting then make those changes too
        # this will be moved up into BigCheeze
        #if vhosting:
        #    # this is rote from previous product
        #    zs_name = zope['name'] + zope['port'] + '.zetaserver.com'
        #    update_vhosts({zs_name:zope['port']},www=1)

    def _zope_rename(self, old_name, new_name):
        """ rename a zope instance """
        pass

    def _set_port(self, zope, port):
        """ change a zopes port """
        pass

    def _zope_delete(self, zope):
        """ given an instance name, delete a zope """
        top = join(self.instance_root, zope)
        #raise 'top', top
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(join(root, name))
            for name in dirs:
                os.rmdir(join(root, name))
        os.rmdir(top)


    ##
    # helpers
    ##

    def _initialize_kw(self):
        """ return initial kw for use in copyzopeskel """
        import sys

        ### BEGIN COPY FROM mkzopeinstance.py ###

        # we need to distinguish between python.exe and pythonw.exe under
        # Windows in order to make Zope run using python.exe when run in a
        # console window and pythonw.exe when run as a service, so we do a bit
        # of sniffing here.
        psplit = os.path.split(sys.executable)
        exedir = join(*psplit[:-1])
        pythonexe = join(exedir, 'python.exe')
        pythonwexe = join(exedir, 'pythonw.exe')

        if ( os.path.isfile(pythonwexe) and os.path.isfile(pythonexe) and
             (sys.executable in [pythonwexe, pythonexe]) ):
            # we're using a Windows build with both python.exe and pythonw.exe
            # in the same directory
            PYTHON = pythonexe
            PYTHONW = pythonwexe
        else:
            # we're on UNIX or we have a nonstandard Windows setup
            PYTHON = PYTHONW = sys.executable

        ### END COPY FROM mkzopeinstance.py ###

        softwarehome = os.environ.get('SOFTWARE_HOME', '')
        zopehome     = os.environ.get('ZOPE_HOME', '')

        return {"PYTHON"        : PYTHON,
                "PYTHONW"       : PYTHONW,
                "SOFTWARE_HOME" : softwarehome,
                "ZOPE_HOME"     : zopehome,
                }
