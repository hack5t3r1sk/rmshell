#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
from rmchallenge import RMChallenge

import re

class RMCategory:
    def __init__(self, bsObject, catBS, catId, browser):
        self.BS = bsObject
        self.browser = browser
        self.id = catId
        self.challenges = []
        self.challengesList = []
        self.href = None
        self.title = None
        self.description = None
        self.count = None
        self.challengesBS = None

        # Support for pagination
        self.pages = []

        # Parse the soup
        # Does it have a link ?
        tmpLink = self.BS('a')
        if tmpLink and len(tmpLink) >0:
            # DEBUG
            #print tmpLink
            #print dir(tmpLink)

            # Yes, it has a link
            # Does it have a challenge count span ?
            self.href = tmpLink[0].attrs['href']
            tmpCount = self.BS('span')
            if tmpCount and len(tmpCount) >0:
                # Yes it has
                # Does it have a B inside
                tmpCountInt = tmpCount[0].find('b')
                if tmpCountInt and len(tmpCountInt) >0:
                    # Find the link in the menu
                    navDiv = catBS.find('div', {'role': 'navigation'})
                    if navDiv and len(navDiv) >0:
                        # This category exists in the menu
                        menuLink = navDiv('ul',
                                    {'class': 'dropdown'})[1].find('a',
                                    {'href': self.href})
                        if menuLink:
                            tmpDesc = menuLink.attrs['title']
                            catTitle = menuLink.string.strip()
                        else:
                            tmpDesc = 'Not found in menu...'
                            catTitle = 'Is this a category ?'
                        challengesCount = int(tmpCountInt.string.strip())

                        # This really looks like a valid challenge category
                        self.title = catTitle.encode("utf-8")
                        self.count = challengesCount
                        self.description = tmpDesc.encode("utf-8")
                        self.href = self.href.encode("utf-8")
                        # Get the challenges in this categroy
                        rmlog(u'RMCategory::init()', u'getting challenges for %s' % self, 'debug')

                        # We grabbed everything we could, get challenges list
                        self.getChallenges()

        # unset browser and BS for serializing,
        # browser is a thread and BS is heavy
        self.browser = None
        self.BS = None
        self.challengesBS = None
        # TODO: empty self.challenges,
        # only keep a list with paths

        rmlog(u'RMCategory::init()', u'end of init().', 'debug3')

    def __repr__(self):
        return "<Category ['%s'] (%s challenges)>" % (self.title, self.count)

    def __str__(self):
        return "<Category ['%s'] (%s challenges)>" % (self.title, self.count)

    def getChallenges(self):
        challURL = '%s/%s' % (self.browser.baseURL, self.href)
        rmlog(u'RMCategory::getChallenges()', u'getting URL [%s]' % challURL, 'debug3')
        if self.getPage(challURL):
            self.challenges = []
            # Store AJAX-ENV for pagination requests
            self.ajaxEnv = self.challengesBS.findAll('div', {'class': 'ajaxbloc'})[2].attrs['data-ajax-env']

            # Isolate the challenges DIV
            challDiv = self.getChallDiv()

            # Check for pagination
            self.getPages(challDiv)

            # Parse the first page
            self.parsePage()

            if len(self.pages) > 0:
                # Repeat for each page
                for page in self.pages:
                    rmlog(u'RMCategory::getChallenges()', u'getting next page with ajax...', 'debug')
                    tmpURL = page.split('?')
                    ajaxURL = '%s/%s?var_ajax=1&var_ajax_env=%s&var_ajax_ancre=pagination_co&%s' % (
                                    self.browser.baseURL, tmpURL[0],
                                    self.browser.urlQuote(self.ajaxEnv), tmpURL[1])
                    if self.getPage(ajaxURL):
                        # Isolate the challenges DIV
                        #challDiv = self.getChallDiv()
                        # Parse the new page
                        self.parsePage()


            rmlog(u'RMCategory::getChallenges()', u'added %s challenges' % len(self.challenges), 'debug')
            self.challengesList = [chall.title for chall in self.challenges]
            return self.challenges
        return False

    def parsePage(self):
        # Get the category object from the sub-soup
        rows = self.challengesBS('tr')

        # Skip the first row as it is table headers
        firstRow = True
        breaker = 0

        # Parse HTML for all TRs
        for chalTR in rows:
            if firstRow:
                firstRow = False
            else:
                # DEBUG
                # Uncomment to limit the number of categories
                #breaker += 1
                if breaker >2:
                    break
                chalFields = chalTR.findAll('td')
                # Challenges table has 8 TD
                if len(chalFields) == 8:
                    # Get the category object from the TD fields
                    self.challenges.append(RMChallenge(chalFields, self.title, self.id, self.browser))

    def getChallDiv(self):
        challTitle = self.challengesBS.findAll('h1')[1]
        if challTitle:
            return challTitle.parent
        else:
            return None

    def getPages(self, challDiv):
        for pageItem in challDiv('li'):
            if 'class' in pageItem.attrs:
                rmlog('RMCategory::getPages()', u'Skipping current page', 'debug2')
            else:
                pageLink = pageItem.find('a', {'class': 'lien_pagination'})
                if pageLink:
                    self.pages.append(pageLink.attrs['href'])

    def getPage(self, page):
        html = self.browser.getURL(page, clean=False)
        if html:
            # Request succeded
            BS = self.browser.getBeautifulSoup(html)
            if BS and len(BS) >0:
                self.challengesBS = BS
                return True
            else:
                return False
        else:
            rmlog(u'RMCategory::getChallenges()', u'HTML is [%s]' % html, 'error')
            return False
