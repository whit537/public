#!/usr/local/bin/python
# (c) 2005 Chad Whitacre <http://www.zetaweb.com/>
# This program is beerware. If you like it, buy me a beer someday.
# No warranty is expressed or implied.

import os, re, sys
from glob import glob
from sets import Set
from ConfigParser import RawConfigParser


class EOLToolkit:
    """This is a toolkit for cleaning up line endings in a tree.
    """

    __version__ = '0.9'

    def __init__(self):
        pass


    def __call__(self, subcommand, path, to_windows):
        method = getattr(self, subcommand)
        if subcommand == 'clean':
            method(path, to_windows)
        else:
            method(path)


    def _confglobs(self):
        """Get a list of patterns that match text files from the svn config.
        """

        config = RawConfigParser()
        config.optionxform = lambda x: x # stock parser is case-insensitive

        config.read(os.path.expanduser('~/.subversion/config'))
        if not config.has_section('auto-props'):
            print 'Your subversion config file has no auto-props section.'
            sys.exit(1)

        autoprops = config.options('auto-props')
        globs = Set()
        for pattern in autoprops:
            if 'svn:eol-style' in config.get('auto-props', pattern):
                globs.add(pattern)
        globs = list(globs); globs.sort()
        return globs


    def confgen(self, top):
        """Given a tree root, walk the tree and generate an auto-props section
        based on the filenames found.
        """

        globs = Set()
        for path, dirs, files in os.walk(top):
            for filename in files:
                parts = filename.split('.')
                if len(parts) > 1:
                    pattern = '*.%s' % parts[-1]
                else:
                    pattern = parts[-1]
                globs.add(pattern)

            # Skip svn directories.
            if '.svn' in dirs:
                dirs.remove('.svn')

        globs = list(globs)
        globs.sort()

        print '[miscellany]'
        print 'enable-auto-props = yes'
        print
        print '[auto-props]'
        for pattern in globs:
            print "%s = svn:eol-style=native" % pattern.ljust(12)


    def clean(self, top, to_windows):
        """Given a tree root, clean up newlines in all text files.
        """

        filepaths = self.find(top, raw=1)
        nix = re.compile(r'(?<!\r)\n')
        win = re.compile(r'\r\n')
        mac = re.compile(r'\r(?!\n)')
        j = 0; sys.stdout.write('scrubbing newlines ...')

        for path in filepaths:
            # do the replacements
            textfile = file(path, 'r+')
            tmp = textfile.read()

            if to_windows:
                tmp, k = nix.subn('\r\n', tmp)
                tmp, l = mac.subn('\r\n', tmp)
            else:
                tmp, k = win.subn('\n', tmp)
                tmp, l = mac.subn('\n', tmp)

            textfile.seek(0)
            textfile.truncate()
            textfile.write(tmp)
            textfile.close()

            # indicate progress
            if k + l > 0:
                j += 1
                if j % 50 == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()

        print ' %s files cleaned' % j


    def find(self, top, raw=0):
        """Given a tree root, walk the tree and find all text files.
        """

        textfiles = Set()
        if raw: i = 0; sys.stdout.write('locating text files ...')
        globs = self._confglobs()

        for path, dirs, foo in os.walk(top):
            for pattern in globs:
                fullpattern = '%s/%s' % (path, pattern)
                for textfile in glob(fullpattern):
                    if raw:
                        # Indicate progress.
                        i += 1
                        if i % 50 == 0:
                            sys.stdout.write('.')
                            sys.stdout.flush()
                    textfiles.add(textfile)

            # Skip Subversion directories.
            if '.svn' in dirs:
                dirs.remove('.svn')

        textfiles = tuple(textfiles)

        if raw:
            print ' %s found' % len(textfiles)
            return textfiles
        else:
            for textfile in textfiles:
                try:
                    print textfile
                except IOError:
                    # play nice with less(1)
                    pass



if __name__ == '__main__':


    # Get our subcommand.
    # ===================

    subcommand = sys.argv[1:2]
    if not subcommand:
        print "see man 1 svneol for usage"
        sys.exit(2)
    elif subcommand not in (['clean'], ['confgen'], ['find']):
        print "'%s' command not available; " % subcommand +\
              "see man 1 svneol for usage"
        sys.exit(2)
    else:
        subcommand = subcommand[0]



    # Decide if we want to convert to windows newlines.
    # =================================================

    to_windows = False
    if '-w' in sys.argv:
        to_windows = True
        sys.argv.remove('-w')



    # Determine the root of the tree.
    # ===============================

    arg = sys.argv[2:3]
    if arg:
        path = arg[0]
    else:
        path = '.'
    path = os.path.realpath(path)



    # Instantiate and invoke the toolkit.
    # ===================================

    toolkit = EOLToolkit()
    toolkit(subcommand, path, to_windows)
