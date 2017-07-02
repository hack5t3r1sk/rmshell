#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import glob

import curses, shlex, subprocess, os, time, traceback
from threading  import Thread
from rmhelpers import *
from math import *

# Set the Queue for the Thread BEFORE importing rmlogin
# for logging the Browser-imports
import Queue
glob.loginQueue = Queue.Queue()

import rmlogin

# Store the selected element in the categories-lists
catListPos = 1

# Store the selected element in the challenges-lists
challListPos = 1

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def flushQueue(queue,outList):
    done = False
    while not done:
        try:  loginLine = queue.get_nowait() # or q.get(timeout=.1)
        except Empty:
            #print('Empty exception, setting done=True')
            done = True
        else: # got line
            # add the line to the subwindow
            outList.append(loginLine)
    return outList

""" A possible solution from https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
fcntl, select, asyncproc won't help in this case.

A reliable way to read a stream without blocking
regardless of operating system is to use Queue.get_nowait():

import sys
from subprocess import PIPE, Popen
from threading  import Thread

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
q = Queue()
t = Thread(target=enqueue_output, args=(p.stdout, q))
t.daemon = True # thread dies with the program
t.start()

# ... do other things here

# read line without blocking
try:  line = q.get_nowait() # or q.get(timeout=.1)
except Empty:
    print('no output yet')
else: # got line
    # ... do something with line



"""

""" Another solution from https://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python

I typically want my program to exit, ut it can't because readline()
is still blocking in the other thread waiting for a line.
A solution I have found to this problem is to make stdin
a non-blocking file using the fcntl module:



import fcntl
import os
import sys

# make stdin a non-blocking file
fd = sys.stdin.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

# user input handling thread
while mainThreadIsRunning:
      try: input = sys.stdin.readline()
      except: continue
      handleInput(input)

"""




"""
Test process


import subprocess
proc = subprocess.Popen(['python', './rmlogin.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
proc.communicate()

for line in proc.stdout.readlines():
  print line



"""

class suspend_curses():
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        newscr = curses.initscr()
        newscr.addstr('Newscreen is %s\n' % newscr)
        newscr.refresh()
        curses.doupdate()




################################### WIDGETS
class LoginWidget():
    def __init__(self, winParent, height, width):
        self.winParent = winParent
        self.height = int(height / 3) - 2
        self.width = width - 3
        self.beginX = 1
        self.beginY = 4
        # Create new sub-window
        self.win = curses.newwin(self.height, self.width, self.beginY, self.beginX)

    def update(self, lines):
        self.win.clear()
        lineNr = 1
        maxlines = self.height - 2
        # Compute the max number of line according to current height
        if len(lines) > maxlines:
            startIdx = len(lines) - maxlines     # maxlines + 2 == self.height
        else:
            startIdx = 0

        # The last line should be the last one shown
        endIdx = len(lines)

        # Check if we miscomputed
        if len(lines[startIdx:endIdx]) >= self.height:
            self.win.addstr(lineNr,2, 'THIS IS STILL TOO BIG [%s]' % len(lines[startIdx:endIdx]))
            return

        # Display the lines
        for loginLine in lines[startIdx:endIdx]:
            if loginLine:
                # add the formatted line to the subwindow
                self.win.addstr(lineNr,2, truncLine(loginLine, self.width), curses.color_pair(2))
                lineNr += 1
        self.win.border(1)

        # Add title to the sub-window
        self.win.addstr(0,5,'| LOGIN LOG |', curses.color_pair(1))
        self.win.noutrefresh()


