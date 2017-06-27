#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *
from rmchallenge import RMChallenge 

class RMCategory:
    def __init__(self, bsObject, catBS, browser):
        self.BS = bsObject
        self.browser = browser
        self.challenges = []
        self.challengesList = []
        self.href = None
        self.title = None
        self.description = None
        self.count = None
        
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
                        self.challenges = self.getChallenges()
        # Update our challenges list
        self.challengesList = [chall.title for chall in self.challenges]
        # unset browser for serializing, it is a thread
        self.browser = None
        rmlog(u'RMCategory::init()', u'end of init().', 'debug3')

    def __repr__(self):
        return "<Category ['%s'] (%s challenges)>" % (self.title, self.count)
        
    def __str__(self):
        return "<Category ['%s'] (%s challenges)>" % (self.title, self.count)

    def getChallenges(self):
        rmlog(u'RMCategory::getChallenges()', u'getting URL [%s]' % self.href, 'debug3')
        self.challengesBS = None
        
        # Get the HTML
        challengesHTML = self.browser.getURL('%s/%s' % (self.browser.baseURL, self.href), clean=False)
        if challengesHTML:
            self.challengesBS = self.browser.getBeautifulSoup(challengesHTML)
        else:
            rmlog(u'RMCategory::getChallenges()', u'HTML is [%s]' % challengesHTML, 'debug3')
            
        if self.challengesBS and len(self.challengesBS) >0:  
            # Get the category object from the sub-soup       
            rows = self.challengesBS('tr')
            
            # Skip the first row as it is table headers
            firstRow = True
            # Parse HTML for all TRs
            for chalTR in rows:
                if firstRow:
                    firstRow = False
                else:
                    chalFields = chalTR.findAll('td')
                    # Challenges table has 8 TD
                    if len(chalFields) == 8:
                        # Get the category object from the sub-soup
                        self.challenges.append(RMChallenge(chalFields, self.browser))
        return self.challenges

