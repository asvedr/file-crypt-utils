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
import argparse
import getpass
from Crypto import Random
from Crypto.Cipher import AES
import hashlib
import base64

PORT = 28960

class AESCipher(object):
    def __init__(self, key): 
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()
    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))
    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

logfile = None
def log(text):
    if logfile is None:
        return
    t = time.localtime()
    t = '%s.%s.%s %s:%s:%s' % (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    with open(logfile, 'a') as h:
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
#def decrypt(inp, out, pas):
#    return sp.call(['openssl', 'aes-256-cbc', '-d', '-a', '-in', inp, '-out', out, '-pass', 'pass:' + pas]) == 0
#def encrypt(inp, out, pas):
#    return sp.call(['openssl', 'aes-256-cbc', '-a', '-salt', '-in', inp, '-out', out, '-pass', 'pass:' + pas]) == 0
def encrypt(inp, out, pas):
    with open(inp, 'rt') as i:
        with open(out, 'wt') as o:
            text = AESCipher(pas).encrypt(i.read()).decode('utf8')
            chunks, chunk_size = len(text), 64
            for line in [ text[i:i+chunk_size] for i in range(0, chunks, chunk_size) ]:
                o.write(line + '\n')

class Crypter:
    def __init__(self,src,dst,fdel,passwd):
        self._srcd = src
        self._ddst = dst
        self._pass = passwd
        if os.path.isdir(dst):
            os.chmod(dst, 0o700)
        if fdel:
            self._port = 'DEL'
        else:
            self._port = PORT
        self.remover = Remover(self._port)
    def run(self):
        while True:
            self.trydir(self._srcd, self._ddst)
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
            os.chmod(dst, 0o700)
            self.withdir(src, dst)
    def withdir(self, srcd, ddst):
        #print(srcd)
        for root,dirs,files in os.walk(srcd):
            for obj in files:
                finp = os.path.join(root, obj)
                fout = os.path.join(ddst, obj)
                encrypt(finp, fout, self._pass)
                os.chmod(fout, 0o600)
                self.remover.dfile(finp)
            for obj in dirs:
                finp = os.path.join(root, obj)
                fout = os.path.join(ddst, obj)
                self.trydir(finp, fout)
                self.remover.ddir(finp)

parser = argparse.ArgumentParser('crypt all files from dir and remove source')
parser.add_argument('--daemon', default=False, action='store_true', help='run process as daemon')
parser.add_argument('--src', help='source dir')
parser.add_argument('--dst', help='destination dir')
parser.add_argument('--fdel', default=False, action='store_true', help="directly delete src, don't use daemon")
parser.add_argument('--log', help='log file', default=None)
parser.add_argument('--softpass', default=False, action='store_true', help='request password without getpass.getpass')
parser.add_argument('--noroot', default=False, action='store_true', help='allow run with no root')
args = parser.parse_args()
if not (args.log is None):
    logfile = args.log

user = sp.check_output(['whoami']).decode('utf8').strip()
if user != 'root' and not args.noroot:
    print('please run from root')
    sys.exit(1)
if args.src is None or args.dst is None:
    print('src or dst not setted')
    sys.exit(1)
if args.softpass:
    passwd = sys.stdin.readline()[:-1]
else:
    passwd = getpass.getpass()
if args.daemon:
    if os.fork() == 0:
        os.setsid()
        Crypter(args.src, args.dst, args.fdel, passwd).run()
else:
    Crypter(args.src, args.dst, args.fdel, passwd).run()
