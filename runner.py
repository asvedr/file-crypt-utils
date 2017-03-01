#!/usr/bin/env python3
import subprocess as sp
import os.path as path
import getpass
import argparse
import sys
import os

parser = argparse.ArgumentParser('crypt all files from dir and remove source')
parser.add_argument('-s', help='source dir')
parser.add_argument('-d', help='destination dir')
parser.add_argument('-p', help='password')
args = parser.parse_args()

if args.s is None:
	print('source dir not setted')
	sys.exit(1)
if args.d is None:
	print('destination dir not setted')
	sys.exit(1)

src = path.abspath(args.s)
dst = path.abspath(args.d)
if args.p is None:
    passwd = getpass.getpass()
else:
    passwd = args.p

pdir    = path.dirname(path.abspath(__file__))
crypter = path.join(pdir, 'crypter.d.py')
keeper  = path.join(pdir, 'keeper.d.py')

if os.fork() == 0:
	crypt_d = sp.Popen([crypter, '--src', src, '--dst', dst, '--daemon', '--softpass'], stdin=sp.PIPE)
	crypt_d.stdin.write((passwd + '\n').encode('utf8'))
	crypt_d.stdin.flush()
	print('crypt ok')
	sys.exit(0)
else:
	keep_d = sp.Popen([keeper, '--dir', dst, '--daemon', '--softpass'], stdin=sp.PIPE)
	keep_d.stdin.write((passwd + '\n').encode('utf8'))
	keep_d.stdin.flush()
	print('keep ok')
	sys.exit(0)
