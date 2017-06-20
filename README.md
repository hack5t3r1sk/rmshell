# rmshell

## About me
*rmshell* is a tool to resolve [root-me.org](https://www.root-me.org/) challenges over a SOCKS proxy.  
It's main purpose is to check wether the public IP has changed.  
If yes it will perform a new login on root-me.org through the proxy, allowing the current public IP to SSH into the challenge.  
The second purpose (to be impleted at the time of writing) is to provide the challenge selection
and the corresponding SSH shell in the same window.

## Howto
```bash
git clone https://github.com/hack5t3r1sk/rmshell.git
cd rmshell
```
... then edit rmlogin.conf with your credentials and proxy-settings.  
You can avoid the proxy completely by setting it to `""`, and then:
```bash
python rmscreen.py
```
