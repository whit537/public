#!/usr/bin/env python

import os
import unittest
from StringIO import StringIO

from httpy.Config import Config
from httpy.Request import ZopeRequest
from httpy.Response import Response



DUMMY_APP = """\
class Transaction:
   def __init__(self, config):
        return config
    def process(self, request):
        raise "heck"
"""

from TestCaseTask import DUMMY_TASK


class TestTaskRespond(unittest.TestCase):

    def setUp(self):
        self.task = DUMMY_TASK()
        self.task.out = StringIO()
        self.task.dev_mode = True
        os.mkdir('root')

        os.environ['HTTPY_VERBOSITY'] = '0'


    # Demonstration
    # =============

    def testBasic(self):
        response = Response(200)
        response.headers['content-type'] = 'text/plain'
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)


    # Response Line
    # =============

    def testBadResponseCode(self):
        response = Response(600)
        self.assertRaises(Exception, self.task.respond, response)

    def testStatusLineGetsWritten(self):
        response = Response(505)
        self.task.respond(response)

        expected = [ 'HTTP/1.0 505 HTTP Version not supported'
                   , 'content-length: 23'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Cannot fulfill request.'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testButReasonMessageCanBeOverriden(self):
        response = Response(505)
        response.body = "Just leave me alone, ok!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 505 HTTP Version not supported'
                   , 'content-length: 24'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Just leave me alone, ok!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)


    # Headers
    # =======

    def testHeadersAreOptional(self):
        response = Response(200)
        response.headers = {} # the default
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 35'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Request fulfilled, document follows'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testYouCanAddArbitraryHeaders_TheyWillBeLowerCasedButWillMakeIt(self):
        response = Response(200)
        response.headers['cheese'] = 'yummy'
        response.headers['FOO'] = 'Bar'
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'cheese: yummy'
                   , 'content-length: 19'
                   , 'foo: Bar'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testYouCanOverrideServerAndContentType(self):
        response = Response(200)
        response.headers['server'] = 'MY SERVER! MINE!'
        response.headers['content-type'] = 'cheese/yummy'
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: cheese/yummy'
                   , 'server: MY SERVER! MINE!'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testButYouCantOverrideContentLength(self):
        response = Response(200)
        response.headers['content-length'] = 50000
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testContentTypeDefaultsToApplicationOctetStream(self):
        response = Response(200)
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testExceptForNonSuccessfulRequests_InWhichCaseItIsTextPlain(self):
        response = Response(301)
        response.headers['location'] = 'http://www.google.com/'
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 301 Moved Permanently'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'location: http://www.google.com/'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)




    # body
    # ====

    def testBodyNotWrittenFor304(self):
        response = Response(304)
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 304 Not modified'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testBodyNotWrittenForHEADRequest(self):
        self.task.request = ZopeRequest()
        self.task.request.received("HEAD / HTTP/1.1\r\n\r\n")

        response = Response(200)
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testOtherwiseBodyIsWritten(self):
        response = Response(200)
        response.body = "Greetings, program!"
        self.task.respond(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.out.getvalue().splitlines()
        self.assertEqual(expected, actual)


    def tearDown(self):
        os.rmdir('root')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTaskRespond))
    return suite

if __name__ == '__main__':
    unittest.main()
