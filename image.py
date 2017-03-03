import argparse
from PIL import Image
from functools import reduce
import hashlib

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
prims = _prims(5000)

class Random:
    def __init__(self,n0):#,ia,ib):
        self.n = n0
        self.M = prims[2050] * prims[3000]
    def __iter__(self):
        return self
    def __next__(self):
        if self.n == 0:
            self.n = int(self.M * 0.7)
        self.n = (self.n * self.n) % self.M
        return self.n
    def nextid(self, rng, idl):
        ''' return val witch is not in set 'idl' and put it to 'idl' '''
        for i in self:
            val = i % rng
            if not (val in idl):
                idl.add(val)
                return val

alphabet = ['\n','\t'] + [chr(i) for i in range(32, 127)] + [chr(i) for i in range(ord('А'),ord('ё'))]
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

def encrypt(key,textfile,picn):
    pic = Image.open(picn)
    if not isrgb(pic):
        pic = pic.convert('RGB')
    w = pic.size[0]
    h = pic.size[1]
    # making ind map
    #def to(oldmax, newmax):
    #    return lambda x: int((x / oldmax) * newmax)
    mkey = md5(key)
    seqc = shuffle(prims[int(mkey[:3], 16)], len(alphabet))
    randx = Random(prims[int(mkey[3:6], 16)])
    randy = Random(prims[int(mkey[6:9], 16)])
    redind = dict(zip(seqc, range(len(seqc))))
    with open(textfile, 'rt') as hdr:
        txt = hdr.read()
    tlen = to4(hex(len(txt))[2:])
    #acc = []
    xl = set()
    yl = set()
    px = pic.load()
    for c in (signal + tlen + txt):
        x = randx.nextid(w, xl)
        y = randy.nextid(h, yl)
        #xl.add(x)
        #yl.add(y)
        (r,g,b) = px[x,y]
        px[x,y] = (redind[c], g, b)
        #acc.append((x,y,redind[c]))
    pic.save(picn + '.cr.png', 'PNG')
    print('ok')

def decrypt(key,textfile,picn):
    pic = Image.open(picn)
    if not isrgb(pic):
        pic.convert('RGB')
    w = pic.size[0]
    h = pic.size[1]
    mkey = md5(key)
    seqc = shuffle(prims[int(mkey[:3], 16)], len(alphabet))
    randx = Random(prims[int(mkey[3:6], 16)])
    randy = Random(prims[int(mkey[6:9], 16)])
    redind = dict(zip(range(len(seqc)), seqc))
    xl = set()
    yl = set()
    def sym():
        x = randx.nextid(w, xl)
        y = randy.nextid(h, yl)
        try:
            return redind[px[x, y][0]]
        except:
            return '\0'
    px = pic.load()
    testsignal = reduce(str.__add__, (sym() for _ in range(len(signal))))
    if testsignal != signal:
        print('signal error: "%s"' % testsignal)
        return
    try:
        tlen = int(reduce(str.__add__, (sym() for _ in range(4))), 16)
    except:
        print('grab len error')
        return
    with open(textfile, 'wt') as hdr:
        for _ in range(tlen):
            hdr.write(sym())
    print('ok')

parser = argparse.ArgumentParser('steganography')
parser.add_argument('-k', help='key password')
parser.add_argument('-f', help='text file')
parser.add_argument('-p', help='picture')
parser.add_argument('-x', default=False, action='store_true', help='decrypt')
#parser.add_argument('-c', default='0.$.$:ff.$.$', help='color range for crypt (<min>:<max> where color is r.g.b where $ is "use original color component")')
args = parser.parse_args()

if args.k is None or args.f is None or args.p is None:
    print('bad args')
else:
    if args.x:
        decrypt(args.k, args.f, args.p)
    else:
        encrypt(args.k, args.f, args.p)
