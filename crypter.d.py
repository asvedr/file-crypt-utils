#!/usr/bin/env python3

# ARGS:
#   ["daemon"] // if this flag exist, process will be run as daemon
#   <src-dir>  // directory to get raw files
#   <dst-dir>  // directory to put crypted files
#   <passwd>   // password to encrypt
#   [port]     // port to connect with delete-daemon. Default is 28960.
#      // if port is 'DEL' then crypter will remove files without daemon

# enc: openssl aes-256-cbc -a -salt -in <input> -out <output>
# dec: openssl aes-256-cbc -d -a -in <input> -out <output>

import subprocess as sp
import sys
import os
import stat
import time
import socket
import json

def log(text):
    t = time.localtime()
    t = '%s.%s.%s %s:%s:%s' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    with open('log', 'a') as h:
        h.write('%s: %s\n' % (t, text))

def to8(s):
    for _ in range(0, 8 - len(s)):
        s = '0' + s
    return s

class Remover:
    def __init__(self,port):
        self.port = port
        self.files = []
        self.dirs = []
    def dfile(self, path):
        self.files.append(os.path.abspath(path))
        log('FILE: ' + path)
    def ddir(self, path):
        self.dirs.append(os.path.abspath(path))
        log('DIR:  ' + path)
    def flush(self):
        if len(self.files) + len(self.dirs) == 0:
            return
        if self.port == 'DEL':
            for f in self.files:
                try:
                    os.remove(f)
                except:
                    log("can't rm file: " + f)
                    pass
            for d in self.dirs:
                try:
                    os.rmdir(d)
                except:
                    log("can't rm dir: " + d)
                    pass
        else:
            sock = socket.socket()
            sock.settimeout(3)
            try:
                sock.connect( ('127.0.0.1', self.port) )
                connected = True
            except:
                connected = False
            if connected:
                mess = json.dumps({'f': self.files, 'd': self.dirs}).encode('utf8')
                sock.send(to8(hex(len(mess))[2:]).encode('utf8'))
                sock.send(mess)
                if sock.recv(1).decode('utf8') != 'y':
                    log('bad rm request')
            else:
                log('no connection')
        self.files = []
        self.dirs = []

# args: (path,path,password) -> exit-code
def decrypt(inp, out, pas):
    return sp.call(['openssl', 'aes-256-cbc', '-d', '-a', '-in', inp, '-out', out, '-pass', 'pass:' + pas]) == 0
def encrypt(inp, out, pas):
    return sp.call(['openssl', 'aes-256-cbc', '-a', '-salt', '-in', inp, '-out', out, '-pass', 'pass:' + pas]) == 0

# args:
#   1 - src dir
#   2 - dest dir
#   3 - pass
class Crypter:
    def __init__(self,argv):
        self._srcd = argv[0]
        self._dstd = argv[1]
        self._pass = argv[2]
        if len(argv) > 3:
            if argv[3] == 'DEL':
                self._port = 'DEL'
            else:
                self._port = int(argv[3])
        else:
            self._port = 28960
        self.remover = Remover(self._port)
    def run(self):
        while True:
            self.trydir(self._srcd, self._dstd)
            self.remover.flush()
            time.sleep(5)
    def trydir(self, src, dst):
        if os.path.isfile(dst):
            for i in range(0, 10000):
                if not os.path.isfile(dst + str(i)):
                    dst = dst + str(i)
                    if os.path.isdir(dst):
                        self.withdir(src, dst)
                    else:
                        os.mkdir(dst)
                        self.withdir(src, dst)
                    return
            log('YOU FAGGOT')
            exit(1)
        elif os.path.isdir(dst):
            self.withdir(src, dst)
        else:
            os.mkdir(dst)
            self.withdir(src, dst)
    def withdir(self, srcd, dstd):
        print(srcd)
        for root,dirs,files in os.walk(srcd):
            for obj in files:
                finp = os.path.join(root, obj)
                fout = os.path.join(dstd, obj)
                encrypt(finp, fout, self._pass)
                os.chmod(fout, 0o600)
                self.remover.dfile(finp)
            for obj in dirs:
                finp = os.path.join(root, obj)
                fout = os.path.join(dstd, obj)
                self.trydir(finp, fout)
                self.remover.ddir(finp)

user = sp.check_output(['whoami']).decode('utf8').strip()
if user != 'root':
    print('run script from root please (%s)' % user)
    sys.exit(1)
args = sys.argv[1:]
if args[0] == 'daemon':
    args = args[1:]
    if os.fork() == 0:
        setsid()
        Crypter(args).run()
else:
    Crypter(args).run()
