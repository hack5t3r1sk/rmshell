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
  * atexit, Datetime, json, pickle, Queue, signal, sys, time, urllib, urllib2, yaml
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
  - added a global `loginQueue` for log with the thread with the helper
  - improved display logic to avoid flickering / weird chars
  - added challenges-widget for displaying categories, challenges and associated descriptions
  - added the scrolling / selection logic to the list display 
  - added update command `u` for refreshing / initializing the state-storage
  - added colors
