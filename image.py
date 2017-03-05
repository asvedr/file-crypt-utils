#!/usr/bin/env python3
import argparse
from PIL import Image
from functools import reduce
from struct import unpack
import hashlib
import random
import time
import os

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

class RandomLoop(Exception):
    pass

class Random:
    def __init__(self,n0):#,ia,ib):
        self.n = n0
        self.A = 2050
        self.B = 4000
        self.initM()
        #self.M = prims[5000] * prims[4999]
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

alphabet = ['\n','\t'] + [chr(i) for i in range(32, 127)] + [chr(i) for i in range(ord('А'),ord('ё'))]
alphaind = dict(zip(alphabet, range(len(alphabet))))
signal = 'ok'

def md5(s):
    m = hashlib.md5()
    m.update(s.encode('utf8'))
    return m.hexdigest()

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

#randclr = lambda: random.randint(0,255)
def randclr():
    return tuple(i % 255 for i in unpack('iii', os.urandom(12)))
    #return abs(unpack('i', os.urandom(4))[0]) >> 8
def sym_indexer(key):
    seq = shuffle(int(key, 16), len(alphabet))
    return dict(zip(seq, range(len(seq))))
def indexer_sym(key):
    seq = shuffle(int(key, 16), len(alphabet))
    return dict(zip(range(len(seq)), seq))

class PixelWalker(object):
    def __init__(self,key,w,h):
        self.key = key
        mkey = md5(key)
        self.sind   = sym_indexer(mkey[:4])# (
                #sym_indexer(mkey[:4])#,
                #sym_indexer(mkey[4:8]),
                #sym_indexer(mkey[8:12])
            #)
        self.inds   = indexer_sym(mkey[:4])# (
                #indexer_sym(mkey[:4])#,
                #indexer_sym(mkey[4:8]),
                #indexer_sym(mkey[8:12])
            #)
        self.randx1 = Random(prims[int(mkey[12:15], 16)])
        self.randx2 = Random(prims[int(mkey[15:18], 16)])
        self.randy1 = Random(prims[int(mkey[18:21], 16)])
        self.randy2 = Random(prims[int(mkey[21:24], 16)])
        self.kind   = 0
        self.klen   = len(key)
        self.w      = w
        self.h      = h
        self.wh     = w * h
        self.idx    = set()
        self.idy    = set()
    def randx(self):
        #if alphaind[self.key[self.kind]] % 2 == 0:
            return self.randx1
        #else:
        #    return self.randx2
    #def randy(self):
        #if alphaind[self.key[self.klen - self.kind - 1]] % 2 == 0:
        #    return self.randy1
        #else:
        #    return self.randy2
    def getc(self,pic):
        passym  = self.key[self.kind] 
        ind     = alphaind[passym] % 3
        crd     = self.randx().nextid(self.wh, self.idx)
        y       = int(crd / self.w)
        x       = crd % self.w
        pixel   = pic[x,y]#pic[self.randx().nextid(self.w, self.idx), self.randy().nextid(self.h, self.idy)]
        return self.inds[pixel[ind] ^ alphaind[passym]]
    def putc(self,pic,sym):
        #x = self.randx().nextid(self.w, self.idx)
        #y = self.randy().nextid(self.h, self.idy)
        crd = self.randx().nextid(self.wh, self.idx)
        y   = int(crd / self.w)
        x   = crd % self.w
        pixel = pic[x,y]
        passym = self.key[self.kind]
        ind    = alphaind[passym] % 3
        def cval():
            return self.sind[sym] ^ alphaind[passym]
        if ind == 0:
            pic[x,y] = (cval(), pixel[1], pixel[2])
        elif ind == 1:
            pic[x,y] = (pixel[0], cval(), pixel[2])
        else:
            pic[x,y] = (pixel[0], pixel[1], cval())
    #@staticmethod
    def chstate(f):
        def res(self,*args):
            f(self,*args)
            self.kind = (self.kind + 1) % self.klen
        return res
    @chstate
    def getpixel(self,pic):
        x = self.randx()
        y = self.randy()
        clr = pic[x,y]
        self.randc()
    @chstate
    def putpixel(self,pic,sym):
        indexer = self.randc()
        pic[self.randx(), self.randy()] = indexer[sym] ^ self.key[self.kind]

def encrypt(key,textfile,picn,rand_pic_size,salt):
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
                xy = unpack('ii', os.urandom(8))
                x = xy[0] % w
                y = xy[1] % h
                px[x,y] = randclr()
                if i % 100 == 0:
                    print('salt: %d of %d: %f%%' % (i, saltc, int(i * 100 / saltc)))
    else:
        pic = Image.new('RGB', rand_pic_size, 'white')
        #random.seed(time.time())
        w = pic.size[0]
        h = pic.size[1]
        px = pic.load()
        for x in range(w):
            for y in range(h):
                px[x,y] = randclr()#(randclr(), randclr(), randclr())
    walker = PixelWalker(key,w,h)
    with open(textfile, 'rt') as hdr:
        txt = hdr.read()
    tlen = to4(hex(len(txt))[2:])
    if w * h <= len(txt) + len(tlen) + len(signal):
        print('image too small')
        return
    #xl = set()
    #yl = set()
    px = pic.load()
    #i = 0
    txt = signal + tlen + txt
    for c in txt:
        #if i % 20 == 0:
            #print('%s%%' % (float(i) / len(txt) * 100))
        walker.putc(px, c)
        #i += 1
    if rand_pic_size is None:
        pic.save(picn + '.cr.png', 'PNG')
    else:
        pic.save(picn)
    print('ok %s' % len(txt))

def decrypt(key,textfile,picn):
    pic = Image.open(picn)
    if not isrgb(pic):
        pic.convert('RGB')
    w = pic.size[0]
    h = pic.size[1]
    walker = PixelWalker(key,w,h)
    px = pic.load()
    testsignal = reduce(str.__add__, (walker.getc(px) for _ in range(len(signal))))
    if testsignal != signal:
        print('signal error: "%s"' % testsignal)
        return
    try:
        tlen = int(reduce(str.__add__, (walker.getc(px) for _ in range(4))), 16)
    except:
        print('grab len error')
        return
    with open(textfile, 'wt') as hdr:
        for _ in range(tlen):
            hdr.write(walker.getc(px))
    print('ok %s' % (len(signal) + 4 + tlen))

parser = argparse.ArgumentParser('steganography')
parser.add_argument('-k', help='key password')
parser.add_argument('-f', help='text file')
parser.add_argument('-p', help='picture')
parser.add_argument('-g', help='generate picture with size. Example "-g 100x500"')
parser.add_argument('-gray', default=False, action='store_true', help='use grayscale')
parser.add_argument('-s', help='add salt(percent)')
parser.add_argument('-x', default=False, action='store_true', help='decrypt')
#parser.add_argument('-c', default='0.$.$:ff.$.$', help='color range for crypt (<min>:<max> where color is r.g.b where $ is "use original color component")')
args = parser.parse_args()

if args.k is None or args.f is None or args.p is None:
    print('bad args')
else:
    if args.x:
        decrypt(args.k, args.f, args.p)
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
                encrypt(args.k, args.f, args.p, None, salt)
            else:
                encrypt(args.k, args.f, args.p, None, None)
        else:
            sz = args.g.split('x')
            sz = (int(sz[0]), int(sz[1]))
            encrypt(args.k, args.f, args.p, sz, None)
