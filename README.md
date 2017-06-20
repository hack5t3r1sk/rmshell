# rmshell

## About me
*rmshell* is a tool to resolve [root-me.org](https://www.root-me.org/) challenges over a SOCKS proxy.  

It's main purpose is to check wether the public IP has changed.  
If yes it will perform a new login on root-me.org through the proxy, allowing the current public IP to SSH into the challenge.  

The second purpose (to be impleted at the time of writing) is to provide the challenge selection
and the corresponding SSH shell in the same window.

## Howto
```bash
challenger@computer:/rmshell $ git clone https://github.com/hack5t3r1sk/rmshell.git
challenger@computer:/rmshell $ cd rmshell
challenger@computer:/rmshell $ cp rmlogin.conf.example rmlogin.conf
```
... then edit rmlogin.conf with your credentials and proxy-settings.  
You can avoid the proxy completely by setting it to `""`.

To start the curses interface (decrease your terminal's font-size to see more output):
```bash
challenger@computer:/rmshell $ python rmscreen.py
```

To start the auto-login script alone:
```bash
challenger@computer:/rmshell $ python rmlogin.py.py
```

If for some reason the program crashes and lets your terminal in a weird state, don't panic.  
Just:
```bash
challenger@computer:/rmshell $ stty sane
```


