
def edit_header_coords_info(filename, ra_str, dec_str, scale_sec_pix, frame_rotation=0, flip=0, ra_dec_delim=' '):
	from apex.io import *
	from apex.astrometry import Simple_Astrometry
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

def list_contains(small, big):
	for i in xrange(len(big) - len(small) + 1):
		for j in xrange(len(small)):
			if big[i+j] != small[j]:
				break
		else:
			return i, i + len(small)
	return False

def to_ext_format(ext):
	if ext and not ext.startswith('.'):
		ext = '.' + ext
	return ext

def exts_list(filename):
	import os
	base, ext = os.path.splitext(filename)
	print os.path.splitext(filename)
	res = [ext]
	while ext:
		base, ext = os.path.splitext(base)
		res.append(ext)
	if '' in res:
		res.remove('')
	return res

def ext_split(ext):
	return [to_ext_format(e) for e in to_ext_format(ext).split('.')][1:]

def change_file_extension(filename, new_ext=None, only_last_ext=False):
	import os
	if new_ext is None:
		return filename
	base, ext = os.path.splitext(filename)
	while not only_last_ext and ext:
		base, ext = os.path.splitext(base)
	base += to_ext_format(new_ext)
	return base

def change_file_path(filepath, new_path=None):
	import os
	if new_path is None:
		return filepath
	path, filename = os.path.split(filepath)
	return os.path.join(new_path, filename)

def build_filenames_list(names, **kwargs):
	new_path = None if 'new_path' not in kwargs else kwargs['new_path']
	new_ext = None if 'new_ext' not in kwargs else kwargs['new_ext']
	filenames_list = names if isinstance(names, list) else [names]
	return [change_file_path(change_file_extension(filename, new_ext), new_path) for filename in filenames_list]

# function returns list of filenames with specified format in directory
# TODO: implement separate functions for tech frames search (needed for tech frames preprocessing step)
# TODO: define naming convention for super tech frames
# TODO: support os.walk (nested dirs) flag
def get_fits_images_from_dir(directory, files_exts=['.fits'], only_last_ext=True, ignore_case=True):
	import os
	from re import search, IGNORECASE
	res = []
	files_exts = files_exts if isinstance(files_exts, list) else [files_exts]
	for files_ext in files_exts:
		ext = to_ext_format(files_ext)
		exts = [to_ext_format(e) for e in ext.split('.')[1:]]
		filenames = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
		if only_last_ext:
			filenames = [f for f in filenames if search(''.join(exts) + '$', f, ignore_case*IGNORECASE) is not None]
		else:
			exts = exts[::-1]
			to_remove = []
			for filename in filenames:
				filename_exts = exts_list(filename)
				if len(exts) > len(filename_exts):
					to_remove.append(filename)
				else:
					small = [e.lower() for e in exts] if ignore_case else exts
					big = [fe.lower() for fe in filename_exts] if ignore_case else filename_exts
					if not list_contains(small, big):
						to_remove.append(filename)
			for tr in to_remove:
				filenames.remove(tr)
		res.extend(filenames)
	return res

