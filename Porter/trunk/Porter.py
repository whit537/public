"""

ok, porter

Porter is our Cmd app that basically does the ui for us. Our three data-relevant
commands are:

    add

    rm

    mv

We have data stored in three places:

    [codename] -- actually, not used atm, maybe in 0.6?

    rewrite.db -- {'domain':'server:port'}

    named.conf.frag -- fragment to be appended to named.conf, records are of the
    form:

zone "example.com" {
        type master;
        file "porter.zone";
};

    The good news here is that all we need to replace is example.com. So it
    really shouldn't be too much overhead to just generate this entire file
    fragment every time we store to disk. And the rest of the record can be
    hard-coded, so we run very little chance of screwing this up. ;-)

    [porter.zone] -- this is the main abstracted config file for named, but we
    are going to manage it manually for now (forever?)

Ok, so let's treat the db as authoritative, for these reasons:

    - it is easier to parse data out

    - it has all the data we need in it (named.conf.frag only has domain)

    - it is harder to screw up (not being plaintext)

On program initialization, we want to read data from rewrite.db into an internal
data structure or two. Then whenever we do one of [add, mv, rm] we want to save
these changes to the db and regenerate our named.conf.frag file.

"""

import os, dbm, cmd, shutil, sys
from os.path import join, abspath, isfile, isabs
from StringIO import StringIO

class PorterError(RuntimeError):
    """ error class for porter """
    pass

