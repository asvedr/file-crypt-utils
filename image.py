#!/usr/bin/env python3
import argparse
from PIL import Image
from functools import reduce
from struct import unpack
import hashlib
import time
import os
import sys
from binascii import b2a_base64, a2b_base64

# tuple of primary numbers
def _prims(cnt):
    prims = [2]
    i = 3
    while len(prims) < cnt:
        yes = True
        for p in prims:
            if i % p == 0:
                yes = False
                break
        if yes:
            prims.append(i)
        i += 2
    return tuple(prims)
prims = _prims(5001)

# exception for check situation when identyty random generator stucked in loop
class RandomLoop(Exception):
    pass

class DecodeError(Exception):
    pass

# determined random generator
class Random:
    def __init__(self,n0):
        self.n = n0
        self.A = 2050
        self.B = 4000
        self.initM()
    def initM(self):
        self.M = prims[self.A] * prims[self.B]
    def __iter__(self):
        return self
    def __next__(self):
        if self.n == 0:
            self.n = int(self.M * 0.7)
        self.n = (self.n * self.n) % self.M
        return self.n
    def nextid(self, rng, idl):
        ''' return val witch is not in set 'idl' and put it to 'idl' '''
        while True:
            try:
                cnt = 0
                for i in self:
                    val = i % rng
                    if not (val in idl):
                        idl.add(val)
                        return val
                    cnt += 1
                    if cnt > 300:
                        raise RandomLoop()
            except RandomLoop:
                print('end for %s' % self.B)
                self.B -= 1
                self.n = prims[self.B]
                self.initM()

# alphabet len must be < 256
alphabet = ['\n','\t'] + [chr(i) for i in range(32, 127)] + [chr(i) for i in range(ord('А'),ord('ё'))]
alphaind = dict(zip(alphabet, range(len(alphabet))))

def md5(s):
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    return m.hexdigest()

# shuffle alphabet and return
def shuffle(n,count):
    ''' arguments: (seed for RAND, iteration count) '''
    alp = alphabet[:]
    l = len(alp)
    rand = Random(n)
    for n in range(count):
        i = rand.__next__() % l
        j = rand.__next__() % l
        alp[i],alp[j] = alp[j],alp[i]
    return alp

# A8 ==> 00A8. hex num to 4 len
def to4(t):
    for _ in range(4 - len(t)):
        t = '0' + t
    return t

def isrgb(pic):
    try:
        (r,g,b) = pic.getpixel((0,0))
        return True
    except:
        return False

# true-random color
def randclr():
    return tuple(i % 255 for i in unpack('iii', os.urandom(12)))
intence = max
def setintence(pxl,val):
    maxi = 0
    maxv = pxl[0]
    for i in range(1,3):
        if pxl[i] > maxv:
            maxv = pxl[i]
            maxi = i
    coef = (val / maxv) * 0.99
    if maxi == 0:
        return (val, int(pxl[1] * coef), int(pxl[2] * coef))
    elif maxi == 1:
        return (int(pxl[0] * coef), val, int(pxl[2] * coef))
    else:
        return (int(pxl[0] * coef), int(pxl[1] * coef), val)
    #assert intence(pix) == val
    #return pix

# making dict {symbol: index}
def sym_indexer(key):
    seq = shuffle(int(key, 16), len(alphabet))
    return dict(zip(seq, range(len(seq))))

# making dict {index:symbol}
def indexer_sym(key):
    seq = shuffle(int(key, 16), len(alphabet))
    return dict(zip(range(len(seq)), seq))

class PixelWalker(object):
    def __init__(self,key,w,h):
        self.key = key
        mkey = md5(key)
        self.sind   = sym_indexer(mkey[:4])
        self.inds   = indexer_sym(mkey[:4])
        self.randx  = Random(prims[int(mkey[12:15], 16)])
        self.kind   = 0
        self.klen   = len(key)
        self.w      = w
        self.h      = h
        self.wh     = w * h
        self.idx    = set()
        self.idy    = set()
    def chstate(f):
        def res(self,*args):
            ans = f(self,*args)
            self.kind = (self.kind + 1) % self.klen
            return ans
        return res
    @chstate
    def getc(self,pic):
        passym  = self.key[self.kind] 
        crd     = self.randx.nextid(self.wh, self.idx)
        y       = int(crd / self.w)
        x       = crd % self.w
        pixel   = pic[x,y]
        try:
            return self.inds[intence(pixel) ^ alphaind[passym]]
        except:
            raise DecodeError()
    @chstate
    def putc(self,pic,sym):
        crd = self.randx.nextid(self.wh, self.idx)
        y   = int(crd / self.w)
        x   = crd % self.w
        pixel = pic[x,y]
        passym = self.key[self.kind]
        pic[x,y] = setintence(pixel, self.sind[sym] ^ alphaind[passym])
