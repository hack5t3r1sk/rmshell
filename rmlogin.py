#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

import atexit, os, cPickle, sys, time, traceback, yaml
from rmhelpers import *
from rmbrowser import RMBrowser

def initBrowser(cfg):
    global glob
    global browser
    # Absolute path for the cookieFile
    cookieFilePath = '%s/%s/%s/rmCookie.lwp' % (glob.initCwd,
                                                cfg['challBaseDir'],
                                                cfg['challHiddenDir'])
    # Since there is a loginQueue global variable, pass it to the browser
    browser = RMBrowser(queue=glob.loginQueue,
                        userAgent=cfg['rmUserAgent'],
                        cookieFile=cookieFilePath)

    # Set browser's proxy to our config-proxy
    if cfg['proxyHost'] != "":
        browser.setProxy(cfg['proxyHost'], cfg['proxyPort'])

    # Set the credentials in the browser instance
    browser.setCredentials(cfg['rmuser'], cfg['rmpassword'])

    # Load categories, from file or website
    browser.getCategories()
    return browser

def readConf(cfgFile):
    cfg = None
    # Read YAML conf file
    with open(cfgFile, 'r') as configfile:
        cfg = yaml.load(configfile)
    return cfg

def init():
    glob.cfg = readConf("rmlogin.conf")
    setDebugLevel(glob.cfg['debug'])
    return initBrowser(glob.cfg)

def updateCategories(browser):
    try:
        # Update categories (and all related challenges)
        browser.updateCategories()
    except Exception as e:
        rmlog(u'rmlogin::start()',u'Exception while getting categories [%s]' % e, 'error')
        traceback.print_exc()
        glob.UPDATE = False
        return False
        #pass
    else:
        if browser.categories:
            browser.saveState()
            rmlog(u'rmlogin::start()',u'UPDATE COMPLETED')
            glob.UPDATE = False
            return True
        else:
            glob.UPDATE = False
            return False
            rmlog(u'rmlogin::start()',u'UPDATE FAILED')

def start(browser):
    # This is what this file is about:
    # - keep track of the current public IP seen by rootme
    # - when the exit IP has changed, login into rootme again
    # - when 'u' is pressed in the UI, update the challenges

    # Get home page
    # Uncomment to initialize browser.lastHomePage
    #browser.getHome()

    while True:
        if glob.UPDATE:
            if not browser.lastOutIP:
                 browser.lastOutIP = browser.getOutIP()
            if browser.lastOutIP:
                rmlog(u'rmlogin::start()',u'Update-Mode ON, getting categories...')
                updateCategories(browser)
        elif glob.UPDATECAT:
            if not browser.lastOutIP:
                browser.lastOutIP = browser.getOutIP()
            if browser.lastOutIP:
                rmlog(u'rmlogin::start()',u'Updating selected category...')
                if browser.selectedCategory:
                    browser.selectedCategory.browser = browser
                    browser.selectedCategory.getChallenges()
                    browser.selectedCategory.browser = None
                    browser.saveState()
                    glob.UPDATECAT = False
        else:
            if not updating():
                rmlog(u'rmlogin::start()',u'glob.UPDATE is [%s], doing IP check...' % glob.UPDATE, 'debug')
                try:
                    browser.ipCheck()
                except Exception as e:
                    rmlog(u'rmlogin::start()',u'Exception while doing ipCheck() [%s]' % e, 'debug3')
                    pass
        # Waiting according to conditions
        # This checks if UPDATE or GETCHALL
        # and breaks out right away if True
        if not updating():
            if browser.lastOutIP and browser.crsfToken and browser.loggedIn:
                # Are we still logged in ?
                browser.isLoggedIn()
                rmlog(u'rmlogin::start()',u'Sleeping %ss...' % glob.cfg['checkIpInterval'], 'debug')
                for oneSec in range(1, int(glob.cfg['checkIpInterval'])):
                    if not updating():
                        time.sleep(1)
            elif browser.lastOutIP and not (browser.crsfToken and browser.loggedIn):
                # We are online, but are we logged in ?
                browser.isLoggedIn()
                # Sleep half of interval
                secs = int(int(glob.cfg['checkIpInterval']) / 2)
                rmlog(u'rmlogin::start()',u'Sleeping %ss...' % secs, 'debug3')
                for oneSec in range(1, secs):
                    if not updating():
                        time.sleep(1)
            else:
                rmlog(u'rmlogin::start()',u'Sleeping 5s...', 'debug3')
                time.sleep(5)
        else:
            # We are OFFLINE, 1sec is more than enough
            rmlog(u'rmlogin::start()',u'Update-Mode detected, skipping IPCheckInterval...', 'debug3')
            time.sleep(5)

def initStart():
    global browser
    glob.initCwd = os.getcwd()
    browser = init()
    start(browser)

def rmExit():
    global browser
    # Save state before exiting
    rmlog(u'rmlogin::rmExit()',u'Exit handler called, saving state...', 'debug')
    browser.saveState()

    # Call the standard exit handler
    exit_handler


if __name__ == '__main__':
    browser = None
    glob.loginQueue = None

    # Register our custom exit handler
    atexit.register(rmExit)

    initStart()


"""
# FOR TESTING LISTS IN CURSES
browser.categoriesList = [
    u'App - Script',
    u'App - System',
    u'Cracking',
    u'Cryptanalysis',
    u'Forensic',
    u'Network',
    u'Programming',
    u'Realist',
    u'Steganography',
    u'Web - Client',
    u'Web - Server',
    u'App - Script',
    u'App - System',
    u'Cracking',
    u'Cryptanalysis',
    u'Forensic',
    u'Network',
    u'Programming',
    u'Realist',
    u'Steganography',
    u'Web - Client',
    u'Web - Server'
]

"""
