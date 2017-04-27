from apex.io import *
from apex.astrometry import Simple_Astrometry

def edit_header_coords_info(filename, ra_str, dec_str, scale_sec_pix, frame_rotation=0, flip=0, ra_dec_delim=' '):
    ra_list = [float(ra) for ra in ra_str.split(ra_dec_delim)]
    dec_list = [float(dec) for dec in dec_str.split(ra_dec_delim)]
    # TODO: check if ra and dec lists are correct
    
    ra = ra_list[0] + ra_list[1]/60. + ra_list[2]/3600.
    dec = (abs(dec_list[0]) + dec_list[1]/60. + dec_list[2]/3600.) * (-1. if dec_list[0] < 0 else 1.)
    scale = float(scale_sec_pix)/3600.

    im = imread(filename)
    im.wcs = Simple_Astrometry(ra, dec, im.width/2.0, im.height/2.0,
                               (2*flip - 1)*scale, scale, frame_rotation)
    imwrite(im, im.filename)
