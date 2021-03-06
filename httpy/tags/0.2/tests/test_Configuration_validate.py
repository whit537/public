#!/usr/bin/env python

import os
import unittest

from ConfigurationTestCase import ConfigurationTestCase
from httpy.Configuration import ConfigError

class TestConfigurationValidate(ConfigurationTestCase):

    # Basic functions
    # ===============

    def testEmptyDictReturned(self):
        expected = {}
        actual = self.config._validate('test', {})
        self.assertEqual(expected, actual)

    def testSuperfluousKeysRemoved(self):
        d = {'ip':'', 'foo':'bar'}
        expected = {'ip':''}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)


    # ip
    # ==

    def testGoodIP(self):
        d = {'ip':'192.168.1.1'}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testIPOutOfRange(self):
        d = {'ip':'256.68.1.1'}
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test'
                         , d
                          )

    def testFalseIPCoercedToEmptyString(self):
        d = {'ip':''}
        expected = {'ip':''}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':None}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':[]}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':tuple()}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':{}}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':False}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'ip':0}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)


    def testNonFalseIPOfWrongTypeRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test'
                         , {'ip':192.16811}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test'
                         , {'ip':('192','168','1','1')}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test'
                         , {'ip':{'192':'168','1':'1'}}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test'
                         , {'ip':['192','168','1','1']}
                          )

    def testIPErrorMessage(self):
        d = {'ip':'256.68.1.1'}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad IP '256.68.1.1' in context 'test'. IP " +\
                       "must be empty or a valid IPv4 address."
            actual = err.msg
            self.assertEqual(expected, actual)


    # port
    # ====

    def testGoodPort(self):
        d = {'port':8080}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testOutOfRangeRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':100000}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':65536}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':-1}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':-8080}
                          )

    def testButInRangeIsFine(self):
        d = {'port':0}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'port':1}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'port':80}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

        d = {'port':65535}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testDigitStringIsCoerced(self):
        d = {'port':'8080'}
        expected = {'port':8080}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testNonIntableRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':False} # considered non-intable here
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':[]}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':['foo']}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'port':None}
                          )

    def testPortErrorMessage(self):
        d = {'port':None}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad port 'None' in context 'test'. Port " +\
                       "must be an integer between 0 and 65535."
            actual = err.msg
            self.assertEqual(expected, actual)


    # root
    # ====

    def testGoodRoot(self):
        d = {'root':'.'}
        expected = {'root':os.path.realpath('.')}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testNonDirectoryRootRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'root':'./runalltests.py'}
                          )

    def testNonExistantRootAlsoRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'root':'./not-there'}
                          )

    def testRootErrorMessage(self):
        d = {'root':None}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad root 'None' in context 'test'. Root " +\
                       "must point to a directory."
            actual = err.msg
            self.assertEqual(expected, actual)


    # defaults
    # ========

    def testGoodDefaults(self):
        d = {'defaults':('index.html', 'index.pt')}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testStringCoercedToTuple(self):
        d = {'defaults':'index.html index.pt'}
        expected = {'defaults':('index.html', 'index.pt')}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testFilenameWithPathSepsRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'defaults':'/etc/master.passwd'}
                          )

    def testDefaultsErrorMessage(self):
        d = {'defaults':None}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad defaults 'None' in context 'test'. " +\
                       "Defaults must be a whitespace- or comma-separated " +\
                       "list of filenames."
            actual = err.msg
            self.assertEqual(expected, actual)


    # extensions
    # ==========

    def testGoodExtensions(self):
        d = {'extensions':('pt',)}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testStringCoercedToTuple(self):
        d = {'extensions':'html pt'}
        expected = {'extensions':('html', 'pt')}
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testNonAlphanumExtensionsRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'extensions':'$pt'}
                          )

    def testExtensionsErrorMessage(self):
        d = {'extensions':None}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad defaults 'None' in context 'test'. " +\
                       "Extensions must be a whitespace- or comma-" +\
                       "separated list of alphanumeric filename extensions."
            actual = err.msg
            self.assertEqual(expected, actual)


    # mode
    # ====

    def testGoodMode(self):
        d = {'mode':'deployment'}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testOtherMode(self):
        d = {'mode':'development'}
        expected = d.copy()
        actual = self.config._validate('test', d)
        self.assertEqual(expected, actual)

    def testAnythingElseRaisesError(self):
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':'$pt'}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':0}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':'developmen'}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':'-*- Python -*-'}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':False}
                          )
        self.assertRaises( ConfigError
                         , self.config._validate
                         , 'test', {'mode':0755}
                          )

    def testModeErrorMessage(self):
        d = {'mode':None}
        try:
            self.config._validate('test', d)
        except ConfigError, err:
            expected = "Found bad mode 'None' in context 'test'. " +\
                       "Mode must be either `deployment' or `development'."
            actual = err.msg
            self.assertEqual(expected, actual)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestConfigurationValidate))
    return suite

if __name__ == '__main__':
    unittest.main()
