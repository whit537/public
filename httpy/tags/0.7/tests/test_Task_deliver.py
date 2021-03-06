#!/usr/bin/env python

import os
import unittest
from StringIO import StringIO

from httpy.Config import Config
from httpy.Request import ZopeRequest
from httpy.Response import Response

from TestCaseHttpy import TestCaseHttpy



DUMMY_APP = """\
class Application:
   def __init__(self, config):
        return config
    def respond(self, request):
        raise "heck"
"""

from utils import DUMMY_TASK


class TestCase(TestCaseHttpy):

    def setUp(self):
        TestCaseHttpy.setUp(self)
        self.task = DUMMY_TASK()
        self.task.server.deploy_mode = True


    # Demonstration
    # =============

    def testBasic(self):
        response = Response(200)
        response.headers['content-type'] = 'text/plain'
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)


    # Response Line
    # =============

    def testBadResponseCode(self):
        response = Response(600)
        self.assertRaises(StandardError, self.task.respond, response)

    def testStatusLineGetsWritten(self):
        response = Response(505)
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 505 HTTP Version not supported'
                   , 'content-length: 23'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Cannot fulfill request.'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testButReasonMessageCanBeOverriden(self):
        response = Response(505)
        response.body = "Just leave me alone, ok!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 505 HTTP Version not supported'
                   , 'content-length: 24'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'Just leave me alone, ok!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)


    # Headers
    # =======

    def testHeadersAreOptional(self):
        response = Response(200)
        response.headers = {} # the default
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 0'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testYouCanAddArbitraryHeaders_TheyWillBeLowerCasedButWillMakeIt(self):
        response = Response(200)
        response.headers['cheese'] = 'yummy'
        response.headers['FOO'] = 'Bar'
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'cheese: yummy'
                   , 'content-length: 19'
                   , 'foo: Bar'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testYouCanOverrideServerAndContentType(self):
        response = Response(200)
        response.headers['server'] = 'MY SERVER! MINE!'
        response.headers['content-type'] = 'cheese/yummy'
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: cheese/yummy'
                   , 'server: MY SERVER! MINE!'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testButYouCantOverrideContentLength(self):
        response = Response(200)
        response.headers['content-length'] = 50000
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testContentTypeDefaultsToApplicationOctetStream(self):
        response = Response(200)
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testExceptForNonSuccessfulRequests_InWhichCaseItIsTextPlain(self):
        response = Response(301)
        response.headers['location'] = 'http://www.google.com/'
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 301 Moved Permanently'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'location: http://www.google.com/'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)




    # body
    # ====

    def testBodyNotWrittenFor304(self):
        response = Response(304)
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 304 Not modified'
                   , 'content-length: 19'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testBodyNotWrittenForHEADRequest(self):
        self.task.request = ZopeRequest()
        self.task.request.received("HEAD / HTTP/1.1\r\n\r\n")

        response = Response(200)
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testBodyIsFormattedFor537(self):
        response = Response(537)
        response.body = ('#'*20,['#'*70])
        self.task.server.deploy_mode = False
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 537 HTTPY App Dev'
                   , 'content-length: 101'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , u"('####################',"
                   , u" ['######################################################################'])"
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testButOnlyForNonStrings(self):
        response = Response(537)
        response.body = 'foo'
        self.task.server.deploy_mode = False
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 537 HTTPY App Dev'
                   , 'content-length: 3'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'foo'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testAndEmptyValuesArePreserved(self):
        response = Response(537)
        response.body = {}
        self.task.server.deploy_mode = False
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 537 HTTPY App Dev'
                   , 'content-length: 2'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , '{}'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testJustLikeFor200(self):
        response = Response(200)
        response.headers['content-type'] = 'text/plain'
        response.body = ''
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 0'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testIncludingNoneForExample(self):
        response = Response(537)
        response.body = None
        self.task.server.deploy_mode = False
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 537 HTTPY App Dev'
                   , 'content-length: 4'
                   , 'content-type: text/plain'
                   , 'server: stub server'
                   , ''
                   , 'None'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)

    def testAnd537NotAvailableInDeploymentMode(self):
        response = Response(537)
        response.body = ('#'*20,['#'*70])
        self.task.server.deploy_mode = True
        self.assertRaises(StandardError, self.task.respond, response)

    def testOtherwiseBodyIsWritten(self):
        response = Response(200)
        response.body = "Greetings, program!"
        self.task.deliver(response)

        expected = [ 'HTTP/1.0 200 OK'
                   , 'content-length: 19'
                   , 'content-type: application/octet-stream'
                   , 'server: stub server'
                   , ''
                   , 'Greetings, program!'
                    ]
        actual = self.task.channel.getvalue().splitlines()
        self.assertEqual(expected, actual)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCase))
    return suite

if __name__ == '__main__':
    unittest.main()
