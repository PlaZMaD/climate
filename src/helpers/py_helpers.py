import contextlib
import sys


@contextlib.contextmanager
def catch(on_exception=None, err_types=Exception):
	if not err_types:
		yield
		return

	try:
		yield
	except err_types as e:
		if on_exception:
			on_exception(e)


def invert_dict(dict):
	return {v: k for k, v in dict.items()}


def fix_strs_case(strs: list[str], correct_case: list[str]):
	correct_l_to_correct = {c.lower(): c for c in correct_case}
	assert len(correct_l_to_correct) == len(correct_case), \
		'Possibly correct_case contains duplicates with different cases'

	missing = [c for c in strs if c.lower() in correct_l_to_correct]
	new_strs = [correct_l_to_correct.get(c.lower(), c) for c in strs]
	renames = [(s, n) for s, n in zip(strs, new_strs) if s != n]
	return new_strs, renames, missing


def debug_stdout_to_log(debug_log_fpath):
	class Logger(object):
		def __init__(self):
			self.terminal = sys.stdout
			self.log = open(debug_log_fpath, "w")

		def write(self, message):
			self.terminal.write(message)
			self.log.write(message)

		def flush(self):
			# this flush method is needed for python 3 compatibility.
			# this handles the flush command by doing nothing.
			# you might want to specify some extra behavior here.
			pass

	sys.stdout = Logger()
