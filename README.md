# file-crypt-utils

Scripts for automatic crypt files
you make *src* and *dst* dirs

## crypter.d.py
### root
crypter.d.py read files from *src*, encrypt it with AES and move to *dst*.
For more security better(if you use it on server somewhere in internet),
you should run it from root. When *src* is on you regular user, *dst*
is on another.
**It is daemon**
## remover.d.py
### root
remover.d.py remove files in *src* dir after encrypting. Run it from regulat user, not root.
**It is daemon**
## keeper.d.py
### root
keeper.d.py look for *dst* and wait for requests from port.
keeper.d.py can add&encrypt new files, decrypt&return old files, remove files.
run it on root.
**It is daemon.**
## asker.py
### user
asker.py is script for connecting to keeper.d.py. Use it for add new files or
read files from store and print it on stdout or delete files in store.
All operations requires passoword.
**It isn't daemon.**

you should run crypter.d and keeper.d manual AND type password after run
so encrypt-password exist only in RAM
