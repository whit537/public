if __name__ == '__main__':
    import framework

import unittest, os, pdb
from os.path import join, abspath, isdir
from StringIO import StringIO
from Porter.Porter import Porter

class TestCRUD(unittest.TestCase):

    def setUp(self):
        # ready,...
        self.out = StringIO()
        self.cleanUp()

        # ...set,...
        os.mkdir('var')
        self.porter = Porter(stdout=self.out)
        self.porter._available_websites = self._test_websites

        # ... go!

    def tearDown(self):
        self.cleanUp()

    def cleanUp(self):
        # clean up our filesystem
        for directory in ('var',):
            if isdir(directory):
                test_dir = abspath(directory)
                for datafile in os.listdir(test_dir):
                    os.remove(join(test_dir, datafile))
                os.rmdir(test_dir)

    def _test_websites(self):
        servers  = { 'working'  : (4,'live')
                   , 'no_8000'  : (0,'no 8000')
                   , 'no_ping'  : (0,'no ping')
                   , 'no_fellow': (0,'no fellow')
                    }
        websites = { 'flanderous@working:8010'  : 8010
                   , 'foo@working:8020'         : 8020
                   , 'bar@working:8120'         : 8120
                   , 'baz@working:8440'         : 8440
                     }
        return (servers, websites)


    def testListWhenEmpty(self):
        self.porter.onecmd("ls")
        self.assertEqual(self.out.getvalue(), '')
        self.assertEqual(os.listdir(self.porter.var), ['rewrite.db'])
        # db gets created when we try to read in data, frag file not until we
        #  write

    def testBadInput(self):
        self.porter.onecmd("add test")
        self.assertEqual(self.out.getvalue(), "We need a domain name and " +\
                                              "a website id.\n")
        self.assertEqual(os.listdir(self.porter.var), ['rewrite.db'])
        # didn't write, so still just one file

    def testAddOneItem(self):
        self.porter.onecmd("add zetaweb.com alpin 8010")
        self.porter.onecmd("ls")
        self.assertEqual(self.porter.domains, {'zetaweb.com':'alpin:8010'})
        self.assertEqual(self.porter.aliases, {'alpin:8010':['zetaweb.com']})
        self.assertEqual(self.out.getvalue(), 'zetaweb.com\n')
        self.assertEqual(os.listdir(self.porter.var), ['rewrite.db'
                                                      ,'rewrite.db.old'])
        self.assertEqual(os.listdir(self.porter.var), ['rewrite.db'
                                                      ,'rewrite.db.old'])
        # now we should have both files, plus a backup!
        # to be really thorough we should reload the backup and make sure it works

    def testExtraInputIsIgnored(self):
        self.porter.onecmd("add example.com server:port Frank Sinatra sings the blues")
        self.assertEqual(self.porter.domains, {"example.com":"server:port"})

    def testAddMultipleItems(self):
        self.porter.onecmd("add zetaweb.com alpin 8010")
        self.porter.onecmd("mk  thedwarf.com duder 8020")
        self.porter.onecmd("add malcontents.org duder 8020")
        self.porter.onecmd("mk  christyanity.com duder 8020")
        self.porter.onecmd("add tesm.edu underbird 8310")

        domains = self.porter.domains.keys(); domains.sort()
        self.assertEqual(domains, ['christyanity.com'
                                  ,'malcontents.org'
                                  ,'tesm.edu'
                                  ,'thedwarf.com'
                                  ,'zetaweb.com'
                                   ])

        aliases = self.porter.aliases.keys(); aliases.sort()
        self.assertEqual(aliases, ['alpin:8010'
                                  ,'duder:8020'
                                  ,'underbird:8310'
                                   ])

        multi_domains = self.porter.aliases['duder:8020']
        multi_domains.sort()
        self.assertEqual(multi_domains, ['christyanity.com'
                                        ,'malcontents.org'
                                        ,'thedwarf.com'
                                         ])

        single_domain = self.porter.aliases['alpin:8010']
        self.assertEqual(single_domain, ['zetaweb.com'])

        single_domain = self.porter.aliases['underbird:8310']
        self.assertEqual(single_domain, ['tesm.edu'])

    def testList(self):
        self.porter.onecmd("add zetaweb.com alpin 8010")
        self.porter.onecmd("mk thedwarf.com duder 8020")
        self.porter.onecmd("add malcontents.org duder 8020")
        self.porter.onecmd("mk christyanity.com duder 8020")
        self.porter.onecmd("add tesm.edu underbird 8310")
        self.porter.onecmd("add zoobaz.info dummy 80")
        self.porter.onecmd("add latebutlaughing.com dummy 80")

        expected = """\
christyanity.com     malcontents.org  thedwarf.com  zoobaz.info
latebutlaughing.com  tesm.edu         zetaweb.com \n"""

        self.porter.onecmd("ls")
        self.assertEqual(self.out.getvalue(), expected)

    def testRemove(self):
        self.porter.onecmd("add zetaweb.com alpin 8010")
        self.porter.onecmd("mk thedwarf.com duder 8020")
        self.porter.onecmd("add malcontents.org duder 8020")
        self.porter.onecmd("mk christyanity.com duder 8020")
        self.porter.onecmd("add tesm.edu underbird 8310")
        self.porter.onecmd("add zoobaz.info dummy 80")
        self.porter.onecmd("add latebutlaughing.com dummy 80")

        self.porter.onecmd("rm zetaweb.com")
        self.assertEqual(len(self.porter.domains), 6)
        self.assert_('zetaweb.com' not in self.porter.domains)
        domains = []
        for w in self.porter.aliases:
            domains += self.porter.aliases[w]
        self.assertEqual(len(domains), 6)
        self.assert_('zetaweb.com' not in domains)

        self.porter.onecmd("rm thedwarf.com malcontents.org christyanity.com")
        self.assertEqual(len(self.porter.domains), 3)
        self.assert_('thedwarf.com' not in self.porter.domains)
        self.assert_('malcontents.org' not in self.porter.domains)
        self.assert_('christyanity.com' not in self.porter.domains)
        domains = []
        for w in self.porter.aliases:
            domains += self.porter.aliases[w]
        self.assertEqual(len(domains), 3)
        self.assert_('thedwarf.com' not in domains)
        self.assert_('malcontents.org' not in domains)
        self.assert_('christyanity.com' not in domains)

        self.porter.onecmd("rm latebutlaughing.com")
        self.assertEqual(len(self.porter.domains), 2)
        self.assert_('latebutlaughing.com' not in self.porter.domains)
        domains = []
        for w in self.porter.aliases:
            domains += self.porter.aliases[w]
        self.assertEqual(len(domains), 2)
        self.assert_('latebutlaughing.com' not in domains)

        domains = self.porter.domains.keys(); domains.sort()
        self.assertEqual(domains, ['tesm.edu','zoobaz.info'])

    def testDoubleUpBug(self):
        self.porter.onecmd("add ugandapartners.org bridei 8010")
        self.porter.onecmd("mv ugandapartners.org bridei 8110")
        self.assertEqual(self.porter.aliases['bridei:8010'], [])

        self.porter.onecmd("mv ugandapartners.org bridei 8010")
        self.assertEqual(self.porter.aliases['bridei:8010'], ['ugandapartners.org'])

    def testDoubleUpBugAgain(self):
        self.porter.onecmd("add zetaweb.com bridei 8090")
        self.porter.onecmd("add ugandapartners.org bridei 8090")
        self.assertEqual(self.porter.aliases['bridei:8090'], ['ugandapartners.org','zetaweb.com'])

        self.porter.onecmd("mv zetaweb.com bridei 8080")
        self.assertEqual(self.porter.aliases['bridei:8090'], ['ugandapartners.org'])

        self.porter.onecmd("mv zetaweb.com bridei 8090")
        self.assertEqual(self.porter.aliases['bridei:8090'], ['ugandapartners.org','zetaweb.com'])

        self.porter.onecmd("mv zetaweb.com bridei 8080")
        self.assertEqual(self.porter.aliases['bridei:8090'], ['ugandapartners.org'])

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCRUD))
    return suite

if __name__ == '__main__':
    unittest.main()