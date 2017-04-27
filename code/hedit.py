
import sys

filename = sys.argv[1]

ra = float(sys.argv[2]) + float(sys.argv[3])/60 + float(sys.argv[4])/3600
dec = (abs(float(sys.argv[5])) + float(sys.argv[6])/60 + float(sys.argv[7])/3600)*(1 - 2*int(sys.argv[5][:1] == '-'))

scale = float(sys.argv[8])/3600

try:
    rot = float(sys.argv[9])
except:
    rot = 0

try:
    flip = int(sys.argv[10])
except:
    flip = 0

from apex.io import *
from apex.astrometry import Simple_Astrometry

im = imread(filename)
im.wcs = Simple_Astrometry(ra, dec, im.width/2.0, im.height/2.0,
                           (2*flip - 1)*scale, scale, rot)
imwrite(im, im.filename)
