import curses, sys, time, subprocess
from threading  import Thread
from Queue import Queue, Empty

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

class loginWidget():
    def __init__(self, stdscr, height, width):
        self.height = (height / 2) -4
        self.width = width -2
        self.beginX = 2
        self.beginY = 4
        # Create new sub-window
        self.win = curses.newwin(self.height, self.width, self.beginY, self.beginX)
        self.win.border(1)
        # Add title to th sub-window
        self.win.addstr(0,5,'| LOGIN LOG |')

    def update(self, lines):
        lineNr = 1
        if len(lines) > self.height - 2:
            startIdx = len(lines) - self.height + 2
        else:
            startIdx = 0
        endIdx = len(lines)
        if len(lines[startIdx:endIdx]) >= self.height:
            self.win.addstr(lineNr,2, 'THIS IS STILL TOO BIG [%s]' % len(lines[startIdx:endIdx]))
            return
        for loginLine in lines[startIdx:endIdx]:
            # add the line to the subwindow
            if len(loginLine) > self.width - 1:
                self.win.addstr(lineNr,1, loginLine[0:self.width - 8] + '[...]')
            else:
                self.win.addstr(lineNr,1, loginLine)
            lineNr += 1
            # call addstr() and refresh()
        self.win.refresh()




class  loginProcess():
    def __init__(self):
        # Define the subprocess args
        autologin = ['python', './rmlogin.py']

        # Start the subprocess
        self.process = subprocess.Popen(autologin,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     bufsize=1,
                                     close_fds=ON_POSIX)
        self.log = []
        self.queue = Queue()
        self.reader = Thread(target=enqueue_output, args=(self.process.stdout, self.queue))
        self.reader.daemon = True # thread dies with the program
        self.reader.start()

    def updateLog(self):
        done = False
        while not done:
            try:  loginLine = self.queue.get_nowait() # or q.get(timeout=.1)
            except Empty:
                #print('Empty exception, setting done=True')
                done = True
            else: # got line
                # add the line to the subwindow
                self.log.append(loginLine)
        return self.log



def main(winMain):
    doQuit = False
    showLogin = False
    showShell = False

    # Start the auto-login script
    loginProc = loginProcess()

    # Make stdscr.getch non-blocking
    winMain.nodelay(True)
    width = 4
    count = 0
    direction = 1


    # Create main window
    #winMain = curses.initscr()
    curses.curs_set(0)

    # Don't echo keys pressed
    curses.noecho()

    while not doQuit:
        height, width = winMain.getmaxyx()
        # Store the queued output to our log
        loginProc.updateLog()
        # Set the border on
        winMain.border(1)
        winMain.clear()

        # Set title
        winMain.addstr(0,5,'| ROOT THE CASBA |')
        winMain.addstr(2,5, "Usage: q = quit | l = show/hide login log | s = show/hide the shell")
        winMain.refresh()

        if showLogin:
            winLogin = loginWidget(winMain, height, width)
            winLogin.update(loginProc.log)

        # Wait for a char
        k = winMain.getch()
        # Clear out anything else the user has typed in
        curses.flushinp()

        # Analyse key pressed
        if k == ord('q'):
            doQuit = True
        elif k == ord('l'):
            showLogin = not not not showLogin
        elif k == ord('s'):
            showShell = not not not showShell
        else:
            pass

        time.sleep(0.1)

    curses.endwin()


curses.wrapper(main)
