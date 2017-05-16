import sys
import os
import datetime
import errno
import json


# TODO: add remove dirs tree method (to remove dirs tree as temorary, when pipeline stage is done on spark executor)
class AEDirsTreeConfigurer:

	def __init__(self, check_dirs_existance=False, dirs_tree_root='.', **kwargs):

		# declare non-setable class attributes
		self._class_non_setable_attrs = ['_attr_prefix', '_cur_path', '_paths_names']
		self._cur_path = os.getcwd()
		self._attr_prefix = '_'
		self._paths_names = ['catalogs', 'logs', 'temp', 'images', 'config', 'stacks']

		# declare class attributes and first init
		self._exec_mode = ''
		self._wrk_path = None
		#self._cur_timestamp = None
		self._logs_timestamp = None
		self._dirname_delim = '_'
		self._paths = None
		self._log_paths = []

		# init strictly valued attrs (may be reinitialized later in this __init__)
		#self._update_cur_timestamp()
		self._update_logs_timestamp()

		# check check_dirs_existance argument type and set it if ok
		if isinstance(check_dirs_existance, bool):
			self._check_dirs_existance = check_dirs_existance
		else:
			raise TypeError('check_dirs_existance argument must have bool type, but '
									   + type(check_dirs_existance).__name__ + ' typed value specified')

		# check if kwargs contains only supported args
		class_setable_attrs = {attr for attr in dir(self) if not callable(getattr(self, attr)) and
					   not attr.startswith('__')} - set(self._class_non_setable_attrs)
		class_setable_attrs = {attr.lstrip(self._attr_prefix) for attr in class_setable_attrs}
		paths_attrs = {'%s_path' % name for name in self._paths_names}
		kwargs_setable_attrs = class_setable_attrs | paths_attrs
		kwargs_attrs = {kwarg for kwarg in kwargs}
		err_attrs = (kwargs_setable_attrs | kwargs_attrs) - kwargs_setable_attrs
		if err_attrs:
			raise AttributeError('argument' + ('s ' if len(err_attrs) > 1 else ' ') + ', '.join(err_attrs)
								 + ' passed, but no attributes exist for it')

		# check not None kwargs
		for kwarg in kwargs:
			if kwargs[kwarg] is not None:
				# check if str args are actually str typed
				if kwarg.endswith('_mode') \
				or kwarg.endswith('_path') \
				or kwarg.endswith('_timestamp') \
				or kwarg.endswith('_delim'):
					if not isinstance(kwargs[kwarg], str):
						raise TypeError(kwarg + ' argument must have str type, but '
									   + type(kwargs[kwarg]).__name__ + ' typed value specified')
				# check if path args are valid pathnames
				if kwarg.endswith('_path') and not self._is_pathname_valid(kwargs[kwarg]):
					raise ValueError('value \"' + kwargs[kwarg] + '\" for argument ' + kwarg
										 + ' is not a valid pathname')
				# check paths kwarg, if it is
				if kwarg == 'paths':
					# check paths, its keys and values types
					if not isinstance(kwargs[kwarg], dict):
						raise TypeError(kwarg + ' argument must have dict type, but '
									   + type(kwargs[kwarg]).__name__ + ' typed value specified')
					for k, v in kwargs[kwarg].iteritems():
						if not isinstance(k, str):
							raise TypeError('keys for paths dict must have str type, but '
									   + type(k).__name__ + ' typed value specified')
						if not isinstance(v, str):
							raise TypeError('values for paths dict must have str type, but '
									   + type(v).__name__ + ' typed value specified')
					# check paths keys
					paths_keys = set(kwargs[kwarg].keys())
					err_paths_keys = (set(self._paths_names) | paths_keys) - set(self._paths_names)
					if err_paths_keys:
						raise KeyError('key' + ('s ' if len(err_paths_keys) > 1 else ' ')
									   + ', '.join(err_paths_keys)
									   + (' are' if len(err_paths_keys) > 1 else ' is')
									   + ' wrong')
					# check paths values
					for k, v in kwargs[kwarg].iteritems():
						if not self._is_pathname_valid(v):
							raise ValueError('value ' + v + ' for key ' + k + ' is not a valid pathname')


		# init class attrs if it set directly in kwargs (paths dict will be initialized later)
		for kwarg in kwargs:
			if kwarg != 'paths' and hasattr(self, self._attr_prefix + kwarg) and kwargs[kwarg] is not None:
				setattr(self, self._attr_prefix + kwarg, kwargs[kwarg])

		# build wrk_path
		if not self._wrk_path:
			self._wrk_path = self._cur_path
		else:
			self._wrk_path = self._build_path(self._cur_path, self._wrk_path)

		# set default paths to work dirs
		self._paths = {
			'temp': os.path.join(self._wrk_path, 'temp'),
			'logs': os.path.join(self._wrk_path, 'logs'),
			'config': os.path.join(self._wrk_path, 'config'),
			'catalogs': os.path.join(self._wrk_path, 'catalogs'),
			'stacks': os.path.join(self._wrk_path, 'stacks'),
			'images': os.path.join(self._wrk_path, 'images')
				}

		# set paths dict or its part from kwargs, if specified
		if 'paths' in kwargs:
			if kwargs['paths']:
				for k, v in kwargs['paths'].iteritems():
					self._paths[k] = self._build_path(self._wrk_path, v)

		# set paths to work dirs from kwargs, if specified
		for kwarg in kwargs.keys():
			paths_dir = kwarg.replace('_path', '')
			if paths_dir in self._paths:
				pathname = kwargs[kwarg]
				self._paths[paths_dir] = self._build_path(self._wrk_path, pathname)

	def _update_logs_timestamp(self):
		self._logs_timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

	def _build_dir_name(self, *args, **kwargs):
		delim = '_'
		if 'delim' in kwargs:
			delim = kwargs['delim']
		res = ''
		for arg in args:
			if arg:
				res += arg + delim
		return res.rstrip(delim)

	def _is_pathname_valid(self, pathname):
		try:
			if not isinstance(pathname, str) or not pathname:
				return False

			_, pathname = os.path.splitdrive(pathname)
			root_dirname = os.environ.get('HOMEDRIVE', 'C:') if sys.platform == 'win32' else os.path.sep
			assert os.path.isdir(root_dirname)
			root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

			for pathname_part in pathname.split(os.path.sep):
				try:
					os.lstat(root_dirname + pathname_part)
				except OSError as os_err:
					if hasattr(os_err, 'winerror'):
						if os_err.winerror == ERROR_INVALID_NAME:
							return False
					elif os_err.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
						return False
		except TypeError:
			return False
		else:
			return True

	def _is_dir_writeable(self, pathname, base=None):
		dirname = os.path.dirname(pathname) or (base if base else self._wrk_path)
		return os.access(dirname, os.W_OK)

	def _is_dir_exists(self, pathname, check_pathname=True):
		try:
			return (True if not check_pathname else self._is_pathname_valid(pathname)) \
					and os.path.isdir(pathname)
		except OSError:
			return False

	def _create_dir(self, pathname, check_pathname=True, check_exist=False):
		try:
			if check_pathname:
				if not self._is_pathname_valid(pathname):
					raise ValueError('cannot create dir: pathname is not valid')
			os.makedirs(pathname)
		except OSError as os_err:
			if check_exist and os_err.errno == errno.EEXIST or os_err.errno != errno.EEXIST:
				raise

	def _build_path(self, base, pathname):
		return pathname if os.path.isabs(pathname) else os.path.join(base, pathname)

	def build_dirs_tree(self):
		# create dirs tree for application according to paths dict
		for path in self._paths:
			self._create_dir(self._paths[path], True, self._check_dirs_existance)

	def get_exec_mode(self):
		return self._exec_mode

	def set_exec_mode(self, new_exec_mode):
		if isinstance(new_exec_mode, str):
			self._exec_mode = new_exec_mode
		else:
			raise TypeError('exec_mode attribute has str type, but passed argument has type ' + \
							 type(new_exec_mode).__name__)
		return self._exec_mode

	def get_paths(self):
		return self._paths

	def get_paths_dir_names(self):
		return self._paths_names

	def new_log_dir(self, check_exist=True):
		self._update_logs_timestamp()
		self._log_paths.append(os.path.join(self._paths['logs'],
											self._build_dir_name(self._exec_mode, 'log',
																 self._logs_timestamp,
																 delim=self._dirname_delim)))
		self._create_dir(self._log_paths[-1], False, check_exist)
		return self._log_paths[-1]

	def get_last_log_dir(self):
		return self._log_paths[-1]

	def get_dir(self, dirname):
		return self._paths[dirname]



