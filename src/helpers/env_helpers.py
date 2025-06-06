from IPython import get_ipython
from plotly.io import renderers


class _Env:
	def __init__(self):
		# TODO COLAB | LOCAL, IPYNB | PY ?
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


def setup_plotly():
	if ENV.COLAB:
		renderers.default = 'colab'
	else:
		renderers.default = 'svg'
		print(f"Non-colab plotly renderer is set to: {renderers.default}")

