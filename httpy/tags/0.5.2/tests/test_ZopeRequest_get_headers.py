#!/usr/bin/env python

import os
import unittest

from httpy._zope.server.adjustments import default_adj

from httpy.Request import ZopeRequest

from utils import REQUEST_PARTS


class RequestGetHeadersTests:

    def testExactLine(self):
        self.request.received(self.LINE)
        self.request.received(self.HEADERS)
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request.raw_headers, self.HEADERS.strip())

    def testLineHeadersAtOnce(self):
        self.request.received(self.LINE+self.HEADERS)
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request.raw_headers, self.HEADERS.strip())

    def testPartialHeaders(self):
        self.request.received(self.LINE+self.HEADERS[:30])
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request._tmp, self.HEADERS[:30])
        self.assertEqual(self.request.raw_headers, '')

    def testDividedHeaders(self):
        self.request.received(self.LINE+self.HEADERS[:30])
        self.request.received(self.HEADERS[30:])
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request.raw_headers, self.HEADERS.strip())

    def testExtraStuff(self):
        self.request.received(self.POST)
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request.raw_headers, self.HEADERS.strip())

    def testDividedHeadersAndExtra(self):
        self.request.received(self.LINE+self.HEADERS[:30])
        self.request.received(self.HEADERS[30:]+self.BODY)
        self.assertEqual(self.request.raw_line, self.LINE.strip())
        self.assertEqual(self.request.raw_headers, self.HEADERS.strip())


class TestRequestGetHeadersCRLF(RequestGetHeadersTests,unittest.TestCase):
    def setUp(self):
        self.request = ZopeRequest(default_adj)
        newline='\r\n'
        (self.IE_CRAP,self.LINE,self.LINE2,self.HEADERS,self.HEADERS2,self.BODY,self.POST,self.GET)=REQUEST_PARTS(newline)

class TestRequestGetsHeadersCR(RequestGetHeadersTests,unittest.TestCase):
    def setUp(self):
        self.request = ZopeRequest(default_adj)
        newline='\r'
        (self.IE_CRAP,self.LINE,self.LINE2,self.HEADERS,self.HEADERS2,self.BODY,self.POST,self.GET)=REQUEST_PARTS(newline)

class TestRequestGetsHeadersLF(RequestGetHeadersTests,unittest.TestCase):
    def setUp(self):
        self.request = ZopeRequest(default_adj)
        newline='\n'
        (self.IE_CRAP,self.LINE,self.LINE2,self.HEADERS,self.HEADERS2,self.BODY,self.POST,self.GET)=REQUEST_PARTS(newline)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestRequestGetHeadersCRLF))
    suite.addTest(makeSuite(TestRequestGetsHeadersCR))
    suite.addTest(makeSuite(TestRequestGetsHeadersLF))
    return suite

if __name__ == '__main__':
    unittest.main()