class Porter(cmd.Cmd):

    def __init__(self, var, *args, **kw):

        # set our data paths 
        if not isabs(var):
            var = join(sys.path[0], var)
        self.var = var
        self.db_path = join(self.var, "rewrite")
        self.frag_path = join(self.var, "named.conf.frag")

        # read in data from our db, which is a one-to-one mapping of domains
        #  to websites (website == server:port)
        db = dbm.open(self.db_path, 'c')
        domains = dict(db)
        db.close()

        # should we do some integrity checking here? i.e., make sure that all
        # domains have a www counterpart? check for dupes?

        # filter out www's for our users, we will add them back in when we
        #  write to disk
        self.domains = {}
        for domain in domains:
            if not domain.startswith('www.'):
                self.domains[domain] = domains[domain]

        # we also keep an index around
        #  a one-to-many mapping of websites to domains
        self.aliases = {}
        for domain in self.domains:
            website = self.domains[domain]
            if website in self.aliases:
                self.aliases[website].append(domain)
            else:
                self.aliases[website] = [domain]

        # and let our superclass have its way too
        cmd.Cmd.__init__(self, *args, **kw)

        # ui settings
        self.intro = """
#-------------------------------------------------------------------#
#  Porter v0.1 (c)2004 Zeta Design & Development <www.zetaweb.com>  #
#-------------------------------------------------------------------#

You are currently managing %s domains.
        """ % len(self.domains)
        self.prompt = 'porter> '




    ##
    # Completes
    ##

    def complete_domains(self,text, line, begidx, endidx):
        return [d for d in self.domains.keys() if d.startswith(text)]


    ##
    # Create/Update
    ##

    complete_mv = complete_domains

    def do_mv(self, inStr=''):
        """ alias for mk, but with tab-completion """
        self.do_mk(inStr)

    def do_add(self, inStr=''):
        """ pure alias for mk """
        self.do_mk(inStr)

    def do_mk(self, inStr=''):
        """ given a domain name and a website, map them """

        # get our arguments and validate them
        opts, args = self._parse_inStr(inStr)
        if len(args) < 3:
            print >> self.stdout, "We need a domain name, a server name, " +\
                                  "and a port number."
            return
        domain, server, port = args[:3]
        if domain.startswith('www.'):
            print >> self.stdout, "Please do not include 'www' on domains."
            return
        # not worth validating port number since it will come from "dropdown" anyway
        # not worth validating server since it will come from "dropdown" anyway
        website = ':'.join((server,port))

        # update our data
        self.domains[domain] = website
        self._write_to_disk()

        # and update our indices
        if website in self.aliases:
            if domain not in self.aliases[website]:
                self.aliases[website].append(domain)
        else:
            self.aliases[website] = [domain]


    ##
    # Read
    ##

    complete_ls = complete_domains

    def do_ls(self, inStr=''):
        """ print out a list of the domains we are managing """
        opts, args = self._parse_inStr(inStr)
        domains = self.domains.keys()
        if ('i' in opts) or ('info' in opts):
            print >> self.stdout, "You are currently managing %s domains." % len(self.domains)
            return
        if len(domains) > 0: # otherwise columnize gives us "<empty>"

            # TODO: this might be big enough to refactor into dict switch notation

            if ('r' in opts) or ('raw' in opts):
                print >> self.stdout, """
KEY                           VALUE\n%s""" % (self.ruler*60,)
                raw = dbm.open(self.db_path,'r')
                for key in dict(raw):
                    print >> self.stdout, "%s  %s" % (key.ljust(28), raw[key].ljust(28))
                print >> self.stdout
                raw.close()
            else:
                # massage our list of domains
                domains.sort(self._domain_cmp)
                if args:
                    domains = filter(lambda d: d.startswith(args[0]), domains)

                if ('l' in opts) or ('long' in opts):
                    header = """
DOMAIN NAME                   SERVER        PORT  ALIASES\n%s""" % (self.ruler*79,)
                    print >> self.stdout, header
                    for domain in domains:
                        server, portnum = self.domains[domain].split(':')
                        aliases = self.aliases[self.domains[domain]][:]
                        aliases.remove(domain) # don't list ourselves in aliases

                        domain  = domain.ljust(28)[:28]
                        server  = server.ljust(12)[:12]
                        portnum = str(portnum).rjust(4)
                        if aliases: alias = aliases.pop(0)[:28]
                        else:       alias = ''

                        record = "%s  %s  %s  %s" % (domain, server, portnum, alias)

                        print >> self.stdout, record
                        for alias in aliases:
                            print >> self.stdout, ' '*53 + alias
                    print >> self.stdout

                else:
                    # columnize is an undocumented method in cmd.py
                    self.columnize(domains, displaywidth=79)


    ##
    # Delete
    ##

    complete_rm = complete_ls

    def do_rm(self, inStr=''):
        """ given one or more domain names, remove it/them from our storage """
        opts, args = self._parse_inStr(inStr)
        for domain in args:
            if domain in self.domains:
                del self.domains[domain]
            for website in self.aliases:
                if domain in self.aliases[website]:
                    self.aliases[website].remove(domain)
        self._write_to_disk()


    ##
    # Store
    ##

    def _write_to_disk(self):
        """ given that our data is clean, store it to disk """

        # first step is to back up the current files
        shutil.copyfile(self.db_path + '.db', self.db_path + '.db.old')
        if isfile(self.frag_path):
            shutil.copyfile(self.frag_path, self.frag_path + '.old')

        # create a local copy of self.domains, adding www's back in
        #  we create separate record structs so that we can sort the one that
        #  goes to named.conf.frag, thus making testing easier
        db_records = {}; frag_records = []
        for domain in self.domains:
            website = self.domains[domain]
            db_records[domain] = website
            db_records['www.' + domain] = website
        frag_records = db_records.keys()
        frag_records.sort(self._domain_cmp)

        # now first write our db file
        db = dbm.open(self.db_path, 'n')
        for domain in db_records:
            db[domain] = db_records[domain]
        db.close()

        # then generate our named.conf fragment
        #  we generate the text before actually writing, just to be safe
        tmp = StringIO()
        print >> tmp, "\n// begin records generated by porter\n"
        record="""\
zone "%s" {
        type master;
        file "porter.zone";
};\n"""
        for domain in frag_records:
            print >> tmp, record % domain
        print >> tmp, "\n// end records generated by porter"
        named_conf_frag = tmp.getvalue()
        tmp.close()

        # so we could do some integrity checking in here if we wanted to
        #print named_conf_frag

        frag = file(self.frag_path,'w+')
        frag.write(named_conf_frag)
        frag.close()


    ##
    # Helpers
    ##

    def _parse_inStr(inStr):
        """ given a Cmd inStr string, return a tuple containing a list of
        options and a list of args """
        # for now we will just ignore opts that we don't understand
        tokens = inStr.split()
        opts = []
        args = []
        for t in tokens:
            if t.startswith('--'):
                # interpret as a word opt
                opts.append(t[2:])
            elif t.startswith('-'):
                # interpret as a sequence of single-letter opts
                opts.extend(list(t)[1:])
            else:
                # interpret as an arg
                args.append(t)
        return (opts, args)
    _parse_inStr = staticmethod(_parse_inStr)


    def emptyline(self):
        pass

    def do_EOF(self, inStr=''):
        print >> self.stdout; return True
    def do_exit(self, *foo):
        return True
    do_q = do_quit = do_exit
    def _domain_cmp(x, y):
        """

        Given two domain names, return -1, 0, or 1

        Domains should be at least two places long, i.e, example.com, not example

        first sort on SLD (second level domain)
        then sort on TLD
        then sort on tertiary

        """
        # convert to lists, checking for bad data
        try:    d1 = x.split('.')
        except: raise PorterError, "unable to parse '%s' as a domain name" % x
        try:    d2 = y.split('.')
        except: raise PorterError, "unable to parse '%s' as a domain name" % y

        # more data checks
        if len(d1) < 2:
            raise PorterError, "'%s' doesn't look like a full domain name" % x
        if len(d2) < 2:
            raise PorterError, "'%s' doesn't look like a full domain name" % y

        # marshall into the order we want for sorting
        d1tertiary = d1[:-2]; d1tertiary.reverse()
        d2tertiary = d2[:-2]; d2tertiary.reverse()
        d1 = [d1[-2], d1[-1], d1tertiary]
        d2 = [d2[-2], d2[-1], d2tertiary]

        # do the comparison
        if d1 == d2: return 0
        if d1 < d2: return -1
        if d1 > d2: return 1
    _domain_cmp = staticmethod(_domain_cmp)