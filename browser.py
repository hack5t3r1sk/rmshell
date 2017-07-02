#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

import json, os.path, re, time, urllib, urllib2
from threading import Thread
from bs4 import BeautifulSoup, UnicodeDammit
from rmhelpers import *
import socks
from sockshandler import SocksiPyHandler

ClientCookie = None
cookielib = None

class Browser(Thread):
    """A base browser to be subclassed by more interesting implementations..."""
    def __init__(self, queue=None, userAgent=None, cookieFile='cookies.lwp', DEBUG=False):
        global Request
        global cookielib
        global ClientCookie
        global urlopen
        super(Browser, self).__init__()
        self.DEBUG = DEBUG

        self.opener = None

        # Variables used for the import
        # Our CookieJar
        self.cj = None
        self.cookieFile = cookieFile


        self.checkIpURL = "http://ipecho.net/plain"
        self.baseURL = "https://www.startpage.com"
        self.searchURL = "%s/do/search" % self.baseURL
        self.resolveURL = "http://www.ip-tracker.org/resolve/domain-to-ip.php?ip="

        # The anti-CSRF token
        # This should be used by the getCrsfToken() method
        self.crsfToken = ""

        # Used to fill referrer in requests
        self.lastVisited = ""

        # Used to keep trace of responses / IP
        self.lastOutIP = None
        self.lastHeader = None
        self.lastHTML = None
        self.lastHTMLorig = None
        self.lastPostHTML = None
        self.lastError = None

        # Search related
        self.lastSearch = None
        self.lastSearchHTML= ""

        # Login related
        self.lastHomePage = None
        self.lastLoginPage = None
        self.lastLoginPost = None
        self.lastLogoutPost = None

        # Our BeautifullSoup object
        self.BS = None

        # Our loggin queue
        self.queue = queue

        # Used to re-write URLs in grabbed HTML
        self.replaceURL = None
        self.dnsCache = {}

        # Set User-Agent
        if userAgent:
            self.userAgent = userAgent
        else:
            self.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_12) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.65 Safari/535.11"
        rmlog(u'Browser::init()', u'user-agent: [%s].' % self.userAgent, 'debug')

        # Credentials
        self.login = None
        self.password = None
        self.loggedIn = False

        # Variables for browser-status
        self.status = "INIT"
        self.ready = False

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
                self.cj = ClientCookie.LWPCookieJar()
        else:
            # importing cookielib worked
            urlopen = urllib2.urlopen
            Request =  urllib2.Request
            self.cj = cookielib.LWPCookieJar()
            # This is a subclass of FileCookieJar
            # that has useful load and save methods

        if self.cj is not None:
        # we successfully imported
        # one of the two cookie handling modules
            if os.path.isfile(self.cookieFile):
                rmlog('Browser::init()', 're-using cookie %s' % self.cookieFile, 'debug2')
                # if we have a cookie file already saved
                # then load the cookies into the Cookie Jar
                self.cj.load(self.cookieFile,ignore_discard=True)
            else:
                rmlog('Browser::init()', 'creating cookie %s' % self.cookieFile, 'debug2')

            # Now we need to get our Cookie Jar
            # installed in the opener;
            # for fetching URLs
            if cookielib is not None:
                # if we use cookielib
                # then we get the HTTPCookieProcessor
                # and install the opener in urllib2
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
                urllib2.install_opener(opener)
                rmlog('Browser::init()', 'using urllib2', 'debug2')
            else:
                # if we use ClientCookie
                # then we get the HTTPCookieProcessor
                # and install the opener in ClientCookie
                opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(self.cj))
                ClientCookie.install_opener(opener)
                rmlog('Browser::init()', 'using ClientCookie' % self.cookieFile, 'debug2')
        #
        ##### End of conditional import
        if self.cj == None:
            rmlog('Browser::init()', 'I don\'t have a cookie library available.', 'error')
            rmlog('Browser::init()', 'I can\'t show you any cookies.', 'error')
        else:
            #if len(self.cj) >0:
            #    print 'These are the cookies we have received so far :'
            #    for index, cookie in enumerate(self.cj):
            #        print index, '  :  ', cookie
            self.cj.save(self.cookieFile,ignore_discard=True)

        # We now have a cookie-compatible urlopen function with our cookie loaded


    def buildReq(self, url=None, data=None, referer="", extradata=""):
        rmlog(u'Browser::buildReq()', u'URL: %s' % url, 'debug3')
        if data:
            encoded_data = urllib.urlencode(data)
            encoded_data += extradata
            rmlog(u'Browser::buildReq()', u'encoded data: %s.' % encoded_data.replace(self.login, 'xxxxxxxx').replace(self.passwd, 'xxxxxxxx'), 'debug2')
            req = Request(url, encoded_data)
        else:
            req = Request(url)
        req.add_header('User-agent', self.userAgent)
        self.cj.add_cookie_header(req)
        if referer != "":
            rmlog(u'Browser::buildReq()', u'adding referrer [%s].' % referer, 'debug2')
            req.add_header('Referrer', referer)
        return req

    def setCredentials(self, login=None, password=None):
        if login and login != '':
            rmlog(u'Browser::setCredentials()', u'setting login.')
            self.login = login
        if password and password != '':
            rmlog(u'Browser::setCredentials()', u'setting password.')
            self.passwd = password

    def setProxy(self,host="127.0.0.1", port=9050):
        rmlog(u'Browser::setProxy()', u'setting proxy [%s:%s].' % (host, port))
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj), SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, host, port))
        urllib2.install_opener(self.opener)

    def unsetProxy(self):
        rmlog(u'Browser::unsetProxy()', u'UNSETTING proxy.')
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(self.opener)

    def doreq(self,clean=True):
        try:
            self.response = urlopen(self.req)
        except Exception, e:
            if hasattr(e, 'code'):
                rmlog(u'Browser::doreq()', u'We failed with error code - %s.' % e.code, 'error')
            if hasattr(e, 'reason'):
                rmlog(u'Browser::doreq()', u'The error object has the following reason: [%s]' % e.reason, 'error')
                rmlog(u'Browser::doreq()', u'This usually means the server doesn\'t exist, is down, or we don\'t have an internet connection.', 'error')
            self.lastError = e
            return False
        html = None
        ### Process response, try to get unicode in the end
        try:
            respData = self.response.read()
        except Exception, e:
            rmlog(u'Browser::doreq()', u'Exception while reading response data: [%s]' % e, 'error')
            return False
        else:
            try:
                uhtml = UnicodeDammit(respData)
            except Exception, e:
                uhtml = None
                rmlog(u'Browser::doreq()', u'UnicodeDammit failed to convert response.', 'error')
                return False
            if hasattr(uhtml, 'unicode_markup') and uhtml.unicode_markup:
                html = uhtml.unicode_markup
            else:
                encoding = self.response.headers['content-type'].split('charset=')[-1]
                if encoding and encoding != "":
                    try:
                        html = unicode(self.response.read(), encoding)
                    except Exception, e:
                        rmlog(u'Browser::doreq()', u'failed to unicode(response.read(), %s).' % encoding, 'error')
                        return False
                else:
                    rmlog(u'Browser::doreq()', u'could not find source encoding, storing as it is.', 'error')
                    html = self.response.read()
            if html:
                self.lastHTMLorig = html
                return html
            else:
                return False

    def getURL(self, url=None, data=None, referer="", extraData="", clean=True):
        if not url and self.baseURL and self.baseURL != "":
            url = "%s/" % self.baseURL
        if data:
            getparams = urllib.urlencode(data)
            geturl = "%s?%s" (url,getparams)
        else:
            geturl = url
        self.req = self.buildReq(geturl,None,referer,extraData)
        for i in range(1, 3):
            if i >1:
                rmlog(u'Browser::getURL()', u'Request seems to have failed, retrying...', 'warning')
                sleep(3)
            if self.doreq():
                self.lastVisited = url
                result = self.handleReqSuccess("GET", clean)
                if result:
                    return result
        # We tried 3 times, give up
        return False

    def postURL(self, url=None, data=None, referrer="", extraData="", clean=True):
        if not url and self.baseURL and self.baseURL != "":
            url = "%s/" % self.baseURL
        #if not data:
        #    data = {}
        data['formulaire_action_args'] = self.crsfToken
        self.req = self.buildReq(url,data, referrer, extraData)
        # Here we don't want to retry the posts as we're
        # not sure if the data was posted or not
        if self.doreq():
            return self.handleReqSuccess("POST",clean)
        else:
            return False

    def handleReqSuccess(self, reqType="GET", clean=True):
        self.BS = BeautifulSoup(self.lastHTMLorig, "html5lib")
        self.cleanHTML()
        self.cj.extract_cookies(self.response,self.req)
        self.cj.save(self.cookieFile,ignore_discard=True)
        if reqType == "GET":
            self.lastHTML = self.BS
            if clean:
                return self.lastHTML.prettify()
            else:
                return self.lastHTMLorig
        if reqType == "POST":
            self.lastPostHTML = self.BS
            if clean:
                return self.lastPostHTML.prettify()
            else:
                return self.response

    def cleanHTML(self,html=None):
        if html:
            tmpbs = self.getBeautifulSoup(html)
        else:
            if self.BS:
                tmpbs = self.BS
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
            self.BS = tmpbs

    def getOutIP(self):
        rmlog(u'Browser::getOutIP()', u'getting our current public IP.', 'debug3')
        # Maybe TODO: try catch else
        currentIP = self.getURL(self.checkIpURL , clean=False)
        if not currentIP:
            rmlog(u'Browser::getOutIP()', u'Unable to get the current public IP, check your connection and your proxy settings.', 'error')
        return currentIP

    def resolveHost(self, hostname, port=80):
        if not hostname in self.dnsCache:
            # http://www.ip-tracker.org/resolve/domain-to-ip.php?ip=root-me.org
            resolveBS = self.getBeautifulSoup(self.getURL(
                        '%s%s' % (self.resolveURL, hostname), clean=False))
            if resolveBS:
                ipHead = resolveBS.find('th', string='IP Address:')
                ipAddr = ipHead.nextSibling.nextSibling
                if ipAddr:
                    self.dnsCache[hostname] = ipAddr.string.strip().encode('utf8')
                else:
                    return None
            else:
                return None
        return self.dnsCache[hostname]

    def urlEncode(self, utfUrl):
        return urllib.urlencode(utfUrl)

    def urlQuote(self, utfStr):
        return urllib.quote(utfStr)

    def download(self, srcUrl, dstPath):
        chunkSize = 16 * 1024
        try:
            response = urlopen(srcUrl)
            with open(dstPath, 'wb') as f:
                while True:
                    chunk = response.read(chunkSize)
                    if not chunk:
                        break
                    f.write(chunk)
        except Exception as e:
            rmlog(u'Browser::download()', u'Exception while downloading [%s] to [%s]: %s' % (srcUrl, dstPath, e), 'error')
            return False
        else:
            rmlog(u'Browser::download()', u'Successfully downloaded [%s] to [%s]' % (srcUrl, dstPath), 'debug')
            return True

    def getBeautifulSoup(self, html):
        BS = None
        if html:
            try:
                BS = BeautifulSoup(html, "html5lib")
            except Exception as e:
                rmlog(u'Browser::getBeautifulSoup()', u'BeautifulSoup could not parse the given HTML.', 'error')
        else:
            rmlog(u'Browser::getBeautifulSoup()', u'HTML is [%s], not trying to parse.' % html, 'error')
        return BS

    def getHome(self):
        rmlog(u'Browser::getHome()', u'getting home page.', 'debug3')
        self.lastHomePage = self.getURL(self.baseURL, clean=False)
        return self.lastHomePage

    def getTitle(self):
        if self.BS:
            return self.BS.title.string.encode('utf8').strip().replace("  "," ").replace("\n"," ")

    # TODO: fake a real browser by downloading all assets/images/...
    # but maybe this is not a good idea...
    def getRealPage(self):
        return True

    ################# METHODS TO OVERRIDE IF FUNCTIONALITY IS NEEDED
    # This should be adapted for each specific website
    # The default method just looks for a 'Logout' link
    def isLoggedIn(self):
        rmlog(u'Browser::isLoggedIn()', u'You should override this function if you need it', 'error')
        return False

    def doLogin(self):
        rmlog(u'Browser::doLogin()', u'You should override this function if you need it', 'error')
        return False

    def doLogout(self):
        rmlog(u'Browser::doLogout()', u'You should override this function if you need it', 'error')
        return False
