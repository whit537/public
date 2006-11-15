import os
import unittest

from aspen.config import Configuration


class TestConfiguration(unittest.TestCase):

    def testDefaults(self):

        address, threads, uid, mode, paths = Configuration([])

        self.assertEqual(address, ('', 8080))
        self.assertEqual(threads, 10)
        self.assertEqual(uid, '')
        self.assertEqual(mode, 'development')
        self.assertEqual(paths.root, os.path.realpath('.'))
        self.assertEqual(paths.__, os.path.join(os.path.realpath('.'), '__'))


    def testOverlapProperly(self):

        # set up environment
        os.environ['HTTPY_MODE'] = 'debugging' # should be retained

        argv = [ '-r','root'                    # should be retained
               , '-f','httpy.conf'               # should be retained
                ]

        # expected
        d = {}
        d['sockfam'] = 2                        # default
        d['address'] = ('', 537)                # file
        d['root'] = os.path.realpath('./root')  # opts
        d['apps'] = [None]                      # default

        e = {}
        e['HTTPY_MODE'] = 'development'         # env
        e['HTTPY_VERBOSITY'] = '99'             # env

        config = Config(argv)

        for k, expected in d.items():
            if k == 'apps':
                continue
            actual = getattr(config, k)
            self.assertEqual(expected, actual)
        self.assertEqual([a.__ for a in config.apps], d['apps'])

        for k, expected in e.items():
            actual = os.environ[k]
            self.assertEqual(expected, actual)
