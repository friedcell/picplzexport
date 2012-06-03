Backing up your Picplz account
==============================

You need to have python installed (you do if you're on a recent OS X and likely on a recent Linux).

Put the code into a folder where you want the backup done, then run (of course you need to substitute [username] with your picplz username / email)

    python picplzexport.py [username]

You will be prompted to enter your password (we don't want it lying around in .bash_history).

The run might take a while. When it's done you'll have:

- downloaded full images (picplz_[id].jpg)
- an html (picplz_[username]_backup.html)
