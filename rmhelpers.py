#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob

import datetime as dt, sys, random, time
import atexit, signal

def setLogLevel(level):
    glob.LOGLEVEL = level

def getDebugLevel():
    return glob.DEBUG

def setDebugLevel(level):
    glob.DEBUG = level

# Intercepts sys.exit(0)
def exit_handler():
    rmlog(u'rmhelpers::exit_handler()', u'Application ending.')

# Intercepts any signal
def signal_handler(signalId, frame):
    if signalId == signal.SIGTERM:
        rmlog(u'rmhelpers::signal_handler()', u'Received SIGTERM: exiting.')
    if signalId == signal.SIGINT:
        rmlog(u'rmhelpers::signal_handler()', u'Keyboard Interrupt (SIGINT): exiting.')
    sys.exit(0)

def getaddrinfo(*args):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]

def getChallengePath(uri):
    if uri:
        uriSplit = uri.split('/')
        return '%s_%s' % (uriSplit[-2], uriSplit[-1])
    else:
        return None

def getSshDict(ssHref):
    if ssHref:
        scheme, uri = ssHref.split("://")
        creds, service = uri.split("@")
        user, password = creds.split(":")
        host, port = service.split(":")
        return {'user': user, 'password': password, 'host': host, 'port': port}
    else:
        return None

def rmWriteOut(msg):
    if glob.loginQueue:
        glob.loginQueue.put(msg)
    else:
        sys.stdout.write(msg)
        sys.stdout.flush()
    if glob.cfg['rmLogFile'] != "":
        with open(glob.cfg['rmLogFile'], 'a') as logFile:
            logFile.write(msg)

def rmlog(funcName, msg, level="info"):
    tstamp = getNow('sql')
    umsg = msg.encode('utf-8')
    if level == 'info':
        rmWriteOut("%s::[INFO]:%s: %s\n" % (tstamp, funcName, umsg))
    elif level == 'warning':
        rmWriteOut("%s::[WARNING]:%s: %s\n" % (tstamp, funcName, umsg))
    elif level == 'debug':
        if glob.DEBUG and glob.DEBUG >= 1:
            rmWriteOut("%s::[debug]:%s: %s\n" % (tstamp, funcName, umsg))
    elif level == 'debug2':
        if glob.DEBUG and glob.DEBUG >= 2:
            rmWriteOut("%s::[debug2]:%s: %s\n" % (tstamp, funcName, umsg))
    elif level == 'debug3':
        if glob.DEBUG and glob.DEBUG >= 3:
            rmWriteOut("%s::[debug3]:%s: %s\n" % (tstamp, funcName, umsg))
    else:
        rmWriteOut("%s::[ERROR]:%s: %s\n" % (tstamp, funcName, umsg))

def truncLine(line, width):
    if len(line) > width - 8:
        return line[0:width - 8] + '[...]'
    else:
        return line

def rmDiff(i):
    diffList = {0: 'Unknown', 1: "Very easy", 2: "Easy", 3: "Medium", 4: "Hard", 36: "Very hard"}
    if i in diffList:
        return diffList[i]
    else:
        return "= n-a ="

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

def sleep(secs):
    rmlog("RMHelpers::sleep()", "Sleeping %s seconds..." % secs, "debug")
    time.sleep(secs)

# Register signal handlers
# SIGINT - CTRL+C
signal.signal(signal.SIGINT, signal_handler)
# SIGTERM - kill 15
signal.signal(signal.SIGTERM, signal_handler)

# Register exit handler
atexit.register(exit_handler)
