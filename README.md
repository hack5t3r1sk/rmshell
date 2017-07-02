# rmshell

## About me
*rmshell* is a tool to resolve [root-me.org](https://www.root-me.org/) challenges over a SOCKS proxy.

It's main purpose is to check whether the public IP has changed.
If yes it will perform a new login on root-me.org through the proxy, allowing the current public IP to SSH into the challenge.

The second purpose is to provide a terminal-based navigation through the challenges
and (still to be implemented) the selection of a challenge, opening the corresponding
SSH shell in a dedicated panel over the SOCKS tunnel.

## Howto

### Dependencies
* Python
  * BeautifulSoup (from bs4 import BeautifulSoup, UnicodeDammit)
  * atexit, Datetime, json, os, cPickle, Queue, signal, sys, time, urllib, urllib2, yaml
* Network (optional)
  * a SOCKS proxy (SSH/Tor/etc...)

### Installation / Usage
```bash
challenger@computer:/ $ git clone https://github.com/hack5t3r1sk/rmshell.git
challenger@computer:/ $ cd rmshell
challenger@computer:/rmshell $ cp rmlogin.conf.example rmlogin.conf
```
... then edit rmlogin.conf with your credentials and proxy-settings.
You can avoid the proxy completely by setting
```
proxyHost: ""
```

You can also set your credentials to
```
rmuser: ""
rmpassword: ""
```
if you only want to test the UI.

To start the curses interface (decrease your terminal's font-size to see more output):
```bash
challenger@computer:/rmshell $ python rmscreen.py
```

To start the auto-login script alone:
```bash
challenger@computer:/rmshell $ python rmlogin.py
```

If for some reason the program crashes and lets your terminal in a weird state, don't panic.
Just:
```bash
challenger@computer:/rmshell $ stty sane
```


## Changelog
### v0.4
* UI (rmscreen) : added Challenge interaction
  - added 'Enter' command that opens the selected challenge. For now, 'Enter'
    - suspends the curses interface
    - parse the challenge's page
    - download any file provided (download-links)
    - displays all informations found on the challenge's page
    - starts the challenge's SSH if available or a simple local shell
    - restores the UI after exit
  - improved logging

* RMCategor(ies|y) / RMChallenge / rmlogin
  - added save() and load() methods to RMCategories and RMChallenge (removed from rmlogin)
  - improved state-saving by Noning some runtime-properties before saving (faster startup)
  - introducing challenges directory structure:
    - each challenge has its own directory
    - its state is stored in a hidden directory
  - refactor of rmlogin workflow
  - added rmBuildDB.py for building the whole challenges Tree (this is more for testing, in practice you only want the challenge that you have worked on)

* Base Browser
  - added retry on GET requests, in case the connection was reset in the middle of a request
  - added DNS-cache to avoid secure-resolve of challenges SSH servers multiple time
  - added download method for downloading files over proxy

### v0.3
* Code refactoring (mainly removing global stuff and splitting code into several files)
  - splitted the old RMBrowser into:
    1. a base Browser class for the low-level operations (this subclasses Thread)
    2. a RMBrowser class for the root-me.org specific properties and methods
    3. a RMCategories class for scraping and holding the whole categories-tree (this object will be saved to a file after a sucessful update)
    4. a RMCategory class for scraping and representing a category, including all its challenges
    5. a RMChallenge class for scraping and representing a challenge
  - removed the global browser variable, which is now passed over when needed
  - added a log-file in the glob.cfg
  - improved logging to support the logfile
* rmlogin.py / rmhelpers.py
  - removed unuseful requests for speeding up the whole loop
  - optimized the waiting times in the loop to speed up the init process
  - improved logging
  - ipCheck(): added loggedIn() check when 'IP is still the same', to be sure we're always logged in
* UI (rmscreen)
  - fixed a bug in the logic deciding which login-log-lines are shown (we were missing the last line)
  - added a "Loading, please wait" message at startup
  - adapted to the new RMCategories, RMCategory and RMChallenge classes

### v0.2
* RMBrowser / rmlogin / helpers
  - added a `glob` namespace for sharing global variables across all files
  - added a `debug` setting in rmlogin.conf that defines `glob.DEBUG`
  - improved logging to support the global `glob.loginQueue`
  - added the scraping logic for categories and challenges
  - added state-storage with `pickle`
  - added UTF-8 encoding to the state strings
* UI (rmscreen)
  - added command `0` to `3` for changing `glob.DEBUG` from the UI
  - replaced `subprocess.Popen()` with `threading.Thread()` to interact with rmlogin at runtime via globals
  - added a global `loginQueue` for logging the thread's output with the helper rmlog()
  - improved display logic to avoid flickering / weird chars
  - added challenges-widget for displaying categories, challenges and associated descriptions
  - added the scrolling / selection logic to the list display
  - added update command `u` for refreshing / initializing the state-storage
  - added colors
