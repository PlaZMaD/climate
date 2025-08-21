import os
import sys
from pathlib import Path

from IPython import get_ipython


class _Env:
	def __init__(self):
		# TODO 3 add local ipynb? (COLAB | LOCAL, IPYNB | PY)
		try:
			import google.colab
		except ImportError:
			self.COLAB = False
		else:
			self.COLAB = True

		self.LOCAL = not self.COLAB
		self.IPYNB: bool = get_ipython()


ENV = _Env()


def ipython_only(func):
	def wrapper(*args, **kwargs):
		if ENV.IPYNB:
			return func(*args, **kwargs)
		else:
			print(f"IPython env not detected. {func.__name__} is skipped by design.")
			return None

	return wrapper


def colab_only(func):
	def wrapper(*args, **kwargs):
		if ENV.COLAB:
			return func(*args, **kwargs)
		else:
			print(f"Colab env not detected. {func.__name__} is skipped by design.")
			return None

	return wrapper


def setup_r():
	if ENV.LOCAL:
		env_folder = Path(sys.executable).parent
		r_folder = env_folder / 'Lib/R'
		assert r_folder.exists()
		os.environ['R_HOME'] = str(r_folder)
	else:
		# something different, but it works
		# print(f"Google colab auto sets R_HOME to: {os.environ['R_HOME']}")
		pass