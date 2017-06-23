#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

import os, pickle, sys, time, yaml
from rmhelpers import *
from rmbrowser import RMBrowser

# This is global in this script only, those who import us
# will access rmlogin.browser, the others have no access
global browser

# Since there is a loginQueue global variable, pass it to the browser
browser = RMBrowser(queue=glob.loginQueue)

def initBrowser(cfg):
    # Set browser's proxy to our config-proxy
    if cfg['proxyHost'] != "":
        browser.setProxy(cfg['proxyHost'], cfg['proxyPort'])

    # Check if we have a saved cfg['rmChallengesStore'] file to load
    if os.path.exists(glob.cfg['rmChallengesStore']):
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

        # Update our categories list
        browser.categoriesList = [cat['title'] for cat in browser.categories if 'title' in cat]
    else:
        rmlog(u'rmlogin::initBrowser()',u'No Database found, starting update !')
        glob.UPDATE = True
    # Set the credentials in the browser instance
    browser.setCredentials(cfg['rmuser'], cfg['rmpassword'])

def readConf(cfgFile):
    cfg = None
    # Read YAML conf file
    with open(cfgFile, 'r') as configfile:
        cfg = yaml.load(configfile)
    return cfg

def init():
    glob.cfg = readConf("rmlogin.conf")
    setDebugLevel(glob.cfg['debug'])
    initBrowser(glob.cfg)

def start():
    # This is what this file is about:
    # - keep track of the current public IP seen by rootme
    # - when the exit IP has changed, login into rootme again
    # - when 'u' is pressed in the UI, update the challenges
    while True:
        if glob.UPDATE:
            rmlog(u'rmlogin::start()',u'Update-Mode ON, getting categories...')
            try:
                # Update categories (and all related challenges)
                browser.getCategories()

                glob.UPDATE = False
                with open(glob.cfg['rmChallengesStore'], 'w') as stateObj:
                    state = {'version': glob.rmVersion,
                             'categories': browser.categories}
                    pickle.dump(state, stateObj)

            except:
                rmlog(u'rmlogin::start()',u'Exception while getting categories !', 'error')
                glob.UPDATE = False
                pass
        else:
            rmlog(u'rmlogin::start()',u'glob.UPDATE is [%s], doing IP check...' % glob.UPDATE, 'debug3')
            try:
                ipCheck(browser)
            except:
                pass
        # Controlled sleep
        for s in range(1,glob.cfg['checkIpInterval']):
            if not glob.UPDATE:
                time.sleep(1)
            else:
                rmlog(u'rmlogin::start()',u'Update-Mode detected, skipping IPCheckInterval...', 'debug3')
                break


def initStart():
    init()
    start()

if __name__ == '__main__':
    loginQueue = None
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
