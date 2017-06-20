#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2, json, os.path, re, time
from threading import Thread
from bs4 import BeautifulSoup, UnicodeDammit
from decimal import Decimal
from rmhelpers import *
import socks
from sockshandler import SocksiPyHandler

COOKIEFILE = 'cookies.lwp'
# the path and filename to save your cookies in

cj = None
ClientCookie = None
cookielib = None

# DEBUGGING IS DONE THROUGH THE GLOBAL DEBUG VARIABLE (helpers.rmlog())
# THE GLOBAL DEBUG VARIABLE SHOULD BE SET IN THE MAIN SCRIPT FROM ENV OR CONF

##### Conditional import:
# Try until we find a lib to handle cookies
# define urlopen accodirngly
#
# Let's see if cookielib is available
try:
    import cookielib
except ImportError:
    # If importing cookielib fails
    # let's try ClientCookie
    try:
        import ClientCookie
    except ImportError:
        # ClientCookie isn't available either
        urlopen = urllib2.urlopen
        Request = urllib2.Request
    else:
        # imported ClientCookie
        urlopen = ClientCookie.urlopen
        Request = ClientCookie.Request
        cj = ClientCookie.LWPCookieJar()
else:
    # importing cookielib worked
    urlopen = urllib2.urlopen
    Request =  urllib2.Request
    cj = cookielib.LWPCookieJar()
    # This is a subclass of FileCookieJar
    # that has useful load and save methods

if cj is not None:
# we successfully imported
# one of the two cookie handling modules
    if os.path.isfile(COOKIEFILE):
        rmlog('RMBrowser::pre-init', 're-using cookie %s' % COOKIEFILE) # TODO: , 'debug')
        # if we have a cookie file already saved
        # then load the cookies into the Cookie Jar
        cj.load(COOKIEFILE,ignore_discard=True)
    else:
        rmlog('RMBrowser::pre-init', 'creating cookie %s' % COOKIEFILE) # TODO: , 'debug')

    # Now we need to get our Cookie Jar
    # installed in the opener;
    # for fetching URLs
    if cookielib is not None:
        # if we use cookielib
        # then we get the HTTPCookieProcessor
        # and install the opener in urllib2
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        rmlog('RMBrowser::pre-init', 'using urllib2') # TODO: , 'debug')
    else:
        # if we use ClientCookie
        # then we get the HTTPCookieProcessor
        # and install the opener in ClientCookie
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
        ClientCookie.install_opener(opener)
        rmlog('RMBrowser::pre-init', 'using ClientCookie' % COOKIEFILE) # TODO: , 'debug')
#
##### End of conditional import
if cj == None:
    rmlog('RMBrowser::pre-init', 'I don\'t have a cookie library available.', 'error')
    rmlog('RMBrowser::pre-init', 'I can\'t show you any cookies.', 'error')
else:
    #if len(cj) >0:
    #    print 'These are the cookies we have received so far :'
    #    for index, cookie in enumerate(cj):
    #        print index, '  :  ', cookie
    cj.save(COOKIEFILE,ignore_discard=True)

# We now have a cookie-compatible urlopen function with our cookie loaded

