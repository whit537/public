#!/usr/bin/env python

import os
import unittest
from StringIO import StringIO

from httpy.Config import Config
from httpy.Response import Response
from httpy.Task import Task

from httpyTestCase import httpyTestCase


DUMMY_APP = """\
from httpy.Response import Response
class Transaction:
    def __init__(self, config):
        pass
    def process(self, request):
        raise Response(200)
"""


from TestCaseTask import DUMMY_TASK, StubChannel


class TestTask(httpyTestCase):

    def setUp(self):
        self.task = DUMMY_TASK()
        os.mkdir('root')

        os.environ['HTTPY_VERBOSITY'] = '0'


    # configure
    # =========

    def testConfigure(self):
        config = Config(['-v22','-mdeployment','-rroot'])
        expected = {}
        expected['mode'] = 'deployment'
        expected['verbosity'] = 22
        expected['site_fs_root'] = os.path.realpath('root')
        expected['app_uri_root'] = '/'
        expected['app_fs_root'] = os.path.realpath('root')
        expected['__'] = None
        actual = self.task.configure(config)
        self.assertEqual(expected, actual)


    # fail
    # ====

    def testFailInDevMode(self):
        self.task.dev_mode = True
        self.task.out = StringIO()
        try:
            linenum = 48
            raise Exception("Yarrr!")
        except:
            self.task.fail()

        # Traceback and content length depend on incidental circumstances.
        expected = [ "HTTP/1.0 500 Internal Server Error"
                   # "Content-Length: x"
                   , "Content-Type: text/plain"
                   , ""
                   , "Internal Server Error"
                   , ""
                   , "Traceback (most recent call last):"
                   # ...
                   , 'Exception: Yarrr!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        actual = actual[:1] + actual[2:7] + actual[-1:]
        self.assertEqual(expected, actual)

    def testFailInDepMode(self):
        self.task.dev_mode = False
        self.task.out = StringIO()
        try:
            raise Exception("Yarrr!")
        except:
            self.task.fail()

        expected = [ "HTTP/1.0 500 Internal Server Error"
                   , "Content-Length: 25"
                   , "Content-Type: text/plain"
                   , ""
                   , "Internal Server Error"
                   , ""
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)


    # process
    # =======

    def testProcessAtLeastOnceForCryingOutLoud(self):
        expected = 403 # we don't have a site set up
        try:
            self.task.process()
        except Response, response:
            actual = response.code
        self.assertEqual(expected, actual)

    def testProcessMore(self)
        os.mkdir('root/__')
        file('root/__/app.py','w').write(DUMMY_APP)
        expected = 200
        try:
            import pdb; pdb.set_trace()
            self.task.process()
        except Response, response:
            actual = response.code
        self.assertEqual(expected, actual)



    def tearDown(self):
        os.system('rm -rf root')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTask))
    return suite

if __name__ == '__main__':
    unittest.main()
