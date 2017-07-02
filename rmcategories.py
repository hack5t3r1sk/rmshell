#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
from rmcategory import RMCategory

import cPickle, os

class RMCategories:
    def __init__(self, browser, categoriesURL):
        self.browser = browser
        self.BS = None
        self.categories = []
        self.list = []
        self.href = categoriesURL
        self.storePath = '%s/%s/%s' % (glob.cfg['challBaseDir'],
                                       glob.cfg['challHiddenDir'],
                                       glob.cfg['challengesStore'])

        # DEBUG: counter used for limiting
        # the number of categories to get
        breaker = 0

        # Get the HTML
        rmlog(u'RMCategories::init()', u'getting categories.', 'debug3')

        self.BS = self.browser.getBeautifulSoup(self.browser.getURL(self.href, clean=False))

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
        baseDir = glob.cfg['challBaseDir']
        if not os.path.exists(baseDir):
            rmlog(u'RMCategories::save()',u'Creating base directory [%s]...' % baseDir)
            try:
                os.mkdir(baseDir)
            except Exception as e:
                rmlog(u'RMCategories::save()',u'Exception while creating base directory [%s]: %s' % (baseDir, e), 'error')
                return False

        hiddenDir = '%s/%s' % (glob.cfg['challBaseDir'], glob.cfg['challHiddenDir'])
        if not os.path.exists(hiddenDir):
            rmlog(u'RMCategories::save()',u'Creating base hidden-dir [%s]...' % hiddenDir)
            try:
                os.mkdir(hiddenDir)
            except Exception as e:
                rmlog(u'RMCategories::save()',u'Exception while creating hidden directory [%s]: %s' % (hiddenDir, e), 'error')
                return False

        if os.path.exists(hiddenDir):
            # unset browser and BS for serializing,
            # browser is a thread and BS is heavy
            bkpBrowser = self.browser
            bkpBS = self.BS
            self.browser = None
            self.BS = None
            rmlog(u'RMCategories::start()',u'Saving RMCategories object to [%s]' % self.storePath)
            with open(self.storePath, 'wb') as stateObj:
                try:
                    state = {'version': glob.rmVersion,
                             'categories': self}
                    cPickle.dump(state, stateObj, 2)
                except Exception as e:
                    rmlog(u'RMCategories::save()',u'Exception while saving categories to [%s]: %s' % (self.storePath, e), 'error')
                    success = False
                else:
                    success = True
            # restore browser and BS
            self.browser = bkpBrowser
            self.BS = bkpBS
            return success

    def load(self):
        if os.path.exists(self.storePath):
            with open(self.storePath, 'rb') as stateObj:
                try:
                    state = cPickle.load(stateObj)
                except:
                    rmlog(u'RMChallenge::save()',u'Exception while loading categories from [%s]: %s' % (self.storePath, e), 'error')
                    return False

            # Check DB version
            if state and 'version' in state:
                if float(state['version']) == float(glob.rmVersion):
                    self.__dict__.update(state['categories'])
                    return self
                else:
                    if float(state['version']) < float(glob.rmVersion):
                        rmlog(u'RMCategories::load()',u'The Database is older than the programm, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
                        return False
                    else:
                        rmlog(u'RMCategories::load()',u'The Database is newer than the programm, you should "git pull" and try again.', 'warning')
                        return False
            else:
                rmlog(u'RMCategories::load()',u'The Database seems corrupt, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
                return False
