#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
from rmcategory import RMCategory

import cPickle, os, traceback

class RMCategories:
    def __init__(self, browser=None, categoriesURL=None, fileDict=None):
        self.browser = browser
        self.BS = None
        self.categories = []
        self.list = []
        self.href = categoriesURL
        self.storePath = '%s/%s/%s' % (glob.cfg['challBaseDir'],
                                       glob.cfg['challHiddenDir'],
                                       glob.cfg['stateStore'])
        if not fileDict:
            self.parsePage()
        else:
            self.__dict__.update(fileDict)

    def parsePage(self):
        # Get the HTML
        rmlog(u'RMCategories::init()', u'getting categories.', 'debug3')

        self.BS = self.browser.getBeautifulSoup(self.browser.getURL(self.href, clean=False))

        # DEBUG: counter used for limiting
        # the number of categories to get
        breaker = 0

        if self.BS and len(self.BS) >0:
            # Parse the soup for DIVs with class="tile"
            for catId, catDiv in enumerate(self.BS('div', {'class': "tile"})):
                if breaker >=1:
                    break
                # Get the category object from the sub-soup
                tmpCat = RMCategory(catDiv, self.BS, catId, self.browser)
                if tmpCat.title:
                    self.categories.append(tmpCat)
                    # DEBUG
                    # Uncomment to limit the number of categories
                    #breaker += 1
                    sleep(3)

        # Update our categories list
        self.updateList()

        rmlog(u'RMCategories::init()', u'end of getCategories().', 'debug3')

    def __len__(self):
        return len(self.categories)

    def __getitem__(self, index):
        return self.categories[index]

    def get(self):
        return self.categories

    def updateList(self):
        self.list = ['%s (%s)' % (cat.title, len(cat.challenges)) for cat in self.categories]
        return self.list

    def save(self):
        # Create base dir-structure if it's not there
        absBasePath = '%s/%s' % (glob.initCwd, glob.cfg['challBaseDir'])
        if not os.path.exists(absBasePath):
            rmlog(u'RMCategories::save()',u'Creating challenge\'s dir-struct [%s]...' % absBasePath)
            try:
                os.mkdir(absBasePath)
            except Exception as e:
                rmlog(u'RMCategories::save()',u'Exception while creating [%s]: %s' % (absBasePath, e), 'error')
                return False
        # The hidden dir for the categories
        absHiddenPath = '%s/%s' % (absBasePath, glob.cfg['challHiddenDir'])
        if not os.path.exists(absHiddenPath):
            rmlog(u'RMCategories::save()',u'Creating base hidden-dir [%s]...' % absHiddenPath)
            try:
                os.mkdir(absHiddenPath)
            except Exception as e:
                rmlog(u'RMCategories::save()',u'Exception while creating [%s]: %s' % (absHiddenPath, e), 'error')
                return False

        if os.path.exists(absHiddenPath):
            # unset browser and BS for serializing,
            # browser is a thread and BS is heavy
            lastOutIP = self.browser.lastOutIP
            bkpBrowser = self.browser
            bkpBS = self.BS
            self.browser = ""
            self.BS = ""
            # Unset BS & browser in every category / challenge
            for cat in self.categories:
                cat.browser = ""
                cat.BS = ""
                cat.challengesBS = ""
                for chall in cat.challenges:
                    chall.browser = ""
                    chall.BS = ""
            absPath = '%s/%s' % (absHiddenPath, glob.cfg['stateStore'])
            rmlog(u'RMCategories::start()',u'Saving RMCategories object to [%s]' % absPath)
            # First try to save to a temp file
            tmpFile = '%s.tmp.new' % absPath
            # DEBUG
            #print self.__dict__
            print bkpBrowser.lastOutIP
            with open(tmpFile, 'wb') as catsFile:
                try:
                    state = {'version': glob.rmVersion,
                             'lastOutIP': lastOutIP,
                             'categories': self.__dict__}
                    cPickle.dump(state, catsFile, 2)
                except Exception as e:
                    rmlog(u'RMCategories::save()',u'Exception while saving categories to [%s]: %s' % (self.storePath, e), 'error')
                    rmlog('%s' % traceback.print_exc(), 'debug3')
                    success = False
                else:
                    success = True
            if success:
                if os.path.exists(absPath):
                    os.remove(absPath)
                os.rename(tmpFile, absPath)
            # restore browser and BS
            self.browser = bkpBrowser
            self.BS = bkpBS
            return success
