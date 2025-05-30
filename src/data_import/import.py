from enum import Enum


class ImportMode(Enum):
	# Тип файлов для импорта: 'CSF-1', 'IAS-1', 'EDDY-1'
	CSF1 = 1
	IAS1 = 2
	EDDY1 = 3
