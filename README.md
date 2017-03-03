# file-crypt-utils

## require
pycrypto

## synopsys
Scripts for automatic crypt files.
You make *src* and *dst* dirs. Daemons grab files from
*src*, encrypt and put in *dst*. And change owner to root.

system tested on linux and osx by python3

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
## runner.py
### root
runner.py is one script for sync running crypter.d and keeper.d daemons
## image.py
### user
simple script to hide text in any image using text, image, and password.
Or gen generate random image and hide text there

you should run crypter.d and keeper.d manual AND type password after run
so encrypt-password exist only in RAM
