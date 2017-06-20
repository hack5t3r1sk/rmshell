#!/usr/bin/env python
# -*- coding: utf-8 -*-

################## SHOULD BE SET IN THE MAIN SCRIPT
# Log level
# - False => INFO, ERROR
# - 1     => INFO, WARNING, ERROR
#LOGLEVEL = 1

# Debug level
# - False => no debugging
# - 0     => debug
# - 1     => debug, debug1
# - 2     => debug, debug1, debug2
# - 3     => debug, debug1, debug2, debug3
#DEBUG = 3
################## END: SHOULD BE SET IN THE MAIN SCRIPT
global DEBUG

import datetime as dt, sys, random
import atexit, signal

def setLogLevel(level):
    global LOGLEVEL
    LOGLEVEL = level

def setDebugLevel(level):
    global DEBUG
    DEBUG = level

# Intercepts sys.exit(0)
def exit_handler():
    rmlog(u'rmhelpers::exit_handler()', u'Application ending.')

# Intercepts any signal
def signal_handler(signalId, frame):
    print
    if signalId == signal.SIGTERM:
        rmlog(u'rmhelpers::signal_handler()', u'Received SIGTERM: exiting.')
    if signalId == signal.SIGINT:
        rmlog(u'rmhelpers::signal_handler()', u'Keyboard Interrupt (SIGINT): exiting.')
    sys.exit(0)

def ipCheck(browser):
    currentIP =  browser.getOutIP()
    if currentIP and currentIP != '' and browser.lastOutIP != currentIP:
        browser.lastOutIP = currentIP
        rmlog(u'rmhelpers::ipCheck()', u'IP has changed: setting new => [%s]' % browser.lastOutIP)
        #browser.doLogout()
        browser.doLogin()
        browser.loggedIn()
    else:
        rmlog(u'rmhelpers::ipCheck()', u'IP is still the same => [%s]' % browser.lastOutIP, 'debug3')

def rmlog(funcName, msg,level="info"):
    global DEBUG
    global LOGLEVEL
    tstamp = getNow('sql')
    if level == 'info':
        sys.stdout.write("%s::[INFO]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    elif level == 'warning':
        sys.stdout.write("%s::[WARNING]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    elif level == 'debug':
        if DEBUG and DEBUG >= 1:
            sys.stdout.write("%s::[debug]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    elif level == 'debug2':
        if DEBUG and DEBUG >= 2:
            sys.stdout.write("%s::[debug2]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    elif level == 'debug3':
        if DEBUG and DEBUG >= 3:
            sys.stdout.write("%s::[debug3]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    else:
        sys.stderr.write("%s::[ERROR]:%s: %s\n" % (tstamp, funcName, msg.encode('utf-8')))
    sys.stdout.flush()

def getNow(format="epoch"):
    now = dt.datetime.now()
    if format == "epoch":
        return int(now.strftime("%s"))
    elif format == "sql":
        return now.strftime('%Y-%m-%d %H:%M:%S')
    elif format == "hour":
        return now.strftime('%H')
    else:
        return now

def getRandInRange(min=100,max=999):
    return random.randint(min,max)

def getRandDeltaInRange(min=100,max=999):
    return getNow() + getRandInRange(min,max)


# Register signal handlers
# SIGINT - CTRL+C
signal.signal(signal.SIGINT, signal_handler)
# SIGTERM - kill 15
signal.signal(signal.SIGTERM, signal_handler)

# Register exit handler
atexit.register(exit_handler)
