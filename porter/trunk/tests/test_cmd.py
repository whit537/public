if __name__ == '__main__':
    import framework

import unittest, os, pdb
from os.path import join, abspath, isdir
from StringIO import StringIO
from porter.Porter import Porter

class TestCRUD(unittest.TestCase):

    def setUp(self):
        # ready,...
        self.out = StringIO()
        self.cleanUp()

        # ...set,...
        os.mkdir('var')
        self.c = Porter('var', stdout=self.out)

        # ... go!

    def tearDown(self):
        self.cleanUp()

    def cleanUp(self):
        # clean up our filesystem
        if isdir('var'):
            test_var = abspath('var')
            for datafile in os.listdir(test_var):
                os.remove(join(test_var, datafile))
            os.rmdir(test_var)

    def testListWhenEmpty(self):
        self.c.onecmd("ls")
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(os.listdir(self.c.var), ['rewrite.db'])
        # db gets created when we try to read in data, frag file not until we
        #  write

    def testBadInput(self):
        self.c.onecmd("add test")
        self.assertEqual(self.out.getvalue(), "We need a domain name, a " +\
                                              "server name, and a port " +\
                                              "number.\n")
        self.assertEqual(os.listdir(self.c.var), ['rewrite.db'])
        # didn't write, so still just one file

    def testAddOneItem(self):
        self.c.onecmd("add zetaweb.com alpin 8010")
        self.c.onecmd("ls")
        self.assertEqual(self.c.domains, {'zetaweb.com':'alpin:8010'})
        self.assertEqual(self.c.aliases, {'alpin:8010':['zetaweb.com']})
        self.assertEqual(self.out.getvalue(), 'zetaweb.com\n')
        self.assertEqual(os.listdir(self.c.var), ['rewrite.db','named.conf.frag'])
        # now we should have both files

    def testExtraInputIsIgnored(self):
        self.c.onecmd("add example.com server port Frank Sinatra sings the blues")
        self.assertEqual(self.c.domains, {"example.com":"server:port"})

    def testAddMultipleItems(self):
        self.c.onecmd("add zetaweb.com alpin 8010")
        self.c.onecmd("mk  thedwarf.com duder 8020")
        self.c.onecmd("add malcontents.org duder 8020")
        self.c.onecmd("mk  christyanity.com duder 8020")
        self.c.onecmd("add tesm.edu underbird 8310")

        domains = self.c.domains.keys(); domains.sort()
        self.assertEqual(domains, ['christyanity.com'
                                  ,'malcontents.org'
                                  ,'tesm.edu'
                                  ,'thedwarf.com'
                                  ,'zetaweb.com'
                                   ])

        aliases = self.c.aliases.keys(); aliases.sort()
        self.assertEqual(aliases, ['alpin:8010'
                                  ,'duder:8020'
                                  ,'underbird:8310'
                                   ])

        multi_domains = self.c.aliases['duder:8020']
        multi_domains.sort()
        self.assertEqual(multi_domains, ['christyanity.com'
                                        ,'malcontents.org'
                                        ,'thedwarf.com'
                                         ])

        single_domain = self.c.aliases['alpin:8010']
        self.assertEqual(single_domain, ['zetaweb.com'])

        single_domain = self.c.aliases['underbird:8310']
        self.assertEqual(single_domain, ['tesm.edu'])

    def testList(self):
        self.c.onecmd("add zetaweb.com alpin 8010")
        self.c.onecmd("mk thedwarf.com duder 8020")
        self.c.onecmd("add malcontents.org duder 8020")
        self.c.onecmd("mk christyanity.com duder 8020")
        self.c.onecmd("add tesm.edu underbird 8310")
        self.c.onecmd("add zoobaz.info dummy 80")
        self.c.onecmd("add latebutlaughing.com dummy 80")

        expected = """\
christyanity.com     malcontents.org  thedwarf.com  zoobaz.info
latebutlaughing.com  tesm.edu         zetaweb.com \n"""

        self.c.onecmd("ls")
        self.assertEqual(self.out.getvalue(), expected)

    def testRemove(self):
        self.c.onecmd("add zetaweb.com alpin 8010")
        self.c.onecmd("mk thedwarf.com duder 8020")
        self.c.onecmd("add malcontents.org duder 8020")
        self.c.onecmd("mk christyanity.com duder 8020")
        self.c.onecmd("add tesm.edu underbird 8310")
        self.c.onecmd("add zoobaz.info dummy 80")
        self.c.onecmd("add latebutlaughing.com dummy 80")

        self.c.onecmd("rm zetaweb.com")
        self.assertEqual(len(self.c.domains), 6)
        self.assert_('zetaweb.com' not in self.c.domains)
        domains = []
        for w in self.c.aliases:
            domains += self.c.aliases[w]
        self.assertEqual(len(domains), 6)
        self.assert_('zetaweb.com' not in domains)

        self.c.onecmd("rm thedwarf.com malcontents.org christyanity.com")
        self.assertEqual(len(self.c.domains), 3)
        self.assert_('thedwarf.com' not in self.c.domains)
        self.assert_('malcontents.org' not in self.c.domains)
        self.assert_('christyanity.com' not in self.c.domains)
        domains = []
        for w in self.c.aliases:
            domains += self.c.aliases[w]
        self.assertEqual(len(domains), 3)
        self.assert_('thedwarf.com' not in domains)
        self.assert_('malcontents.org' not in domains)
        self.assert_('christyanity.com' not in domains)

        self.c.onecmd("rm latebutlaughing.com")
        self.assertEqual(len(self.c.domains), 2)
        self.assert_('latebutlaughing.com' not in self.c.domains)
        domains = []
        for w in self.c.aliases:
            domains += self.c.aliases[w]
        self.assertEqual(len(domains), 2)
        self.assert_('latebutlaughing.com' not in domains)

        domains = self.c.domains.keys(); domains.sort()
        self.assertEqual(domains, ['tesm.edu','zoobaz.info'])


    def testNamedConfFrag(self):
        # add three, then remove one, then add two more, then remove all
        #  include subdomains

        ##
        # add three ...
        ##

        self.c.onecmd("add zetaweb.com alpin 8010")
        self.c.onecmd("mk thedwarf.com duder 8020")
        self.c.onecmd("add very.malcontents.org duder 8020")
        self.assertEqual(file(self.c.frag_path).read(),"""\

// begin records generated by porter

zone "very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "www.very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "thedwarf.com" {
        type master;
        file "porter.zone";
};

zone "www.thedwarf.com" {
        type master;
        file "porter.zone";
};

zone "zetaweb.com" {
        type master;
        file "porter.zone";
};

zone "www.zetaweb.com" {
        type master;
        file "porter.zone";
};


// end records generated by porter
"""
        )


        ##
        # ... then remove one ...
        ##

        self.c.onecmd("rm zetaweb.com")
        self.assertEqual(file(self.c.frag_path).read(),"""\

// begin records generated by porter

zone "very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "www.very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "thedwarf.com" {
        type master;
        file "porter.zone";
};

zone "www.thedwarf.com" {
        type master;
        file "porter.zone";
};


// end records generated by porter
"""
        )


        ##
        # ... then add two more ...
        ##

        self.c.onecmd("add malcontents.org duder 8020")
        self.c.onecmd("mk christyanity.com duder 8020")
        self.assertEqual(file(self.c.frag_path).read(),"""\

// begin records generated by porter

zone "christyanity.com" {
        type master;
        file "porter.zone";
};

zone "www.christyanity.com" {
        type master;
        file "porter.zone";
};

zone "malcontents.org" {
        type master;
        file "porter.zone";
};

zone "very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "www.very.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "www.malcontents.org" {
        type master;
        file "porter.zone";
};

zone "thedwarf.com" {
        type master;
        file "porter.zone";
};

zone "www.thedwarf.com" {
        type master;
        file "porter.zone";
};


// end records generated by porter
"""
        )

        ##
        # ... then remove all
        ##

        self.c.onecmd("rm christyanity.com malcontents.org very.malcontents.org")
        self.c.onecmd("rm thedwarf.com")
        self.assertEqual(file(self.c.frag_path).read(),"""\

// begin records generated by porter


// end records generated by porter
"""
        )

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCRUD))
    return suite

if __name__ == '__main__':
    unittest.main()