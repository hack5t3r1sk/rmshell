#!/usr/bin/env python
# -*- coding: utf-8 -*-

global rmVersion
rmVersion = '0.2'

################## LOG AND DEBUG
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

global DEBUG
DEBUG = 0

global loginQueue
loginQueue = None

################## END: LOG AND DEBUG

################## GLOBAL CONFIGURATION
global cfg
cfg = None
################## END: GLOBAL CONFIGURATION


################## GLOBAL RUNTIME VARS
# Setting UPDATE = True will perform challenges update on startup
global UPDATE
UPDATE = False
################## END: GLOBAL RUNTIME VARS