#    @chstate
#    def getpixel(self,pic):
#        x = self.randx()
#        y = self.randy()
#        clr = pic[x,y]
#        self.randc()
#    @chstate
#    def putpixel(self,pic,sym):
#        indexer = self.randc()
#        pic[self.randx(), self.randy()] = indexer[sym] ^ self.key[self.kind]

def encrypt(key,textfile,picn,rand_pic_size,salt,isbin):
    if rand_pic_size is None:
        pic = Image.open(picn)
        if not isrgb(pic):
            pic = pic.convert('RGB')
        w = pic.size[0]
        h = pic.size[1]
        px = pic.load()
        if not (salt is None):
            saltc = int(w * h * (salt / 100))
            for i in range(saltc):
                xyv = unpack('iii', os.urandom(12))
                x = xyv[0] % w
                y = xyv[1] % h
                px[x,y] = setintence(px[x,y], xyv[2] % 255)
                if i % 100 == 0:
                    print('salt: %d of %d: %f%%' % (i, saltc, int(i * 100 / saltc)))
    else:
        pic = Image.new('RGB', rand_pic_size, 'white')
        w = pic.size[0]
        h = pic.size[1]
        px = pic.load()
        for x in range(w):
            for y in range(h):
                px[x,y] = randclr()#(randclr(), randclr(), randclr())
    walker = PixelWalker(key,w,h)
    if isbin:
        with open(textfile, 'rb') as hdr:
            txt = b2a_base64(hdr.read()).decode('utf8')
    else:
        with open(textfile, 'rt') as hdr:
            txt = hdr.read()
    tlen = to4(hex(len(txt))[2:])
    signal = md5(key)
    if w * h <= len(txt) + len(tlen) + len(signal):
        print('image too small')
        return
    px = pic.load()
    txt = signal + tlen + txt
    for c in txt:
        walker.putc(px, c)
    if rand_pic_size is None:
        pic.save(picn + '.cr.png', 'PNG')
    else:
        pic.save(picn)
    print('ok %s' % len(txt))

def decrypt(key,textfile,picn,isbin):
    pic = Image.open(picn)
    if not isrgb(pic):
        pic.convert('RGB')
    w = pic.size[0]
    h = pic.size[1]
    walker = PixelWalker(key,w,h)
    px = pic.load()
    signal = md5(key)
    testsignal = reduce(str.__add__, (walker.getc(px) for _ in range(len(signal))))
    if testsignal != signal:
        print('signal error:\n%s\n%s' % (testsignal, signal))
        return
    try:
        tlen = int(reduce(str.__add__, (walker.getc(px) for _ in range(4))), 16)
    except:
        raise DecodeError()
    if isbin:
        buffile = os.path.join(os.path.dirname(textfile), '__buf__123456789')
        with open(buffile, 'wt') as hdr:
            for _ in range(tlen):
                hdr.write(walker.getc(px))
        print('buf ok, decoding base64')
        with open(textfile, 'wb') as out:
            with open(buffile, 'rt') as hdr:
                out.write(a2b_base64(hdr.read().encode('utf8')))
        os.remove(buffile)
    else:
        with open(textfile, 'wt') as hdr:
            for _ in range(tlen):
                hdr.write(walker.getc(px))
    print('ok %s' % (len(signal) + 4 + tlen))

parser = argparse.ArgumentParser('steganography')
parser.add_argument('-k', help='key password')
parser.add_argument('-f', help='text file')
parser.add_argument('-p', help='picture')
parser.add_argument('-g', help='generate picture with size. Example "-g 100x500"')
parser.add_argument('-s', help='add salt(percent)')
parser.add_argument('-x', default=False, action='store_true', help='decrypt')
parser.add_argument('-b', default=False, action='store_true', help='message binary')
args = parser.parse_args()

if args.k is None or args.f is None or args.p is None:
    print('bad args')
else:
    if args.x:
        try:
            decrypt(args.k, args.f, args.p, args.b)
        except DecodeError:
            print('can not decrypt')
            sys.exit(1)
    else:
        if args.g is None:
            if args.s:
                salt = 0
                try:
                    salt = float(args.s)
                    assert(salt > 0 and salt < 100)
                except:
                    print('salt is not number in (0 .. 100)')
                    sys.exit(1)
                encrypt(args.k, args.f, args.p, None, salt, args.b)
            else:
                encrypt(args.k, args.f, args.p, None, None, args.b)
        else:
            sz = args.g.split('x')
            sz = (int(sz[0]), int(sz[1]))
            encrypt(args.k, args.f, args.p, sz, None, args.b)