# The virtual browser
class RMBrowser(Thread):
    def __init__(self, queue=None, userAgent=None, DEBUG=False):
        super(RMBrowser, self).__init__()
        self.DEBUG = DEBUG
        # Variables for browser-status
        self.status = "INIT"
        self.ready = False
        # Our CookieJar
        self.cj = cj
        self.queue = queue
        self.baseURL = "https://www.root-me.org"
        self.searchURL = "%s/find" % self.baseURL
        self.loginURL = "%s/?page=login&lang=en&ajax=1" % self.baseURL
        self.accountURL = "%s/prof/user-admin.lml" % self.baseURL
        self.logoutURL = "%s/?action=logout&logout=public&url=https%%3A%%2F%%2Fwww.root-me.org%%3Flang%%3Den" % self.baseURL
        self.hasardURL = "%s/?var_hasard=" % self.baseURL
        # The anti-CSRF token
        self.crsfToken = ""
        # Used to fill referrer in requests
        self.lastVisited = ""
        # Used to keep trace of responses / IP
        self.lastOutIP = None
        self.lastHeader = None
        self.lastHTML = ""
        self.lastHTMLorig = ""
        self.lastSearch = None
        self.lastSearchHTML= ""
        self.lastLoginPage = ""
        self.lastLoginPost = ""
        self.lastLogoutPost = ""
        self.lastPostHTML = ""
        self.lastError = None
        # Our BeautifullSoup object
        self.bs = None
        # Used to re-write URLs in grabbed HTML
        self.replaceURL = None
        if userAgent:
            self.userAgent = userAgent
        else:
            self.userAgent = u"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_12) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11"
        rmlog(u'RMBrowser::__init__()', u'user-agent: [%s].' % self.userAgent)
        # Variables for browser-status
        self.status = "IDLE"
        self.ready = True

    def buildReq(self, url=None, data=None, referer="", extradata=""):
        rmlog(u'RMBrowser::buildReq()', u'URL: %s' % url, 'debug2')
        if data:
            encoded_data = urllib.urlencode(data)
            encoded_data += extradata
            rmlog(u'RMBrowser::buildReq()', u'encoded data: %s.' % encoded_data.replace(self.login, 'xxxxxxxx').replace(self.passwd, 'xxxxxxxx'), 'debug2')
            req = Request(url, encoded_data)
        else:
            req = Request(url)
        req.add_header('User-agent', self.userAgent)
        self.cj.add_cookie_header(req)
        if referer != "":
            rmlog(u'RMBrowser::buildReq()', u'adding referrer [%s].' % referer, 'debug2')
            req.add_header('Referrer', referer)
        return req

    def setCredentials(self, login=None, password=None):
        if login:
            rmlog(u'RMBrowser::setCredentials()', u'setting login.')
            self.login = login
        if password:
            rmlog(u'RMBrowser::setCredentials()', u'setting password.')
            self.passwd = password

    def setProxy(self,host="127.0.0.1", port=9050):
        rmlog(u'RMBrowser::setProxy()', u'setting proxy [%s:%s].' % (host, port))
        newopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj),SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, host, port))
        urllib2.install_opener(newopener)

    def unsetProxy(self):
        rmlog(u'RMBrowser::unsetProxy()', u'UNSETTING proxy [%s:%s].' % (host, port))
        newopener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(newopener)

    def doreq(self,clean=True):
        try:
            self.response = urlopen(self.req)
        except Exception, e:
            if hasattr(e, 'code'):
                rmlog(u'RMBrowser::doreq()', u'We failed with error code - %s.' % e.code, 'error')
            elif hasattr(e, 'reason'):
                rmlog(u'RMBrowser::doreq()', u'The error object has the following "reason" attribute :', 'error')
                rmlog(e.reason)
                rmlog(u'RMBrowser::doreq()', u'This usually means the server doesn\'t exist, is down, or we don\'t have an internet connection.', 'error')
            self.lastError = e
            return False

        ### Process response, try to get unicode in the end
        try:
            uhtml = UnicodeDammit(self.response.read())
        except Exception, e:
            uhtml = None
            rmlog(u'RMBrowser::doreq()', u'UnicodeDammit failed to convert response.', 'error')
        if hasattr(uhtml, 'unicode_markup') and uhtml.unicode_markup:
            html = uhtml.unicode_markup
        else:
            encoding = self.response.headers['content-type'].split('charset=')[-1]
            if encoding and encoding != "":
                try:
                    html = unicode(self.response.read(), encoding)
                except Exception, e:
                    rmlog(u'RMBrowser::doreq()', u'failed to unicode(response.read(), %s).' % encoding, 'error')
            else:
                rmlog(u'RMBrowser::doreq()', u'could not find source encoding, storing as it is.', 'error')
                html = self.response.read()
        if html:
            self.lastHTMLorig = html
            return html
        else:
            return self.response



    def getURL(self, url=None, data=None, referer="", extraData="", clean=True):
        if not url and self.baseURL and self.baseURL != "":
            url = "%s/" % self.baseURL
        if data:
            getparams = urllib.urlencode(data)
            geturl = "%s?%s" (url,getparams)
        else:
            geturl = url
        self.req = self.buildReq(geturl,None,referer,extraData)
        if self.doreq():
            self.lastVisited = url
            return self.handleReqSuccess("GET", clean)
        else:
            return False

    def postURL(self, url=None, data=None, referrer="", extraData="", clean=True):
        if not url and self.baseURL and self.baseURL != "":
            url = "%s/" % self.baseURL
        data['formulaire_action_args'] = self.crsfToken
        self.req = self.buildReq(url,data, referrer, extraData)
        if self.doreq():
            return self.handleReqSuccess("POST",clean)
        else:
            return False

    def handleReqSuccess(self, reqType="GET", clean=True):
        self.bs = BeautifulSoup(self.lastHTMLorig, "html5lib")
        self.cleanHTML()
        self.cj.extract_cookies(self.response,self.req)
        self.cj.save(COOKIEFILE,ignore_discard=True)
        if reqType == "GET":
            self.lastHTML = self.bs.prettify()
            if clean:
                return self.lastHTML
            else:
                return self.lastHTMLorig
        if reqType == "POST":
            self.lastPostHTML = self.bs.prettify()
            if clean:
                return self.lastPostHTML
            else:
                return self.response

    def cleanHTML(self,html=None):
        if html:
            tmpbs = BeautifulSoup(html, "html5lib")
        else:
            if self.bs:
                tmpbs = self.bs
        if tmpbs:
            # BS("TAG") is the same as BS.find_all("TAG")
            for link in tmpbs('a'):
                try:
                    link['href'] = link['href'].replace("%s" % self.baseURL,"%s" % (self.replaceURL))
                except Exception, e:
                    pass
            for script in tmpbs('script'):
                if hasattr(script,'src'):
                    try:
                        script['src'] = script['src'].replace("%s" % self.baseURL,"%s" % (self.replaceURL))
                    except Exception, KeyError:
                        script.string = ""
                        pass
                else:
                    script.string = ""

            for form in tmpbs('form'):
                try:
                    form['action'] = form['action'].replace("%s" % self.baseURL,"%s" % (self.replaceURL))
                    form['method'] = "GET"
                    form['action'] = "/form"
                except Exception, e:
                    pass
        # Conditionnal return
        if html:
            return tmpbs.prettify()
        else:
            self.bs = tmpbs

    def doLogin(self):
        if not self.loggedIn():
            if self.login != "" and self.passwd != "":
                if not self.bs:
                    # Get login page to get a cookie
                    # and the login form with token
                    self.lastLoginPage = self.getURL(self.loginURL)
                    time.sleep(getRandInRange(3,6))
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
                # print "RMBrowser::doLogin(): got HTML:"
                # print self.lastLoginPost
                return self.lastLoginPost
            else:
                rmlog(u'RMBrowser::doLogin()', u'I don\'t have sufficient credentials, can\'t log in !', 'error')
        else:
            rmlog(u'RMBrowser::doLogin()', u'we are already logged in, nothing to do.', 'debug2')
            return self.lastLoginPost

    def doLogout(self):
        if self.loggedIn():
            self.lastLogoutPost = self.getURL(self.logoutURL, None, self.lastVisited)
            return self.lastLogoutPost
        else:
            rmlog(u'RMBrowser::doLogin(): we are already logged out, nothing to do.', 'debug2')
            return self.lastLogoutPost


    def loggedIn(self):
        if self.bs:
            foundAccount = self.bs.find("a",{'href': "./?page=preferences&lang=en" })
            if foundAccount:
                rmlog(u'RMBrowser::loggedIn()', u'LOGGED IN.')
                return True
            else:
                rmlog(u'RMBrowser::loggedIn()', u'NOT LOGGED IN.')
                return False

    def getOutIP(self):
        rmlog(u'RMBrowser::getOutIP()', u'getting our current public IP.', 'debug3')
        currentIP = self.getURL("http://ipecho.net/plain", clean=False)
        if not currentIP:
            rmlog(u'RMBrowser::getOutIP()', u'Unable to get the current public IP, check your connection and your proxy settings.', 'error')
        return currentIP

    def getHome(self):
        rmlog(u'RMBrowser::getHome()', u'getting home page.', 'debug3')
        return self.getURL(self.baseURL)

    def getCrsfToken(self):
        rmlog(u'RMBrowser::getCrsfToken()', u'getting CRSF-Token.', 'debug3')
        login_html = self.getURL(self.loginURL)
        crsfInput = False
        if login_html and len(login_html) >0:
            tmpbs = BeautifulSoup(login_html, "html5lib")
            crsfInput = tmpbs('input', {'name': "formulaire_action_args"})
        if crsfInput and len(crsfInput) >0:
            self.crsfToken = crsfInput[0].attrs['value']
        rmlog(u'RMBrowser::getCrsfToken()', u'CRSF-Token is %s.' % self.crsfToken, 'debug')
        return self.crsfToken

    def getTitle(self):
        if self.bs:
            return self.bs.title.string

    def getRealPage(self):
        return True


