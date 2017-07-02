#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import traceback
from rmhelpers import *
import rmlogin

browser = rmlogin.init()
glob.DEBUG = 3
browser.lastOutIP = browser.getOutIP()

if glob.UPDATE:
    if not browser.lastOutIP:
         browser.lastOutIP = browser.getOutIP()
    if browser.lastOutIP:
        rmlog(u'rmlogin::start()',u'Update-Mode ON, getting categories...')
        rmlogin.updateCategories(browser)

# Get all challenges
for cat in browser.categories.get():
    print
    print
    print
    print "####################### CATEGORY: %s" % cat
    for chall in cat.challenges:
        chall.browser = browser
        # Get the challenge
        try:
            chall.getChallenge()
        except Exception as e:
            print "ERROR: unable to get the challenge right now: [%s]" % e
            traceback.print_exc()
            challError = True
        else:
            # Display the challenge's summary
            print
            chall.printStatement()
            print
            print
        print
        print
        print
    print
    print
    print
