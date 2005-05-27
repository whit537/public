# make sure we can find ourselves
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Zope/Plone
from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

# us
from Products.FCKeditor.tests import dict2tuple as d2t
from Products.FCKeditor.PloneFCKmanager import PloneFCKmanager


##
# Tweak the test fixture
##

ZopeTestCase.installProduct('FCKeditor')


##
# Define our tests
##

class Test(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        self.portal.portal_quickinstaller.installProduct('FCKeditor')
        self.fckm = self.portal.portal_fckmanager

        self.portal.acl_users._doAddUser('admin', 'secret', ['Manager'], [])
        self.portal.acl_users._doAddUser('user', 'secret', ['Member'], [])

        self.login('admin')
        self.portal.invokeFactory('Folder', 'Docs')
        self.logout()

    def testCurrentFolderDoesntExist(self):
        Type = ''
        CurrentFolder = '/Nonexistant/'
        NewFolderName = 'Foo'

        expected = {'error_code': 110}
        actual = self.fckm.CreateFolder(Type, CurrentFolder, NewFolderName)
        self.assertEqual(d2t(expected), d2t(actual))

        # but only KeyErrors are caught
        CurrentFolder = []
        self.assertRaises( TypeError, self.fckm.CreateFolder, Type
                         , CurrentFolder, NewFolderName
                          )

    # the rest assume the folder exists


    def testUserDoesntHavePermission(self):
        Type = ''
        CurrentFolder = '/'
        NewFolderName = 'Foo'

        expected = {'error_code': 103}
        self.login('user')
        actual = self.fckm.CreateFolder(Type, CurrentFolder, NewFolderName)
        self.logout()
        self.assertEqual(d2t(expected), d2t(actual))

    def testUserDoesHavePermission(self):
        Type = ''
        CurrentFolder = '/'
        NewFolderName = 'Foo'

        expected = {'error_code': 0}
        self.login('admin')
        actual = self.fckm.CreateFolder(Type, CurrentFolder, NewFolderName)
        self.logout()
        self.assertEqual(d2t(expected), d2t(actual))

    # the rest assume the user has permission on the folder in question


    def testNameCollision(self):
        Type = ''
        CurrentFolder = '/'
        NewFolderName = 'Docs'

        expected = {'error_code': 101}
        self.login('admin')
        actual = self.fckm.CreateFolder(Type, CurrentFolder, NewFolderName)
        self.logout()
        self.assertEqual(d2t(expected), d2t(actual))

    def testPloneCheckId(self):
        Type = ''
        CurrentFolder = '/'
        NewFolderName = ''

        def createFolder(NewFolderName):
            self.login('admin')
            return self.fckm.CreateFolder(Type, CurrentFolder, NewFolderName)
            self.logout()

        # in 2.0.5 check_id catches bad Zope id's (among other things)
        expected = {'error_code': 102}
        actual = createFolder('!!!!foofoofoof!!!!!')
        self.assertEqual(d2t(expected), d2t(actual))

        # but it does not enforce name collisions induced by portal_skins,
        # which means we can override check_id, e.g.
        expected = {'error_code': 0}
        actual = createFolder('check_id')
        self.assertEqual(d2t(expected), d2t(actual))

        # then next time we add something we will get strange behavior
        self.assertRaises(TypeError, createFolder, 'IShouldWork')

        # (clean up our mess)
        self.portal.manage_delObjects('check_id')

        # (now it should work again)
        expected = {'error_code': 0}
        actual = createFolder('IShouldWork')
        self.assertEqual(d2t(expected), d2t(actual))

        # edge errors get caught by our catch-all
        expected = {'error_code': 110}
        actual = createFolder([])
        self.assertEqual(d2t(expected), d2t(actual))





##
# Assemble into a suite and run
##

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(Test))
    return suite

if __name__ == '__main__':
    framework()