######## THIS UPDATES THE CHALLENGES IN STATE-STORE
import os
import glob
glob.DEBUG = 3
glob.initCwd = os.getcwd()
from rmhelpers import *

import rmlogin
from rmchallenge import RMChallenge

b = rmlogin.init()
glob.UPDATE = True
# might be needed...
#b.doLogin()
for c in b.categories:
    i = 0
    print "############### %s" % c

    for ch in c.challenges:
       challStore = '%s/.rmshell/RMChallenge.db' % ch.getPath()
       if not os.path.exists(challStore):
          print c.challenges[i]
          print "CHALLENGE FILE NOT FOUND - UPDATING"
          c.challenges[i] = RMChallenge(browser=b, challObj=ch)
       else:
          print "CHALLENGE FOUND - UPDATING AND GETTING AGAIN"
          os.remove(challStore)
          c.challenges[i] = RMChallenge(browser=b, challObj=ch)
          c.challenges[i].getChallenge(b)
       i += 1
b.saveState()
glob.UPDATE = False
####################### END UPDATE CATEGORIES



