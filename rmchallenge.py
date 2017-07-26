#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *

import cPickle, os, re

class RMChallenge:
    def __init__(self, challFields=None, catTitle=None, catId=None, browser=None, challObj=None):
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
        self.docLinks = []
        self.tcpLinks = []
        self.challIP = None

        # The category we are in
        self.categoryId = catId
        self.categoryTitle = catTitle

        # Generated vars
        self.storePath = None

        # Holds the response when we post a flag
        self.validationHTML = None

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
            if validTD.find('img',{'alt': 'valide'}):
                self.valid = True

            # Extract challenge link
            tmpATag = linkTD.find('a')
            if tmpATag:
                self.title = tmpATag.string.strip().encode("utf-8")
                self.href = tmpATag.attrs['href'].encode("utf-8")
                self.description = tmpATag.attrs['title'].encode("utf-8")

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
                self.path = "%s" % getChallengePath(self.href)

                # Set the store path before going further
                self.storePath = '%s/%s/%s/%s' % (glob.cfg['challBaseDir'],
                                                  self.path,
                                                  glob.cfg['challHiddenDir'],
                                                  glob.cfg['challStore'])
                rmlog(u'RMChallenge::init()', u'storePath is set to [%s]' % self.storePath, 'debug3')
            else:
                rmlog(u'RMChallenge::getChallenge()', u'couldn\'t find a link for title/href/description, skipping this row !', 'error')
        elif challObj:
            rmlog(u'RMChallenge::init()', u'challObj passed, we\'re updating', 'debug3')
            ####### Copy all parent-parsed properties
            # Keep the old paths
            self.path = challObj.path
            self.storePath = challObj.storePath
            # Keep old solutions
            self.solutions = challObj.solutions
            # Keep old valid
            self.valid = challObj.valid
            # Keep old points
            self.points = challObj.points
            # Keep old title
            self.title = challObj.title
            # Keep old difficulty
            self.difficulty = challObj.difficulty
            # Keep old description
            self.description = challObj.description
            # Keep old href
            self.href = challObj.href
            # Keep old categoryId
            self.categoryId = challObj.categoryId
        rmlog(u'RMChallenge::init()', u'end init()', 'debug3')

    def __repr__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)

    def __str__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)

    def getPath(self):
        return '%s/%s/%s' % (glob.initCwd,
                             glob.cfg['challBaseDir'],
                             self.path)

    def getHiddenPath(self):
        return '%s/%s' % (self.getPath(), glob.cfg['challHiddenDir'])

    def getStorePath(self):
        return '%s/%s' % (self.getHiddenPath(), glob.cfg['challStore'])

    def getPage(self):
        if self.browser and self.browser.lastOutIP:
            rmlog(u'RMChallenge::getChallenge()', u'getting URL [%s]' % self.href, 'debug3')

            # Get the HTML
            challengeHTML = self.browser.getURL('%s/%s' % (self.browser.baseURL, self.href), clean=False)
            if challengeHTML:
                self.BS = self.browser.getBeautifulSoup(challengeHTML)
            else:
                rmlog(u'RMChallenge::getChallenge()', u'HTML is [%s]' % challengeHTML, 'warning')
        else:
            if not self.browser:
                rmlog(u'RMChallenge::getChallenge()', u'I don\'t have any browser right now !', 'error')
            elif not self.browser.lastOutIP:
                rmlog(u'RMChallenge::getChallenge()', u'browser.lastOutIP is [%s]' % self.browser.lastOutIP, 'error')

    def getChallenge(self, browser=None, valid=False):
        if browser:
            self.browser = browser

        # If we already have a store
        if os.path.exists(self.getStorePath()):
            rmlog(u'RMChallenge::getChallenge()', u'loading from store [%s]' % self.getStorePath(), 'debug')
            # Load form store
            self.load()
        else:
            glob.GETCHALL = True
            # Get it from root-me.org
            self.getPage()
            if self.BS:
                # Isolate the statement DIV
                self.extractStatement()

                # Set properties
                self.parseStatement()

                # Reset flag
                glob.GETCHALL = False

                # IF LOGGED-IN, save us to make sure the dirs are created
                # TODO: be sure it's all working when not logged in
                #if self.browser.loggedIn:
                if self.save():
                    ### Download the files
                    # First the files in statement
                    for link in self.dlLinks:
                        filePath = '%s/%s' % (self.getPath(), link.split('/')[-1])
                        rmlog('RMChallenge::getChallenge()', 'downloading [%s] to [%s]' % (link, filePath))
                        self.browser.download(link, filePath)

                    # Then the docs
                    # TODO: make it a config-defined value
                    docPath = '%s/doc' % self.getPath()
                    if not os.path.exists(docPath):
                        try:
                            os.mkdir(docPath)
                        except Exception as e:
                            rmlog('RMChallenge::save()','Exception while creating [%s]: %s' % (self.getHiddenPath(), e), 'error')
                            return False
                    if os.path.exists(docPath):
                        for link in self.docLinks:
                            filePath = '%s/%s' % (docPath, link.split('/')[-1])
                            rmlog('RMChallenge::getChallenge()', 'downloading [%s] to [%s]' % (link, filePath))
                            self.browser.download(link, filePath)
            else:
                # Reset flag
                glob.GETCHALL = False
                rmlog(u'RMChallenge::getChallenge()', u'self.BS is [%s]' % self.BS, 'warning')

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
            tmpSources = []
            for src in srcDivs:
                source = ""
                source += "------------------ BEGIN ------------------\n"
                for srcLine in src('li'):
                    source += '%s\n' % srcLine.text.encode('utf8')
                source += "------------------- END -------------------\n"
                tmpSources.append(source)
            self.sources = tmpSources

            # Detect download links
            dlLinks = self.summaryBS('p', {'class': 'download'})
            tmpDlLinks = []
            tmpTcpLinks = []
            for uri in dlLinks:
                if  uri.find('a').attrs['href'][0:6] not in ("ssh://", "tcp://"):
                    link = '%s/%s' % (self.browser.baseURL, uri.find('a').attrs['href'].encode("utf-8"))
                    if not link in self.dlLinks:
                        tmpDlLinks.append(link)
                elif  uri.find('a').attrs['href'][0:6] == "tcp://":
                    link = uri.find('a').attrs['href'].encode("utf-8")
                    if not link in self.tcpLinks:
                        tmpTcpLinks.append(link)
            self.dlLinks = tmpDlLinks
            self.tcpLinks = tmpTcpLinks

            # What is the href of the Start button ?
            startBtn = self.BS.find('a', string=re.compile(".*Start the challenge.*"))
            if startBtn:
                if startBtn.attrs['href'][0:6] not in ("ssh://", "tcp://"):
                    # This doesn't look like an SSH challenge, try downloading
                    self.dlLinks.append(startBtn.attrs['href'].encode("utf-8"))

            # Grab the SSH infos
            sshLinkTag = self.summaryBS.find('a', {'href': re.compile('ssh://.*\.root-me\.org')})
            if sshLinkTag:
                # Get the actual link
                self.ssh = getSshDict(sshLinkTag.attrs['href'].encode("utf-8"))

            # Grab the docs:
            # class="crayon challenge-ressources-CHALLID "
            docDiv = self.BS.find('div', {'class': re.compile("challenge-ressources-.*")})
            for link in docDiv.findAll('a'):
                rmlog(u'RMChallenge::parseStatement()', u'Found docLink', 'debug3')
                # DEBUG
                #print link
                if 'href' in link.attrs:
                    href = link.attrs['href'].encode("utf-8")
                    # FIXME:
                    # 'ascii' codec can't encode character u'\xe8' in position 49: ordinal not in range(128)
                    #rmlog(u'RMChallenge::parseStatement()', u'link is [%s]' % href.decode(), 'debug3')
                    if not href in self.docLinks:
                        fileName = href.split('/')[-1]
                        rmlog(u'RMChallenge::parseStatement()', u'Filename is [%s]' % fileName, 'debug3')
                        if fileName.split('.')[-1] in ("pdf", "txt", "doc", "docx"):
                            self.docLinks.append(href)
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
            print "### Files to download:"
            for link in self.dlLinks:
                print " - %s" % link
            print
        if len(self.docLinks) >0:
            print "### Documentations to download:"
            for link in self.docLinks:
                print " - %s" % link
            print
        if self.ssh:
            print "### SSH"
            cmd, passwd = self.getSshCmdPass()
            print "Command: [%s]" % cmd
            print "Password: [%s]" % passwd
            print

    def getFlagPath(self):
        return '%s/%s/%s' % (glob.initCwd, self.path, glob.cfg['flagFile'])

    def postFlag(self):
        # THE POST DATA
        #   var_ajax=form
        #   formulaire_action=validation_challenge
        #   formulaire_action_args=Uey+XOSaOfFe5PilP9kB1g3NFyocTKPfG+1KzFNXkSbjlU3VWWZL9Mgaxb3qBsA5qBzt6CD3zAgljASkVU3eLTBBOaoeqVp86Yg=
        #   _jeton=2c22f67a98d14e447993e3a79a8e25fbb34f267f
        #   passe=user
        #   email_nobot
        # THE POST REPONSE CONTAINS <div class="ts success"> IF SUCCESSFUL
        # Refresh BS the for form's hidden fields
        if os.path.exists(self.getFlagPath()) and self.browser and self.browser.loggedIn:
            self.getPage()
            validChall = self.BS.find('input', {'value': 'validation_challenge'})
            formArgs = validChall.nextSibling.attrs['value']
            challToken = validChall.nextSibling.nextSibling.attrs['value']
            formData = dict(var_ajax='form',
                            var_login=self.login,
                            password=self.passwd,
                            formulaire_action="validation_challenge",
                            formulaire_action_args=formArgs,
                            _jeton=challToken,
                            passe=user,
                            email_nobot='',
                            lang='en')
            # Post the flag
            self.validationHTML = self.postURL(self.href, loginParams, referrer)


    def save(self):
        ### Create challenge dir-structure if any part of it is not there
        # The base dir for all challenges
        absBasePath = '%s/%s' % (glob.initCwd, glob.cfg['challBaseDir'])
        if not os.path.exists(absBasePath):
            rmlog(u'RMChallenge::save()',u'Creating challenge\'s dir-struct [%s]...' % absBasePath)
            try:
                os.mkdir(absBasePath)
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (absBasePath, e), 'error')
                return False

        # The dir for this challenge
        if not os.path.exists(self.getPath()):
            rmlog(u'RMChallenge::save()',u'Creating challenge\'s dir-struct [%s]...' % self.getPath())
            try:
                os.mkdir(self.getPath())
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (self.getPath(), e), 'error')
                return False

        # The hidden dir for this challenge
        if not os.path.exists(self.getHiddenPath()):
            try:
                os.mkdir(self.getHiddenPath())
            except Exception as e:
                rmlog(u'RMChallenge::save()',u'Exception while creating [%s]: %s' % (self.getHiddenPath(), e), 'error')
                return False

        # The dir-structure should now be there
        # unset browser and BS for serializing,
        # browser is a thread and BS is heavy
        bkpBrowser = self.browser
        bkpBS = self.BS
        self.browser = None
        self.BS = None
        self.challFields = None
        self.summaryBS = None

        # Serialize and dump to file
        if os.path.exists('%s' % (self.getHiddenPath())):
            rmlog(u'RMChallenge::save()',u'Saving challenge to [%s]...' % self.getStorePath())
            # First try to save to a temp file
            tmpFile = '%s.tmp.new' % self.getStorePath()
            with open(tmpFile, 'wb') as stateFile:
                try:
                    state = {'version': glob.rmVersion,
                             'challenge': self.__dict__}
                    cPickle.dump(state, stateFile, 2)
                except:
                    rmlog(u'RMChallenge::save()',u'Exception while saving challenge [%s]: %s' % (self, e), 'error')
                    # Restore the browser and the BS after failing
                    self.browser = bkpBrowser
                    self.BS = bkpBS
                    success = False
                else:
                    success = True
            if success:
                # Remove the old file and rename the tepm to absPath
                if os.path.exists(self.getStorePath()):
                    os.remove(self.getStorePath())
                os.rename(tmpFile, self.getStorePath())

        # Restore the browser and the BS after saving
        self.browser = bkpBrowser
        self.BS = bkpBS
        return success

    def load(self):
        if os.path.exists(self.getStorePath()):
            with open(self.getStorePath(), 'rb') as stateObj:
                try:
                    state = cPickle.load(stateObj)
                except:
                    rmlog(u'RMChallenge::save()',u'Exception while loading challenge [%s] from [%s]: %s' % (self, self.getStorePath(), e), 'error')
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