class ChallWidget():
    def __init__(self, winParent, height, width):
        self.winParent = winParent
        self.listHeight = int(height / 3) - 2
        self.descHeight = int(height / 3) - 1
        self.widthDesc = width - 3
        self.widthCat = int(width / 4) - 3
        self.widthChall = int( width / 4) * 3 - 1
        self.beginX = 1
        self.beginY = int(height / 3) + 2
        self.beginChall = self.widthCat + 2 + self.beginX

        # Create new sub-windows
        self.winCat = curses.newwin(self.listHeight, self.widthCat, self.beginY, self.beginX)
        self.winChall = curses.newwin(self.listHeight, self.widthChall, self.beginY, self.beginChall)
        self.winDesc = curses.newwin(self.descHeight, self.widthDesc, self.beginY + self.listHeight, self.beginX)

        # Holds the current maximum items in list
        self.maxlines = self.listHeight - 2
        # Holds the number of categories
        self.catLines = 0
        # Holds the number of challenges in the currently seleted categories
        self.challLines = 0
        self.descMsg = ""
        self.catDesc = ""
        self.challDesc = ""

    def update(self, browser):
        # Clear the sub-windows
        self.winCat.clear()
        self.winChall.clear()
        self.winDesc.clear()

        # If we are updating the DB, alert the user
        if glob.UPDATE:
            self.winCat.addstr(2,2, ' !  UPDATING  ! ',
                    curses.A_BOLD | curses.A_BLINK | curses.color_pair(3))
            self.winChall.addstr(2,2, '   Please wait until update has completed, I will then disappear :=]   ', curses.color_pair(3))
        else:
            categories = browser.categories.get()
            if categories and len(categories) >0:
                self.catLines = len(browser.categories)

                # Compute the slice to be displayed depending on
                # catListPos , self.catLines and self.maxlines
                # If the list is bigger than maxlines
                # and current position is not at bottom, no scroll
                if self.catLines > self.maxlines:
                    # WHEN WE DO SCROLL
                    if catListPos > self.maxlines - 2:
                        delta = catListPos - self.maxlines + 2
                        # If we are not displaying the last item aready
                        if self.catLines > ( delta + self.maxlines ):
                            startIdx = delta
                            endIdx = self.maxlines + delta
                        else:   # WE REACHED THE END OF THE LIST, STOP SCROLLING
                            startIdx = delta
                            endIdx = self.catLines
                    # WHEN WE DO NOT SCROLL
                    else:
                        delta = None
                        startIdx = 0
                        endIdx = self.maxlines
                # SHOW EVERYTHING
                else:
                    delta = None
                    startIdx = 0
                    # The last line should be the last one shown
                    endIdx = self.catLines

                # Display the slice of cateories around current position
                catLineNr = 1
                for category in browser.categories.list[startIdx:endIdx]:
                    # Is this the selected category ?
                    if ((catLineNr + startIdx) == catListPos):
                        # Display TITLE with inverted list-colors
                        self.winCat.addstr(catLineNr, 2, " %s " % truncLine(
                                                category, self.widthCat - 2), curses.color_pair(5))
                        self.catDesc = "[  Category ] '%s'" % browser.categories[catListPos - 1].description

                        # Populate challenges
                        self.challLines = len(browser.categories[catListPos - 1].challenges)

                        # Compute the slice to be displayed depending on
                        # challListPos , self.challLines and self.maxlines
                        # If the list is bigger than maxlines
                        # and current position 2 lines before bottom, no scroll
                        if self.challLines > self.maxlines:
                            # WHEN WE DO SCROLL
                            if challListPos > self.maxlines - 2:
                                challDelta = challListPos - self.maxlines + 2
                                # If we are not displaying the last item aready
                                if self.challLines > ( challDelta + self.maxlines ):
                                    startIdxChall = challDelta
                                    endIdxChall = self.maxlines + challDelta
                                else:   # WE REACHED THE END OF THE LIST, STOP SCROLLING
                                    startIdxChall = challDelta
                                    endIdxChall = self.challLines
                            # WHEN WE DO NOT SCROLL
                            else:
                                challDelta = None
                                startIdxChall = 0
                                endIdxChall = self.maxlines
                        # SHOW EVERYTHING
                        else:
                            challDelta = None
                            startIdxChall = 0
                            # The last line should be the last one shown
                            endIdxChall = self.challLines

                        challLineNr = 1
                        for challenge in browser.categories[catListPos - 1].challenges[startIdxChall:endIdxChall]:
                            challLine = truncLine('%s' % challenge, self.widthChall - 3 )
                            try:
                                if ((challLineNr + startIdxChall) == challListPos):
                                    self.winChall.addstr(challLineNr , 2, challLine, curses.color_pair(7))
                                    self.challDesc = "[ Challenge ] '%s'" % challenge.description
                                else:
                                    self.winChall.addstr(challLineNr , 2, challLine, curses.color_pair(6))
                            except:
                                try:
                                    challLine = truncLine("ERR: max: %s | tt: %s | sta: %s | end: %s | nr: %s" % (
                                                                    self.maxlines, self.challLines, startIdxChall, endIdxChall,  challLineNr ))
                                    self.winChall.addstr(challLineNr , 2, challLine)
                                except:
                                    print "ERR: max: %s | tt: %s | sta: %s | end: %s | nr: %s" % (
                                        self.maxlines, self.challLines, startIdxChall, endIdxChall,  challLineNr )
                                    dir(curses.error)
                                    time.sleep(2)
                                    pass
                                pass
                            challLineNr += 1
                    else:
                        # Show with list colors
                        catLine = truncLine(" %s " % category, self.widthCat)
                        self.winCat.addstr(catLineNr, 2, catLine, curses.color_pair(4))
                    catLineNr += 1
                # DEBUG IN CHALLENGES WINDOW
                #self.winChall.addstr(1, 2, "self.catLines => [%s] | self.maxlines => [%s] | position => [%s] " % (self.challLines, self.maxlines, catListPos), curses.color_pair(4))
                #self.winChall.addstr(2, 2, "startIdx => [%s] | endIdx => [%s] | delta => %s" % (startIdx, endIdx, challDelta), curses.color_pair(4))
            else:
                # Alert
                self.winCat.addstr(2,2, 'No category found !', curses.color_pair(3))
                self.winChall.addstr(2,2, 'No challenges found in browser. Press "u" to update !', curses.color_pair(3))

        # Display decriptions
        self.winDesc.addstr(1, 2, truncLine('%s' % self.catDesc, self.widthChall * 2 - 3 ), curses.color_pair(4))
        curY, curX = self.winDesc.getyx()
        if curY + 2 <= self.maxlines:
            self.winDesc.addstr(curY + 2, 2, truncLine('%s' % self.challDesc, self.widthChall * 2 - 3 ), curses.color_pair(6))

        # Add borders and titles
        self.winCat.border(1)
        self.winCat.addstr(0,2, '| CATEGORIES < >|', curses.color_pair(4))
        self.winChall.border(1)
        self.winChall.addstr(0,2, '| CHALLENGES ^ v|', curses.color_pair(6))
        self.winDesc.border(1)
        self.winDesc.addstr(0,2, '| DESCRIPTIONS |', curses.color_pair(1))

        # Refresh without output
        self.winCat.noutrefresh()
        self.winChall.noutrefresh()
        self.winDesc.noutrefresh()

    def moveCatDown(self):
        global challListPos
        global catListPos
        if catListPos <self.catLines:
            # Reset challListPos when changing category
            challListPos = 1
            catListPos += 1

    def moveCatUp(self):
        global challListPos
        global catListPos
        if catListPos >1:
            # Reset challListPos when changing category
            challListPos = 1
            catListPos -= 1

    def moveChallDown(self):
        global challListPos
        if challListPos <self.challLines:
            challListPos += 1

    def moveChallUp(self):
        global challListPos
        if challListPos >1:
            challListPos -= 1