# TODO: check json configs, also see paper notes, (*) and (**) notes
class AEJsonConfigLoader:
	def __init__(self, common_config, **kwargs):
		self._required_common_params = {'config_files': ['pipeline_config']}
		self._configs = {}
		self._common_config = common_config
		with open(common_config, 'rb') as fid:
			self._configs['common_config'] = json.load(fid)

	def _check_common_config(self):
		for common_param in self._required_common_params:
			if common_param not in self._configs['common_config']:
				raise KeyError(common_param + ' param is not set in ' + self._common_config + 'config file')
			if not isinstance(self._required_common_params[common_param], list):
				param_list = [self._required_common_params[common_param]]
			else:
				param_list = self._required_common_params[common_param]
			for param in param_list:
				if param not in self._configs['common_config'][common_param]:
					raise KeyError(param + ' param is not set in ' + self._common_config + 'config file')

	def get_required_common_params(self):
		return self._required_common_params

	def get_common_config(self):
		return self._configs['common_config']

	def get_pipeline_config(self):
		return self._configs['pipeline_config']

	def get_configs(self):
		return self._configs

	def extend_required_common_params(self, common_param, params, override=False):
		if not override and common_param in self._required_common_params:
			if not isinstance(params, list):
				params = [params]
			for param in params:
				if param not in self._required_common_params[common_param]:
					if not isinstance(self._required_common_params[common_param], list):
						self._required_common_params[common_param] = [self._required_common_params[common_param]]
					self._required_common_params[common_param].append(param)
		else:
			self._required_common_params[common_param] = params if isinstance(params, list) else [params]
		self._check_common_config()

	def add_required_config(self, config_name):
		self.extend_required_common_params('config_files', config_name, False)

	def build_config(self):
		config_names = [config_name for config_name in self._configs['common_config']['config_files'].keys()]
		for config_name in config_names:
			with open(self._configs['common_config']['config_files'][config_name], 'rb') as fid:
				self._configs[config_name] = json.load(fid)

