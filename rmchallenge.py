#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
from rmhelpers import *

class RMChallenge:
    def __init__(self, chalFields, browser):
        self.chalFields = chalFields
        self.browser = browser
        self.href = None
        self.title = None
        self.description = None
        self.points = None
        self.difficulty = None
        self.solutions = None
        self.note = None
        self.validated = None
        self.sshLink = None
        
        if self.chalFields:
                validTD   = self.chalFields[0]
                linkTD    = self.chalFields[1]
                valsTD    = self.chalFields[2]
                pointsTD  = self.chalFields[3]
                diffTD    = self.chalFields[4]
                noteTD    = self.chalFields[6]
                soluTD    = self.chalFields[7]

                # Is it already validated ? TRUE/FALSE
                self.valid = not (validTD.find('img',{'alt': 'pas_valide'}))

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
        # unset browser for serializing, it is a thread
        self.browser = None

    def __repr__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)

    def __str__(self):
        return "[%spts] [%s] %s" % (self.points, rmDiff(self.difficulty), self.title)