################################### THREADS
class  loginThread():
    def __init__(self):
        self.log = []
        self.browser = rmlogin.init()
        self.thread = Thread(target=rmlogin.start, kwargs={'browser': self.browser})
        self.thread.daemon = True # thread dies with the program
        self.thread.start()

    def updateLog(self):
        done = False
        while not done:
            try:
                loginLine = glob.loginQueue.get_nowait() # or q.get(timeout=.1)
            except Queue.Empty:
                #print('Empty exception, setting done=True')
                done = True
                pass
            else: # got line
                # add the line to the subwindow
                self.log.append(loginLine)
        return self.log

def startChallenge(selectedChallenge, browser, forceLocalShell=False):
    challError = False
    # backup Queue
    bkpQueue = glob.loginQueue
    glob.loginQueue = False
    selectedChallenge.browser = browser

    with suspend_curses():
        # Clear the screen
        os.system('clear')
        print "Getting challenge..."
        # Get the challenge
        try:
            selectedChallenge.getChallenge()
        except Exception as e:
            print "ERROR: unable to get the challenge right now: [%s]" % e
            traceback.print_exc()
            challError = True
        else:
            if glob.cfg['rmuser'] == "" or glob.cfg['rmuser'] == "":
                print
                print
                print "    !!!! YOU HAVE TO SET YOUR rmuser and rmpassword IN rmlogin.conf TO ACCESS THE CHALLENGE !!! "
                print
                print

            selectedChallenge.browser = browser
            # Store current working dir and cd into challDir
            currentCwd = os.getcwd()
            if os.path.exists(selectedChallenge.path):
                os.chdir(selectedChallenge.path)
                # Display the challenge's summary
                selectedChallenge.printStatement()

                # Restore Queue
                glob.loginQueue = bkpQueue
                if selectedChallenge.ssh and not forceLocalShell:
                    # Get cmdString and password
                    (sshCmd, password) = selectedChallenge.getSshCmdPass()
                    if sshCmd:
                        # Start the challenge's SSH
                        print "Starting [%s]..." % sshCmd
                        # DEBUG
                        #print selectedChallenge.sshCmd
                        ret = subprocess.call(sshCmd, shell=True)
                        if ret >0:
                            challError = True
                    else:
                        challError = True
                        print
                        print "ERROR: Invalid SSH command [%s], aborting !" % sshCmd
                        print
                else:
                    print "The challenge doesn't have an SSH link, starting local shell instead..."
                    # Start a simple local shell
                    subprocess.call(['/bin/bash'])
                # Restore previous working dir
                os.chdir(currentCwd)
            else:
                print "The challenge's path does not exist, are you logged in ?"
                challError = True
        if not glob.loginQueue:
            # Restore Queue
            glob.loginQueue = bkpQueue

        # TODO: flush user input queue
        if challError:
            secs = 10
            print
            print "ERROR: Waiting %ss, to let you know about the error. Press CTRL+C to keep reading..." % secs
            # DEBUG
            time.sleep(secs)

