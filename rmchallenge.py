#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *

import cPickle, os, re

class RMChallenge:
    def __init__(self, challFields, catTitle, catId, browser):
        rmlog(u'RMChallenge::init()', u'initialising challenge...', 'debug3')
        self.challFields = challFields
        self.browser = browser
        self.BS = None
        self.statementBS = None

        # Infos from the website
        self.href = None
        self.title = None
        self.description = None
        self.points = None
        self.difficulty = None
        self.solutions = None
        self.note = None
        self.validated = None
        self.ssh = None
        self.sshCmd = None
        self.sources = []
        self.dlLinks = []
        self.challIP = None

        # The category we are in
        self.categoryId = catId
        self.categoryTitle = catTitle

        # Generated vars
        self.storePath = None

        if self.challFields:
            validTD   = self.challFields[0]
            linkTD    = self.challFields[1]
            valsTD    = self.challFields[2]
            pointsTD  = self.challFields[3]
            diffTD    = self.challFields[4]
            noteTD    = self.challFields[6]
            soluTD    = self.challFields[7]

            # Is it already validated ? TRUE/FALSE
            self.valid = not (validTD.find('img',{'alt': 'pas_valide'}))

            # Extract challenge link
            tmpATag = linkTD.find('a')
            if tmpATag:
                self.title = tmpATag.string.strip().encode("utf-8")
                self.href = tmpATag.attrs['href'].encode("utf-8")
                self.description = tmpATag.attrs['title'].encode("utf-8")
                rmlog(u'RMChallenge::getChallenge()', u'initialising challenge...', 'debug3')

                # Extract challenge points
                tmpPoints = pointsTD.string
                if tmpPoints and len(tmpPoints) >0:
                    self.points = int(tmpPoints.strip())
                else:
                    self.points = -1

                # Extract difficulty
                if diffTD.find('span', {'class': 'difficulte1a'}):
                    self.difficulty = 1
                elif diffTD.find('span', {'class': 'difficulte2a'}):
                    self.difficulty = 2
                elif diffTD.find('span', {'class': 'difficulte3a'}):
                    self.difficulty = 3
                elif diffTD.find('span', {'class': 'difficulte4a'}):
                    self.difficulty = 4
                elif diffTD.find('span', {'class': 'difficulte36a'}):
                    self.difficulty = 36
                else:
                    self.difficulty = 0

                # Extract challenge solutions
                tmpSolus = soluTD.string
                if tmpSolus and len(tmpSolus) >0:
                    self.solutions = int(tmpSolus.strip())
                else:
                    self.solutions = -1

                # Initialize local variables
                self.path = "%s/%s" % (glob.cfg['challBaseDir'], getChallengePath(self.href))

                # Set the store path before going further
                self.storePath = '%s/%s/%s' % (self.path, glob.cfg['challHiddenDir'], glob.cfg['challStore'])
                rmlog(u'RMChallenge::init()', u'storePath is set to [%s]' % self.storePath, 'debug3')
            else:
                rmlog(u'RMChallenge::getChallenge()', u'couldn\'t find a link for title/href/description, skipping this row !', 'error')
        # unset browser and BS for serializing,
        # browser is a thread and BS is heavy
        self.browser = None
        self.BS = None
        rmlog(u'RMChallenge::init()', u'end init()', 'debug3')

    def __repr__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)

    def __str__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)

    def getChallenge(self, browser=None):
        # Set the store path before going further
        if not self.storePath or self.storePath == "":
            self.storePath = '%s/%s/%s' % (self.path, glob.cfg['challHiddenDir'], glob.cfg['challStore'])
            rmlog(u'RMChallenge::getChallenge()', u'storePath is set to [%s]' % self.storePath, 'debug3')

        # If we already have a store
        if os.path.exists(self.storePath):
            rmlog(u'RMChallenge::getChallenge()', u'loading from store [%s]' % self.storePath, 'debug')
            # Load form store
            self.load()
        else:
            # Get it from root-me.org
            if browser:
                self.browser = browser
            if self.browser and self.browser.lastOutIP:
                rmlog(u'RMChallenge::getChallenge()', u'getting URL [%s]' % self.href, 'debug3')

                # Get the HTML
                challengeHTML = self.browser.getURL('%s/%s' % (self.browser.baseURL, self.href), clean=False)
                if challengeHTML:
                    self.BS = self.browser.getBeautifulSoup(challengeHTML)
                else:
                    rmlog(u'RMChallenge::getChallenge()', u'HTML is [%s]' % challengeHTML, 'warning')
                if self.BS:
                    # Isolate the statement DIV
                    self.extractStatement()

                    # Set properties
                    self.parseStatement()

                    # IF LOGGED-IN, save us to make sure the dirs are created
                    if self.browser.loggedIn:
                        if self.save():
                            # Download the files
                            for link in self.dlLinks:
                                filePath = '%s/%s' % (self.path, link.split('/')[-1])
                                rmlog(u'RMChallenge::getChallenge()', u'downloading [%s] to [%s]' % (link, filePath))
                                self.browser.download(link, filePath)
                else:
                    rmlog(u'RMChallenge::getChallenge()', u'self.BS is [%s]' % self.BS, 'warning')
            else:
                if not self.browser:
                    rmlog(u'RMChallenge::getChallenge()', u'I don\'t have any browser right now !', 'error')
                elif not self.browser.lastOutIP:
                    rmlog(u'RMChallenge::getChallenge()', u'browser.lastOutIP is [%s]' % self.browser.lastOutIP, 'error')

    def extractStatement(self):
        if self.BS:
            # Find the <h4>Statement</h4>'s next DIV
            self.statementBS = self.BS.find('h4', string="Statement")
            if self.statementBS:
                nextSib = self.statementBS.nextSibling
                if nextSib.nextSibling:
                    self.summaryBS = nextSib.nextSibling
                else:
                    self.summaryBS = nextSib
            else:
                rmlog(u'RMChallenge::parseStatement()', u'Couldn\'t find Statement', 'error')
                self.summaryBS = None
        else:
            rmlog(u'RMChallenge::parseStatement()', u'No BS, do getChallenge(browser) first !', 'error')
            return None

    def parseStatement(self):
        if self.summaryBS:
            # Detect source code
            srcDivs = self.summaryBS('pre')
            source = ""
            for src in srcDivs:
                source += "------------------ BEGIN ------------------\n"
                for srcLine in src('li'):
                    source += '%s\n' % srcLine.text.encode('utf8')
                source += "------------------- END -------------------\n"
                self.sources.append(source)

            # Detect download link
            dlLinks = self.summaryBS('p', {'class': 'download'})
            for uri in dlLinks:
                link = '%s/%s' % (self.browser.baseURL, uri.find('a').attrs['href'])
                if not link in self.dlLinks:
                    self.dlLinks.append(link)

            # Grab the SSH infos
            sshLinkTag = self.summaryBS.find('a', {'href': re.compile('ssh://.*\.root-me\.org')})
            if sshLinkTag:
                # Get the actual link
                self.ssh = getSshDict(sshLinkTag.attrs['href'])
        else:
            rmlog(u'RMChallenge::parseStatement()', u'Couldn\'t find Summary', 'error')
            return None

    def getStatement(self):
        return {'sources': self.sources,
                'dlLinks': self.dlLinks,
                'ssh': self.ssh}

    def getSshCmdPass(self, browser=None):
        if browser:
            self.browser = browser
        if self.ssh and self.browser:
            userPort = "-p %s %s@" % (self.ssh['port'], self.ssh['user'])
            if glob.cfg['proxyHost'] != '':
                # We want to insert
                # when proxyHost != ""
                proxyMsg = u'Proxy ON, securely resolving [%s]...' % self.ssh['host']
                rmlog(u'RMChallenge::getSshCmdPass()', proxyMsg, 'debug')
                print proxyMsg
                self.challIP = self.browser.resolveHost(self.ssh['host'])
                rmlog(u'RMChallenge::getSshCmdPass()',
                        u'%s has IP [%s]' % (self.ssh['host'], self.challIP))
                self.sshCmd = [u'ssh', u'-C',
                    u'-o ProxyCommand="nc -x %s:%s -X 5 %%h %%p"' % (glob.cfg['proxyHost'], glob.cfg['proxyPort']),
                    u'-p%s' % self.ssh['port'],
                    u'%s@%s' % (self.ssh['user'],self.challIP)
                ]
                #self.sshCmd = "ssh -C -o ProxyCommand='\"nc -x %s:%s -X 5 %%h %%p\"' " % (glob.cfg['proxyHost'], glob.cfg['proxyPort'])
                #self.sshCmd += "%s%s" % (userPort,self.challIP)
            else:
                self.sshCmd = ['ssh', '-Cp', self.ssh['port'],
                    '%s@%s' % (self.ssh['user'],self.ssh['host'])
                ]
            cmdString = ' '.join(self.sshCmd)
            return (cmdString, self.ssh['password'])
        else:
            if not self.browser:
                rmlog(u'RMChallenge::getSshCmdPass()', u'I don\'t have any browser right now, can\'t resolve !, ', 'error')
            if not self.ssh:
                rmlog(u'RMChallenge::getSshCmdPass()', u'No SSH infos for this challenge !', 'error')
            return (None, None)

    def printStatement(self):
        print "########## CHALLENGE:  %s" % self
        print "### Description: '%s'" % self.description
        if len(self.sources) >0:
            print "### Sources"
            for src in self.sources:
                print src
                print
        if len(self.dlLinks) >0:
            print "### Files to download"
            for link in self.dlLinks:
                print " - %s" % link
            print
        if self.ssh:
            print "### SSH"
            cmd, passwd = self.getSshCmdPass()
            print "Command: [%s]" % cmd
            print "Password: [%s]" % passwd
            print

    def save(self):
        # Create challenge dir-structure if any part of it is not there
        if not os.path.exists(glob.cfg['challBaseDir']):
            rmlog(u'RMChallenge::save()',u'Creating challenge\'s dir-struct [%s]...' % glob.cfg['challBaseDir'])
            try:
                os.mkdir(glob.cfg['challBaseDir'])
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (glob.cfg['challBaseDir'], e), 'error')
                return False
        if not os.path.exists(self.path):
            rmlog(u'RMChallenge::save()',u'Creating challenge\'s dir-struct [%s]...' % self.path)
            try:
                os.mkdir(self.path)
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (self.path, e), 'error')
                return False
        hiddenPath = '%s/%s' % (self.path, glob.cfg['challHiddenDir'])
        if not os.path.exists(hiddenPath):
            try:
                os.mkdir(hiddenPath)
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (hiddenPath, e), 'error')
                return False

        # Should now be there
        # unset browser and BS for serializing,
        # browser is a thread and BS is heavy
        bkpBrowser = self.browser
        bkpBS = self.BS
        self.browser = None
        self.BS = None
        self.challFields = None
        self.summaryBS = None

        # Serialize and dump to file
        if os.path.exists('%s/%s' % (self.path, glob.cfg['challHiddenDir'],)):
            rmlog(u'RMChallenge::save()',u'Saving challenge to [%s]...' % self.storePath)
            with open(self.storePath, 'wb') as stateObj:
                try:
                    state = {'version': glob.rmVersion,
                             'challenge': self.__dict__}
                    cPickle.dump(state, stateObj, 2)
                except:
                    rmlog(u'RMChallenge::save()',u'Exception while saving challenge [%s]: %s' % (self, e), 'error')
                    # Restore the browser and the BS after failing
                    self.browser = bkpBrowser
                    self.BS = bkpBS
                    success = False
                else:
                    success = True

        # Restore the browser and the BS after saving
        self.browser = bkpBrowser
        self.BS = bkpBS
        return success

    def load(self):
        if os.path.exists(self.storePath):
            with open(self.storePath, 'rb') as stateObj:
                try:
                    state = cPickle.load(stateObj)
                except:
                    rmlog(u'RMChallenge::save()',u'Exception while loading challenge [%s] from [%s]: %s' % (self, self.storePath, e), 'error')
                    return False

            # Check DB version
            if state and 'version' in state:
                if float(state['version']) == float(glob.rmVersion):
                    self.__dict__.update(state['challenge'])
                    return self
                else:
                    if float(state['version']) < float(glob.rmVersion):
                        rmlog(u'rmlogin::initBrowser()',u'The Database is older than the programm, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
                        return False
                    else:
                        rmlog(u'rmlogin::initBrowser()',u'The Database is newer than the programm, you should "git pull" and try again.', 'warning')
                        return False
            else:
                return False
                rmlog(u'rmlogin::initBrowser()',u'The Database seems corrupt, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')

