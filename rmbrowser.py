#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
import browser
from rmcategories import RMCategories

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

    def doLogin(self):
		if self.login != "" and self.passwd != "":
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
			
			# DEBUG
			# print "RMBrowser::doLogin(): got HTML:"
			# print self.lastLoginPost
			return self.lastLoginPost
		else:
			rmlog(u'RMBrowser::doLogin()', u'I don\'t have sufficient credentials, can\'t log in !', 'error')
		return self.lastLoginPost

    def doLogout(self):
        if self.loggedIn():
            self.lastLogoutPost = self.getURL(self.logoutURL, None, self.lastVisited)
            return self.lastLogoutPost
        else:
            rmlog(u'RMBrowser::doLogin(): we are already logged out, nothing to do.', 'debug2')
            return self.lastLogoutPost

    def loggedIn(self):
        self.getHome()
        if self.bs:
            foundAccount = self.bs.find("a",{'href': "./?page=preferences&lang=en" })
            if foundAccount:
                rmlog(u'RMBrowser::loggedIn()', u'LOGGED IN.', 'debug')
                return True
            else:
                rmlog(u'RMBrowser::loggedIn()', u'NOT LOGGED IN.', 'debug')
                return False

    def getCrsfToken(self):
        rmlog(u'RMBrowser::getCrsfToken()', u'getting CRSF-Token.', 'debug3')
        login_html = self.getURL(self.loginURL)
        crsfInput = False
        if login_html and len(login_html) >0:
            tmpbs = self.getBeautifulSoup(login_html)
            crsfInput = tmpbs('input', {'name': "formulaire_action_args"})
        if crsfInput and len(crsfInput) >0:
            self.crsfToken = crsfInput[0].attrs['value']
        rmlog(u'RMBrowser::getCrsfToken()', u'CRSF-Token is %s.' % self.crsfToken, 'debug')
        return self.crsfToken

    def getCategories(self):
        # Return the lightwieght list, not the big one
        # The indexes should match anyway (len(self.categoriesList) == len(self.categories))
        self.categories = RMCategories(self, self.categoriesURL)
        return self.categories.list
