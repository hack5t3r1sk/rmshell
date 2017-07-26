#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
import browser
from rmcategories import RMCategories
import cPickle, os, traceback

# The virtual browser
class RMBrowser(browser.Browser):
    def __init__(self, queue=None, userAgent=None, cookieFile='rmCookie.lwp', DEBUG=False):
        super(RMBrowser, self).__init__(queue=queue, userAgent=userAgent, cookieFile=cookieFile, DEBUG=DEBUG)

        # ROOT-ME SPECIFIC
        self.baseURL = "https://www.root-me.org"
        self.searchURL = "%s/find" % self.baseURL
        self.loginURL = "%s/?page=login&lang=en&ajax=1" % self.baseURL
        self.accountURL = "%s/prof/user-admin.lml" % self.baseURL
        self.logoutURL = "%s/?action=logout&logout=public&url=https%%3A%%2F%%2Fwww.root-me.org%%3Flang%%3Den" % self.baseURL
        self.hasardURL = "%s/?var_hasard=" % self.baseURL
        self.categoriesURL = "%s/en/Challenges/" % self.baseURL

        # Stores for categories and challenges
        self.categories = None

        # Our BeautifullSoup objects
        self.categoriesBS = None

        # Variables for browser-status
        self.status = "IDLE"
        self.ready = True

        # Used for individual updates
        self.selectedCategory = None

        # User specific
        self.score = 0

    def ipCheck(self):
        currentIP = self.getOutIP()
        if currentIP and currentIP != '' and self.lastOutIP != currentIP:
            rmlog(u'RMBrowser::ipCheck()', u'IP has changed: setting new => [%s]' % currentIP)
            self.lastOutIP = currentIP
            # Not necessary on root-me.org
            #browser.doLogout()
            if currentIP and self.login and self.passwd:
                rmlog(u'RMBrowser::ipCheck()', u'IP has changed: forcing new login')
                self.doLogin()
            else:
                rmlog(u'RMBrowser::ipCheck()', u'IP is %s, no credentials, skipping login check.' % self.lastOutIP, 'warning' )
        else:
            if self.lastOutIP:
                if self.login and self.passwd:
                    rmlog(u'RMBrowser::ipCheck()', u'IP is still the same => [%s], checking if we are logged in...' % self.lastOutIP, 'debug2')
                    if not self.isLoggedIn():
                        rmlog(u'RMBrowser::ipCheck()', u'We are not logged in: forcing new login')
                        self.doLogin()
                else:
                    rmlog(u'RMBrowser::ipCheck()', u'IP is still the same => [%s], no credentials, skipping login check.' % self.lastOutIP, 'debug2')

    def doLogin(self):
        if self.lastOutIP and self.login and self.passwd:
            # Get login page to get a cookie
            # and the login form with token
            self.lastLoginPage = self.getURL(self.loginURL)

            # Set params for login request
            referrer = "%s/" % self.baseURL
            extradata = ""
            loginParams = dict(var_ajax='form',
                               var_login=self.login,
                               password=self.passwd,
                               formulaire_action="login",
                               lang='en')
            rmlog(u'RMBrowser::doLogin()', u'url: %s | referrer: %s' % (self.loginURL, referrer), 'debug2')

            # Get CRSF-Token from login page
            self.getCrsfToken()

            # POST the form
            self.lastLoginPost = self.postURL(self.loginURL, loginParams, referrer, extradata)

            # Check that the login succeeded
            self.isLoggedIn()

            # DEBUG
            # print "RMBrowser::doLogin(): got HTML:"
            # print self.lastLoginPost
            return self.lastLoginPost
        else:
            rmlog(u'RMBrowser::doLogin()', u'I don\'t have sufficient credentials, can\'t log in !', 'error')
        return self.lastLoginPost

    def doLogout(self):
        if self.lastOutIP and self.loggedIn:
            self.lastLogoutPost = self.getURL(self.logoutURL, None, self.lastVisited)
            return self.lastLogoutPost
        else:
            rmlog(u'RMBrowser::doLogin()', u'we are already logged out, nothing to do.', 'debug2')
            return self.lastLogoutPost

    def isLoggedIn(self):
        # Check with the score page and
        # update self.validChallenges
        # at the same time
        checkValidChalls = False
        if self.lastOutIP:
            if self.login and self.login != "":
                checkValidChalls = True
                checkURL = "%s/%s?inc=score&lang=en" % (self.baseURL, self.login)
            else:
                checkURL = self.baseURL
            self.BS = self.getBeautifulSoup(self.getURL(checkURL))
            if self.BS:
                foundAccount = self.BS.find("a",{'href': "./?page=preferences&lang=en" })
                if foundAccount:
                    rmlog(u'RMBrowser::isLoggedIn()', u'LOGGED IN, updating scores...', 'debug')
                    self.loggedIn = True
                    # Update the scores
                    catsUpdated = False

                    # Get user's score
                    children = [child.encode('utf8').strip().replace('\xc2\xa0', ' ') for child in self.BS.find('h1', {'itemprop': 'givenName'}).parent.find('div').find('div').find('ul').find('li').find('span').children]
                    score = int(children[0].split(' ')[0])
                    rmlog(u'RMBrowser::isLoggedIn()', u'LOGGED IN, your current score is [%s]' % score, 'debug')
                    self.score = score

                    # Build a list of valid challenges
                    self.validChalls = [link.attrs['href'] for link in self.BS('a', {'class': 'vert'})]
                    rmlog(u'RMBrowser::isLoggedIn()', u'found %s valid challenges.' % len(self.validChalls), 'debug')

                    # Iterate through all cat->challs and update if different
                    for cat in self.categories.categories:
                        for chall in cat.challenges:
                            if chall.href in self.validChalls:
                                if not chall.valid:
                                    catsUpdated = True
                                    rmlog(u'RMBrowser::isLoggedIn()', "You validated a new challenge: %s" % chall)
                                    chall.valid = True
                                    chall.save()
                    if catsUpdated:
                        self.categories.save()
                else:
                    rmlog(u'RMBrowser::isLoggedIn()', u'NOT LOGGED IN.', 'debug')
                    self.loggedIn = False
        else:
            rmlog(u'RMBrowser::isLoggedIn()', u'lastOutIP is [%s]' % self.lastOutIP, 'debug2')
        return self.loggedIn

    def getCrsfToken(self):
        if self.lastOutIP:
            rmlog(u'RMBrowser::getCrsfToken()', u'getting CRSF-Token.', 'debug')
            login_html = self.getURL(self.loginURL)
            crsfInput = False
            if login_html and len(login_html) >0:
                tmpbs = self.getBeautifulSoup(login_html)
                crsfInput = tmpbs('input', {'name': "formulaire_action_args"})
            if crsfInput and len(crsfInput) >0:
                self.crsfToken = crsfInput[0].attrs['value']
            rmlog(u'RMBrowser::getCrsfToken()', u'CRSF-Token is %s.' % self.crsfToken, 'debug')
            return self.crsfToken
        else:
            rmlog(u'RMBrowser::getCrsfToken()', u'lastOutIP is [%s]' % self.lastOutIP, 'debug2')

    def getCategories(self):
        # Check if we have a saved cfg['challengesStore'] file to load
        if not self.loadCategories():
            rmlog(u'RMBrowser::getCategories()',u'No Database found, starting update !')
            glob.UPDATE = True
        else:
            return self.categories

    def updateCategories(self):
            if self.lastOutIP:
                # Return the lightwieght list, not the big one
                # The indexes should match anyway (len(self.categoriesList) == len(self.categories))
                self.categories = RMCategories(self, self.categoriesURL)
                return self.categories.list
            else:
                rmlog(u'RMBrowser::updateCategories()', u'Cannot update, check your connection and your proxy settings !', 'error')

    def getStorePath(self):
        return '%s/%s/%s/%s' % (glob.initCwd,
                                glob.cfg['challBaseDir'],
                                glob.cfg['challHiddenDir'],
                                glob.cfg['stateStore'])
    def loadCategories(self):
        if os.path.exists(self.getStorePath()):
            rmlog("RMBrowser::getCategories()", "Found saved state, loading...")
            print "    => Found saved state, loading..."

            # Unserialize the object
            with open(self.getStorePath(), 'rb') as stateObj:
                state = cPickle.load(stateObj)

            # Check DB version
            if state and 'version' in state:
                if float(state['version']) == float(glob.rmVersion):
                    if 'categories' in state:
                        self.categories = RMCategories(browser=self, fileDict=state['categories'])
                        self.categories.browser = self
                    if 'lastOutIP' in state:
                        self.lastOutIP = state['lastOutIP']
                    return True
                else:
                    if float(state['version']) < float(glob.rmVersion):
                        rmlog(u'RMBrowser::getCategories()',u'The Database is older than the programm, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
                    else:
                        rmlog(u'RMBrowser::getCategories()',u'The Database is newer than the programm, you should "git pull" and try again.', 'warning')
            else:
                rmlog(u'RMBrowser::getCategories()',u'The Database seems corrupt, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
        else:
            return False

    def saveState(self):
        # Create base dir-structure if it's not there
        absBasePath = '%s/%s' % (glob.initCwd, glob.cfg['challBaseDir'])
        if not os.path.exists(absBasePath):
            rmlog(u'RMBrowser::saveState()',u'Creating challenge\'s dir-struct [%s]...' % absBasePath)
            try:
                os.mkdir(absBasePath)
            except Exception as e:
                rmlog(u'RMBrowser::saveState()',u'Exception while creating [%s]: %s' % (absBasePath, e), 'error')
                return False
        # The hidden dir for the categories
        absHiddenPath = '%s/%s' % (absBasePath, glob.cfg['challHiddenDir'])
        if not os.path.exists(absHiddenPath):
            rmlog(u'RMBrowser::saveState()',u'Creating base hidden-dir [%s]...' % absHiddenPath)
            try:
                os.mkdir(absHiddenPath)
            except Exception as e:
                rmlog(u'RMBrowser::saveState()',u'Exception while creating [%s]: %s' % (absHiddenPath, e), 'error')
                return False

        if os.path.exists(absHiddenPath):
            # unset browser and BS for serializing,
            self.categories.browser = None
            self.categories.BS = None
            # Unset BS & browser in every category / challenge
            for cat in self.categories.categories:
                cat.browser = None
                cat.BS = None
                cat.challengesBS = None
                for chall in cat.challenges:
                    chall.browser = None
                    chall.BS = None
                    chall.statementBS = None
                    chall.summaryBS = None
                    chall.challFields = None

            rmlog(u'RMBrowser::saveState()', u'Saving State to [%s]' % self.getStorePath())

            # First try to save to a temp file
            tmpFile = '%s.tmp.new' % self.getStorePath()
            with open(tmpFile, 'wb') as catsFile:
                try:
                    state = {'version': glob.rmVersion,
                             'lastOutIP': self.lastOutIP,
                             'categories': self.categories.__dict__}
                    cPickle.dump(state, catsFile, 2)
                except Exception as e:
                    rmlog(u'RMBrowser::saveState()', u'Exception while saving State to [%s]: %s' % (self.getStorePath(), e), 'error')
                    rmlog('%s' % traceback.print_exc(), 'debug3')
                    success = False
                else:
                    success = True
            if success:
                if os.path.exists(self.getStorePath()):
                    os.remove(self.getStorePath())
                os.rename(tmpFile, self.getStorePath())
            return success