def main(winMain):
    doQuit = False
    showChall = True
    showLogin = True
    showShell = False

    # Initializes curses
    curses.curs_set(0)

    # Don't echo keys pressed
    curses.noecho()

    # Async getch
    curses.cbreak()

    # Enable colors (done by wrapper)
    #curses.start_color()

    # Make stdscr.getch non-blocking
    winMain.nodelay(True)

    # Enable arrow- and special-keys (done by wrapper)
    #winMain.keypad(1)

    ### Define colors
    # TITLES
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    # WARNING
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    # ERRORS
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_WHITE)
    # LIST BLUE
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)
    # LIST GREEN
    curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)
    # HELP / USAGE
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    winMain.addstr(0,2," Loading, please wait... ", curses.color_pair(3))
    winMain.addstr(1,0,"")
    winMain.refresh()

    # Start the auto-login Thread
    login_thread = loginThread()
    winMain.addstr(2,2,"LoginThread loaded !", curses.color_pair(3))
    winMain.refresh()
    # Set the border on
    winMain.border(1)

    # DEBUG
    #time.sleep(10)
    while not doQuit:
        height, width = winMain.getmaxyx()

        # Store the queued output to thread log
        login_thread.updateLog()
        loginStatus = ( login_thread.browser.loggedIn ) and 'LOGGED IN' or 'NOT LOGGED IN'

        # clear the main window
        winMain.clear()

        # Set title
        winMain.border(1)
        winMain.addstr(0,5,'| RM-Shell v%s: ROOT THE CASBA ! (%s)|' % (
                    glob.rmVersion, loginStatus), curses.color_pair(3))
        winMain.addstr(2,5, "  Usage: 0-3 =>debug (%s) | c => challenges | l =>login-log | s =>shell | u =>update_chal-DB (%s) | q =>quit " % (int(getDebugLevel()), glob.UPDATE), curses.color_pair(8))
        winMain.noutrefresh()

        if showLogin:
            winLogin = LoginWidget(winMain, height, width)
            winLogin.update(login_thread.log)

        if showChall:
            winChall = ChallWidget(winMain, height, width)
            winChall.update(login_thread.browser)

        #if showShell:
        #    winShell = shellWidget(winMain, height, width)
        #    winShell.update(browser)

        # Now that the windows are in the next state
        # update the screen for real (no flickering)
        curses.doupdate()

        # Wait for a char
        k = winMain.getch()

        # Clear out anything else the user has typed in
        curses.flushinp()

        # Analyse key pressed
        if k == ord('q'):
            doQuit = True
        ### DEBUG LEVEL
        elif k == ord('0'):
            setDebugLevel(False)
        elif k == ord('1'):
            setDebugLevel(1)
        elif k == ord('2'):
            setDebugLevel(2)
        elif k == ord('3'):
            setDebugLevel(3)
        ### SHOW / HIDE
        elif k == ord('c'):
            showChall = not not not showChall
        elif k == ord('l'):
            showLogin = not not not showLogin
        elif k == ord('s'):
        ### UPDATE CHALLENGES DATABASE
            showShell = not not not showShell
        elif k == ord('u'):
            glob.UPDATE = True
        ### NAVIGATION
        elif k == curses.KEY_RIGHT:
            winChall.moveCatDown()
        elif k == curses.KEY_LEFT:
            winChall.moveCatUp()
        elif k == curses.KEY_DOWN:
            winChall.moveChallDown()
        elif k == curses.KEY_UP:
            winChall.moveChallUp()
        elif k == ord('\n'):
            if login_thread.browser.categories and len(login_thread.browser.categories) >0:
                selectedChallenge = login_thread.browser.categories.get()[catListPos - 1].challenges[challListPos - 1]
                startChallenge(selectedChallenge, login_thread.browser)
        else:
            pass

        # Give the core some breath
        time.sleep(0.1)
    # doQuit is True
    curses.endwin()
# Main scope
if __name__ == "__main__":
    curses.wrapper(main)
