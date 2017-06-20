#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Log level
# - False => only ERROR
# - 0     => WARNING, ERROR
# - 1     => INFO, WARNING, ERROR
LOGLEVEL = 1

# Debug level
# - False => no debugging
# - 0     => debug
# - 1     => debug, debug1
# - 2     => debug, debug1, debug2
# - 3     => debug, debug1, debug2, debug3
DEBUG = 3

import Queue, sys, time, yaml
from rmhelpers import *
from rmbrowser import RMBrowser


# Instanciate global objects
mainQ = Queue.Queue(maxsize=0)
browser = RMBrowser(queue=mainQ, DEBUG=False)


if __name__ == '__main__':
    # Read YAML conf file
    with open("rmlogin.conf", 'r') as configfile:
        cfg = yaml.load(configfile)

    setLogLevel(LOGLEVEL)
    setDebugLevel(DEBUG)

    # Set browser's proxy to our config-proxy
    if cfg['proxyHost'] != "":
        browser.setProxy(cfg['proxyHost'], cfg['proxyPort'])

    # Set the credentials in the browser instance
    browser.setCredentials(cfg['rmuser'], cfg['rmpassword'])

    # Not needed actually: Set the initial IP address
    #ipCheck(browser)

    # This is what this file is about:
    # - keep track of the current public IP seen by rootme
    # - when the exit IP has changed, login into rootme again
    while True:
        ipCheck(browser)
        time.sleep(cfg['checkIpInterval'])

