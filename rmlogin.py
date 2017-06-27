#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

import os, pickle, sys, time, yaml
from rmhelpers import *
from rmbrowser import RMBrowser

def initBrowser(cfg):
    # Since there is a loginQueue global variable, pass it to the browser
    browser = RMBrowser(queue=glob.loginQueue)
    
    # Set browser's proxy to our config-proxy
    if cfg['proxyHost'] != "":
        browser.setProxy(cfg['proxyHost'], cfg['proxyPort'])

    # Check if we have a saved cfg['rmChallengesStore'] file to load
    if os.path.exists(glob.cfg['rmChallengesStore']):
        rmlog("rmlogin::initBrowser()", "Found saved state, loading...")
        print "    => Found saved state, loading..."
        # Unserialize the object
        with open(glob.cfg['rmChallengesStore'], 'r') as stateObj:
            state = pickle.load(stateObj)

        # Check DB version
        if state and 'version' in state:
            if float(state['version']) == float(glob.rmVersion):
                browser.categories = state['categories']
            else:
                if float(state['version']) < float(glob.rmVersion):
                    rmlog(u'rmlogin::initBrowser()',u'The Database is older than the programm, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
                else:
                    rmlog(u'rmlogin::initBrowser()',u'The Database is newer than the programm, you should "git pull" and try again.', 'warning')

        else:
            rmlog(u'rmlogin::initBrowser()',u'The Database seems corrupt, you should set UPDATE = True or press "u" if you\'re in the UI.', 'warning')
    else:
        rmlog(u'rmlogin::initBrowser()',u'No Database found, starting update !')
        glob.UPDATE = True
    
    # Set the credentials in the browser instance
    browser.setCredentials(cfg['rmuser'], cfg['rmpassword'])
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
    browser = initBrowser(glob.cfg)
    return browser
    
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
            rmlog(u'rmlogin::start()',u'Update-Mode ON, getting categories...')
            try:
                # Update categories (and all related challenges)
                browser.getCategories()
            except Exception as e:
                rmlog(u'rmlogin::start()',u'Exception while getting categories [%s]' % e, 'error')
                glob.UPDATE = False
                pass
            else:
                with open(glob.cfg['rmChallengesStore'], 'w') as stateObj:
                    state = {'version': glob.rmVersion,
                             'categories': browser.categories}
                    pickle.dump(state, stateObj)
                glob.UPDATE = False
        else:
            rmlog(u'rmlogin::start()',u'glob.UPDATE is [%s], doing IP check...' % glob.UPDATE, 'debug3')
            try:
                ipCheck(browser)
            except Exception as e:
                rmlog(u'rmlogin::start()',u'Exception while doing ipCheck() [%s]' % e, 'debug3')
                pass
        
        # Wait glob.cfg['checkIpInterval']
        if not glob.UPDATE:
            if browser.lastOutIP and browser.crsfToken:
                time.sleep(glob.cfg['checkIpInterval'])
            elif browser.lastOutIP and not browser.crsfToken:
                time.sleep(5)
            else:
                time.sleep(1)
                
        else:
            rmlog(u'rmlogin::start()',u'Update-Mode detected, skipping IPCheckInterval...', 'debug3')
            break


def initStart():
    browser = init()
    start(browser)

if __name__ == '__main__':
    glob.loginQueue = None
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
