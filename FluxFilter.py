# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% [markdown] id="pqQVYpfkwA8E"
# # **FluxFilter**

# %% [markdown] id="oE87fcFbwlIu"
# ## **Введение**
# Этот скрипт разработан для постобработки - визуализации, фильтрации и заполнения - 30-минутных данных эколого-климатических станций, полученных методом турбулентных пульсаций (eddy covariance). Скрипт может использоваться в качестве инструмента для получения достоверных кумулятивных сумм экосистемных потоков тепла и СО2. Входными параметрами являются: данные об экосистемных потоках с шагом по времени 30 минут, рассчитанные из высокочастотных данных, с диагностическими показателями, а также метеопараметры с разрешением по времени 30 минут. Основное назначение скрипта: дообработка данных эколого-климатических станций 1-го уровня обработки с целью получения данных уровней обработки 2, 3 и 4.
# * Под уровнем 1 подразумеваются потоки, рассчитанные в специализированном программном обеспечении с использованием общепринятых процедур фильтрации и коррекции (например, выходной файл full output программы EddyPro, LI-COR Inc., США) и метеорологические данные с шагом осреднения в 30 минут.
# * Под уровнем 2 подразумеваются незаполненные 30-минутные данные, ответственный за станцию исключает периоды заведомо плохой работы приборов (т.е. данные за эти периоды заполнены кодом пропуска -9999). Такие данные собираются для Информационно-Аналитической системы (ИАС "Углерод-Э", разработчик Институт Космических Исследований РАН).
# * Под уровнем 3 подразумеваются данные уровня 2, также незаполненные, но прошедшие тщательную фильтрацию на основе физических, статистических критериев.
# * Под уровнем 4 подразумеваются заполненные данные.
#
# *Для запуска достаточно нажать в Google Colab "Среда выполнения - Выполнить все"*  
# *Самая новая версия скрипта находится в репозитории https://github.com/PlaZMaD/climate/releases*  
#
# ## **Входные файлы**
# Для работы скрипта требуются ряды фильтруемых и заполняемых турбулентных потоков, а также метеорологических переменных, которые позволяют отфильтровать и заполнить потоки. Ряды могут быть загружены из двух разных файлов или из одного файла.
# Скрипт поддерживает следующие варианты входных файлов:
# 1) выходной файл EddyPro - full output (см. [мануал EddyPro](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) для потоков
# 2) выходной файл CSF программы EasyFlux DL, Campbell Scientific Ink., для потоков. Файлы full output и CSF взаимно заменяемы
# 3) biomet-файл в формате, описанном в руководстве EddyPro (см. [его же](https://licor.app.boxenterprise.net/s/1ium2zmwm6hl36yz9bu4)) для метеорологических переменных. Если потоки загружены из файлов full output или CSF, файл biomet желателен для надежных фильтраций и заполнений потоков. Однако при отсутствии метеорологических переменных возможен запуск скрипта только с файлами full output либо CSF
# 4) или только файл в формате ИАС, содержащий и потоки, и метеорологические переменные
# 5) Опционально можно загрузить файл конфигурации (настройки всех параметров FluxFilter).
# В случае запуска full output+biomet или CSF+biomet турбулентные потоки и u* берутся из файла full output/CSF, а все метеорологические переменные (температура и относительная влажность воздуха и т.д.) берутся из файла biomet. Основные требования ко входным файлам:
# *   Файлы должны быть в формате .csv (текстовый файл, разделенный запятыми).
# *   Заголовки столбцов в файлах full output и biomet должны быть строго по руководству EddyPro, в скрипте переменные идентифицируются по названиям колонок (co2_flux для потока CO2 в full output, Ta_1_1_1 для температуры воздуха в biomet и т.д.).
# *   Код пропуска во входных файлах должен быть -9999
# *   Единицы для переменных файла biomet должны быть как основные единицы для файла biomet по руководству EddyPro. Исключение: температура воздуха/почвы должна быть в градусах Цельсия
# *   Файл-пример full output можно скачать [здесь](https://drive.google.com/file/d/1TyuHYZ0uh5teRiRFAga0XIqfU4vYW4-N/view?usp=sharing)
# *   Файл-пример biomet можно скачать [здесь](https://drive.google.com/file/d/1FjiBcSspDBlYlcg9Vzy71Sm49gOFZGBF/view?usp=sharing)
# *   Файл-пример CSF можно скачать *[здесь]*
# *   Файл конфигурации можно скачать *[здесь]*
# *   В файле full output должны быть 3 строки заголовка и названия переменных должны быть записаны во 2-й строке
# *   В файле biomet должны быть 2 строки заголовка и названия переменных должны быть записаны в 1-й строке. По умолчанию без проблем читаются файлы, у которых дата и время записаны в колонке TIMESTAMP_1 в формате yyyy-mm-dd HHMM
#
# ## **Выходные файлы**
# Форматы выходных файлов (собраны в архиве FluxFilter_output.zip и в директории output в разделе Файлы):
# 1.   Файл базы данных ИАС уровня 2;
# 2.   Входной файл для инструмента фильтрации по u*, заполнения пропусков и разделения потоков [REddyProcWeb](https://www.bgc-jena.mpg.de/5624918/Input-Format) (Институт Макса Планка, Германия). Этот же файл используется как входной для раздела "Обработка утилитами REddyProc" данного скрипта.
# 3. Входной файл для инструмента заполнения пропусков [Flux Analysis Tool](https://atmenv.envi.osakafu-u.ac.jp/staff/ueyama/softwares/) (M. Ueyama, Япония)
# 4. Файл output_all – все исходные переменные и все флаги применения фильтров.
# 5. Файл output_summary – запись для основных переменных исходных данных, отфильтрованных данных, флаг применения каждого фильтра, средние суточные ходы в окне 30 и 10 дней.
# 6. Лог - записи в ходе работы скрипта, введенные для фильтрации параметры в данном пробеге.
# 7. Директория reddyproc содержит результаты заполнения переменных в таком же формате, что и оригинальный инструмент [REddyProcWeb](https://www.bgc-jena.mpg.de/5624929/Output-Format). Помимо этого, в директории output/reddyproc содержатся обобщающие файлы с индексами _hourly (суточные ходы оригинальных и заполненных переменных), _daily (средние суточные значения), _monthly (средние месячные значения) и _yearly (значения за год, если данных меньше - за весь период обработки).
#
# ## **Загрузка входных файлов**
# Возможны два основных варианта загрузки:  
#
# Через браузер:  
# *   нажмите на кнопку директории (нижняя кнопка в левой панели под кнопкой "ключ")
# *   перетащите один или несколько фалов (к примеру, из проводника Windows) в пустое пространство под директорией `sample_data`
# *   закомментировать две команды `!gdown` в разделе **Загружаем данные**  
#
# Через google-диск:  
# *   загрузить на google-диск файлы full output, biomet, файл конфигурации и/или любые другие
# *   открыть к ним доступ
# *   скопировать часть публичной ссылки в раздел **Загружаем данные** в команду !gdown 
# Вариант google-диска оптимален, если в дальнейшем тетрадь будет отправлена другим пользователям (возможен закрытый доступ только отдельным аккаунтам Google).  
# 
# После загрузки в разделе **Конфигурация загрузки данных** необходимо: 
# *   если используется неавтоматический режим работы, то заменить названия входных файлов на импортируемые
# *   проверить формат входных даты и времени 
#
# ## **Перед фильтрацией**
# *   Можно загружать несколько файлов full output и biomet, они будут автоматически расположены по возрастанию дат-времени и слиты в одну таблицу
# *   Осуществляется проверка меток времени для каждого входного файла (регуляризация)
# *   Рассчитываются VPD <-> RH, SWIN <-> RG <-> PAR в случае отсутствия
# *   Можно работать с потоком CO2 либо проверить данные о накоплении, прибавить их к потоку CO2 и работать с NEE
#
# ## **Как происходит фильтрация**
# Скрипт позволяет выявить и удалить некачественные и выбивающиеся значения с помощью  1) физической, 2) статистической  фильтрации, проходящей под визуальным контролем - с просмотром графиков до фильтраций и после.
# 1. Физическая фильтрация включает удаление плохих значений потоков с флагом EddyPro больше порогового, при уровне сигнала газоанализатора (CO2SS) ниже порогового значения, в дождь и после дождей, при высокой влажности, по ночным и дневным допустимым диапазонам, по допустимому диапазону зимой.
# 2. Статистическая фильтрация включает удаление выбивающихся значений (outliers/spikes/выбросы/пики/спайки) с помощью фильтров по минимальным и максимальным допустимым значениям, по квантилям, по отклонениям от среднего суточного хода в окне несколько дней, отклонениям от средних в скользящем окне на несколько точек MAD (Sachs, 2006) и HAMPEL (Pearson et al., 2016).
# 3. Опцию визуальной фильтрации данных (ручное удаление точек при просмотре графика) Google Colab не позволяет реализовать, но в версии для запуска в среде программирования визуальная фильтрация планируется.
# 4. Можно исключить данные по списку интервалов (исключить с ... - по ...), например, калибровки по журналу технических работ.
#
# ## **Скачивание выходных файлов**
# Все выходные файлы можно скачать в последнем разделе "Выгрузка результатов", нажав кнопку "Download outputs".
#
# (с)Евгений Курбатов, Вадим Мамкин, Ольга Куричева
# (с)Инструмент REddyProc: Wutzler T, Lucas-Moffat A, Migliavacca M, Knauer J, Sickel K, Sigut, Menzer O & Reichstein M (2018) Basic and extensible post-processing of eddy covariance flux data with REddyProc. Biogeosciences, Copernicus, 15, doi: 10.5194/bg-15-5015-2018
# (с)Адаптация REddyProc и постобработка: Олег Дещеревский

# %% [markdown] id="sj6Z0gnhVM-R"
# # Технический блок
# Импорт библиотек и определение функций

# %% id="lZliIHxRJiqk"
# from google.colab import userdata
# key = userdata.get('registry_key')

# %pip install pysolar
# %pip install ruamel.yaml
# %pip install deepdiff
# %pip install plotly-resampler dateparser >> /dev/null
# # %pip install --index-url https://public:{key}@gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null
# %pip install --index-url https://gitlab.com/api/v4/projects/55331319/packages/pypi/simple --no-deps bglabutils==0.0.21 >> /dev/null

# py -> ipynb conversion is great to keep only .py in git, this can be used if it's easy to override any function in colab cells

# !git -c init.defaultBranch=main init
# !git sparse-checkout init
# !git sparse-checkout set src locale
# !git remote add origin https://github.com/PlaZMaD/climate.git
# !git fetch --depth 1 origin main
# !git -c advice.detachedHead=false checkout FETCH_HEAD

# %% id="Ywv5kp0rzanK"
import logging
import re
import sys
from pathlib import Path

import matplotlib.pylab as plt
import numpy as np
import pandas as pd

# #%load_ext autoreload
# #%autoreload 2

repo_dir = Path('.')
sys.path.append(str(repo_dir))

import bglabutils.basic as bg
# import bglabutils.boosting as bb
# import textwrap

from src.colab_routines import colab_no_scroll, colab_enable_custom_widget_manager, colab_add_download_button
from src.ffconfig import FFConfig, RepConfig, FFGlobals, InputFileType
from src.ff_logger import init_logging, ff_log
from src.helpers.io_helpers import ensure_empty_dir, create_archive
from src.helpers.env_helpers import setup_r_env
from src.data_io.fat_export import export_fat
from src.data_io.rep_level3_export import export_rep_level3
from src.data_io.data_import import try_auto_detect_input_files, import_data
from src.data_io.ias_io import export_ias
from src.ipynb_routines import setup_plotly, ipython_enable_word_wrap, ipython_edit_function
from src.filters import min_max_filter, qc_filter, std_window_filter, meteorological_rh_filter, \
    meteorological_night_filter, meteorological_day_filter, meteorological_co2ss_filter, meteorological_ch4ss_filter, \
    meteorological_rain_filter, quantile_filter, mad_hampel_filter, manual_filter, winter_filter
from src.plots import get_column_filter, basic_plot, plot_nice_year_hist_plotly, make_filtered_plot, plot_albedo

# cur_dir = %pwd
# assert cur_dir == '/content'
gl = FFGlobals(out_dir=Path('output'), repo_dir=repo_dir)
ensure_empty_dir(gl.out_dir)

colab_no_scroll()
colab_enable_custom_widget_manager()
setup_plotly(gl.out_dir)
init_logging(level=logging.INFO, fpath=gl.out_dir / 'log.log', to_stdout=True)

# Cells can be executed separately via import * and mocking global vars import global as gl
# To tweak any function directly in Colab: 1) run all cells above 2) uncomment and run 3) comment back:
# ipython_edit_function(meteorological_night_filter)


# %% [markdown] id="wVF1vDm4EauW"
# # Загружаем данные

# %% [markdown] id="LV9FvvtnVqdN"
# **Необходимо поменять:**
#
# Возможны два основных варианта загрузки файлов (см. введение: загрузка входных файлов):  
# 1) перетаскиванием в браузер или загрузкой через меню Upload (правый клик под sample_data)  
# 2) загрузкой с google-диска командой `!gdown ...` по ссылке  
# 
# В варианте 1 необходимо вручную добавить файлы и отключить загрузку по умолчанию двух демонстрационных файлов: поменять  
# `!gdown ...` на `# !gdown ...`.  
# 
# При загрузке с google-диска (вариант 2) после !gdown вставьте символы после d/ и до следующего / из публичной ссылки на файл, лежащий на google-диске. К примеру, если ссылка
# https://drive.google.com/file/d/1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB/view?usp=sharing,
# то команда будет записана как  
# `!gdown 1fGhmvra0evNzM0xkM2nu5T-N_rSPoXUB`
#
# `#Загрузка файла full output`
# Здесь нужно прописать символы из ссылки на файл full output
#
# `#Загрузка файла biomet`
# Здесь нужно прописать символы из ссылки на файл biomet

# %% id="KMu4IqY45HG6"

# Загрузка файла full output
# https://drive.google.com/file/d/1CGJmXyFu_pmzTLitG5aU8fwY8gW3CI1n/view?usp=sharing
# !gdown 1CGJmXyFu_pmzTLitG5aU8fwY8gW3CI1n

# Загрузка файла biomet
# https://drive.google.com/file/d/19XsOw5rRJMVMyG1ntRpibfkUpRAP2H4k/view?usp=sharing
# !gdown 19XsOw5rRJMVMyG1ntRpibfkUpRAP2H4k

# %% [markdown] id="WfWRVITABzrz"
# # Задаем параметры для загрузки и обработки данных

# %% [markdown] id="ox0UplWMe7wn"
# ## Конфигурация загрузки данных
# Здесь прописываются параметры входных файлов: названия, формат дат-времени и другие.  
#
# В зависимости от загруженных файлов cкрипт поддерживает следующие режимы чтения данных:  
# - один или несколько файлов EddyPro - full output
# - один или несколько файлов EddyPro - full output и один или несколько файлов EddyPro - biomet
# - один файл ИАС
# - один файл CSF
#
# В простых случаях (и если не загружены лишние файлы) тип фалов и их настройки будут определены автоматически. В сложных случаях или при ошибках можно попробовать вручную задать все настройки в этой ячейке.  
#
# **Файл конфигурации**  
# Скрипт поддерживает два варианта задания опций:  
# - без файла конфигурации, используются настройки из ячеек тетради  
# - с файлом конфигурации, при этом настройки из ячеек не применяются  
#
# Пример файла конфигурации последнего запуска `config*.yaml` будет добавлен в выходной архив после завершения работы тетради.
# Его можно отредактировать и в дальнейшем загружать в скрипт вместе с данными. Файл читается в этой ячейке автоматически, если загружен пользователем и назван по шаблону `config*.yaml`. Отключить загрузку или задать фиксированное название можно в параметре `load_path='auto'`.  
#
# **Необходимо проверить:**
#
# В автоматическом режиме (по умолчанию) в логе работы ячейки **Импорт и проверка данных** будет контрольная информация по импорту и режиму работы (один из `'EDDYPRO_FO'`, `'EDDYPRO_FO_AND_BIOMET'`, `'IAS'`, `'CSF'`).  Также необходимо проверить в логе правильность определения форматов даты-времени и других настроек. При неправильном определении можно задать вручную:  
#
# В `config.input_files` должен быть либо путь до файла (`= ['1.csv']`) при имени файла 1.csv, либо список (list) путей в случае загрузки нескольких файлов (`= ['1.csv', '2.csv']`), либо словарь путей и типов файлов `= {'1.csv': InputFileType.EDDYPRO_FO}`.  
# При импорте через !gdown файла с google-диска достаточно указать в одинарной кавычке *имя файла.расширение*. Не забывайте расширение .csv!  
#
# Проверьте порядок записи даты (год, месяц, день) и разделители даты-времени во входных файлах, открыв их в текстовом редакторе. Возможные варианты:
# 1.  Дата записана как 29.05.2024 и время как 12:00. Тогда они кодируются как
# "%d.%m.%Y %H:%M" – этот формат записан ниже по умолчанию, менять ничего не надо;
# 2.  Дата записана как 29/05/2024 и время как 12:00. Измените в строке ниже формат на "%d/%m/%Y %H:%M"
# 3.  Дата записана как 2024-05-29 и время как 1200. Измените в строке ниже формат на "%Y-%m-%d %H%M"
# 4.  В остальных случаях действуйте по аналогии. Если в графе time есть секунды, то формат кодируется как "%Y-%m-%d %H:%M:%S".  
# К примеру, в биомет-файле по умолчанию дата записана как 2011-11-12 и время как 1200. Кодируется как "%Y-%m-%d %H%M".  
#
# **Дополнительные опции (без уровня PRO лучше не менять)**:  
# `config.*.missing_data_codes = ['-9999']` список значений во входных файлах, которые будут заменены на np.nan для адекватной работы алгоритмов;  
# `config.*.repair_time` если `True`, то проверит колонку с датой-временем на пропуски и монотонность, проведет регенерацию по первой-последней точке с учетом предполагаемой длины шага (вычисляется по паре первых значений ряда).

# %% id="tVJ_DRBrlpYd"

# init_debug=True: быстрый режим скрипта с обработкой только нескольких месяцев
# load_path=None disables lookup, load_path='myconfig.yaml' sets fixed expected name without pattern lookup
config = FFConfig.load_or_init(load_path='auto',
                               init_debug=False, init_version='1.0.0')

if not config.from_file:
    config.input_files = 'auto'
    # alternative ways if 'auto' mode works not as expected:
    # config.input_files = ['eddypro_GHG_biomet_CO2SS_Express_full_output_2023-03-29T020107_exp.csv', 'eddypro_noHMP_full_output_2014_1-5.csv', 'BiometFy4_2023.csv']
    # config.input_files = {'eddy_pro tv_fy4 2023.csv': InputFileType.EDDYPRO_FO, 'BiometFy4_2023.csv': InputFileType.EDDYPRO_BIOMET}
    
    config.time_col = 'datetime'
    
    config.eddypro_fo.missing_data_codes = ['-9999']
    config.eddypro_fo.date_col = 'date'
    config.eddypro_fo.try_date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    config.eddypro_fo.time_col = 'time'
    config.eddypro_fo.try_time_formats = ['%H:%M', '%H:%M:%S']
    config.eddypro_fo.repair_time = True
    
    config.eddypro_biomet.missing_data_codes = ['-9999']
    config.eddypro_biomet.datetime_col = 'TIMESTAMP_1'
    config.eddypro_biomet.try_datetime_formats = ['%Y-%m-%d %H%M', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.eddypro_biomet.repair_time = True
    
    config.csf.missing_data_codes = ['-9999']
    config.csf.datetime_col = 'TIMESTAMP'
    config.csf.try_datetime_formats = ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M']  # yyyy-mm-dd HHMM
    config.csf.repair_time = True
# %% [markdown] id="DtxFTNnEfENz"
# ## Выбор колонок для графиков и фильтраций

# %% id="nLnivFTtg9cu"
# Соберем обзорную информацию о нужных величинах:
cols_to_investigate = [
    'co2_flux',
    'ch4_flux',
    'LE',
    'H',
    'co2_strg',
    'Ta_1_1_1',
    'RH_1_1_1',
    'VPD_1_1_1',
    'P_1_1_1',
    'SWIN_1_1_1',
    'PPFD_1_1_1',
    # 'co2_signal_strength',
    # 'ch4_signal_strength',
]

cols_to_investigate = [k.lower() for k in cols_to_investigate]

# %% [markdown] id="wVpYvr9_fKBU"
# ## Настройка параметров анализа данных
#
# Все настройки для co2_flux будут применены для nee, в случае его расчета

# %% [markdown] id="FH2uRGi4p5Zj"
# ### Фильтрация физическая

# %% id="pPemVdWVbq2E"
if not config.from_file:
    config.calc_nee = True
    
    # Индекс станции для названий выходных файлов, рисунков
    config.site_name = 'auto'
    config.ias_out_version = 'auto'

# %% [markdown] id="5MK90gyzQryZ"
# Параметры фильтрации по флагам качества. Данные с флагами в интервале (-inf, val] будут помечены как валидные, а данные со значением флага больше порога будут исключены.

# %% id="ukl734CBblay"
qc = {}
qc['h'] = 1  # Если система флагов была 1-9, поправить
qc['le'] = 1  # Если система флагов была 1-9, поправить
qc['co2_flux'] = 1  # Если система флагов была 1-9, поправить
qc['ch4_flux'] = 1  # Если система флагов была 1-9, поправить
if not config.from_file:
    config.qc = qc

# %% [markdown] id="QPIFpLN_-8Uf"
# Параметры фильтрации по метеорологическим переменным, возможные опции:
#
# *   `CO2SS_min` - уберет CO2_FLUX при co2_signal_strength ниже указанного значения
# *   `p_rain_limit` - уберет H, LE и CO2_FLUX, для P_rain_1_1_1 выше указанного лимита
# *   `rain_forward_flag` - уберет  значения на указанное число записей вперед от каждого отфильтрованного на прошлом шаге значения
# *   `RH_max` - уберет значения LE и CO2_FLUX для которых RH_1_1_1 больше указанного порога
# * `use_day_filter` - в случае True дневные (Swin>`day_swin_limit`) NEE больше выставленного порога (NEE>`day_nee_max`) будут исключены
# * `use_night_filter` - в случае True ночные (Swin<`day_swin_limit`) NEE меньше выставленного порога (NEE<`night_nee_min`) будут исключены
# * `day_nee_max` - порог для NEE в дневное время (исключение интенсивной эмиссии днем)
# * `night_nee_min` - порог для NEE в ночное время (исключение интенсивного нетто-поглощения ночью)
# * `day_swin_limit` - порог приходящей коротковолновой радиации, задающий дневные данные (может быть изменен для станций за полярным кругом)
# * `night_h_limits`, `night_le_limits` - допустимые ночные диапазоны H и LE
# * `winter_nee_limits` - допустимый диапазон NEE в зимнее время (зимний период устанавливается отдельно в разделе "фильтрация зимних периодов, уточните даты!")
# * `winter_ch4_flux_limits` - допустимый диапазон потока метана в зимнее время
# * `CH4SS_min` - уберет CH4_FLUX при ch4_signal_strength ниже указанного значения
#
# При отсутствии в настройках какого-либо из параметров фильтрация не применяется.

# %% id="vxpiAbWk2yYr"
filters_meteo = {}
filters_meteo['CO2SS_min'] = 80.

# Фильтры могут не понадобиться для систем закрытого типа
filters_meteo['p_rain_limit'] = .1
filters_meteo['rain_forward_flag'] = 2
# Фильтр влажности ниже: применять только тогда, когда нет CO2SS (образование конденсата) и диагностики анемометра
# и данные не были отфильтрованы по этим показателям на этапе расчета в EddyPro
# meteo_filter_config['RH_max'] = 98

# Какие значения допускаются днем/ночью
filters_meteo['use_day_filter'] = True
filters_meteo['use_night_filter'] = True
filters_meteo['day_nee_max'] = 5
filters_meteo['night_nee_min'] = -5
filters_meteo['day_swin_limit'] = 10
filters_meteo['night_h_limits'] = [-50, 20]
filters_meteo['night_le_limits'] = [-50, 20]

# Какие значения допускаются зимой. Для травянистых экосистем правый порог обычно ниже
filters_meteo['winter_nee_limits'] = [0, 5]
filters_meteo['winter_ch4_flux_limits'] = [-1, 1]
filters_meteo['CH4SS_min'] = 20.

if not config.from_file:
    config.filters.meteo = filters_meteo

# %% [markdown] id="utUX7SA4qA_I"
# ### Фильтрация статистическая

# %% [markdown] id="wWISuF-xQCwq"
# Параметры фильтрации по абсолютным значениям.
# Для `rh_1_1_1` значения выше границы не отбрасываются, а заменяются на пограничные. Для `ppfd_1_1_1`, `swin_1_1_1` аналогично обрабатываются минимальные значения.

# %% id="HQfIYFOd9uzi"
filters_min_max = {}
filters_min_max['co2_flux'] = [-40, 40]
filters_min_max['co2_strg'] = [-20, 20]
filters_min_max['h'] = [-100, 800]
filters_min_max['le'] = [-100, 1000]
filters_min_max['u_star'] = [0, 10]
filters_min_max['ta_1_1_1'] = [-50, 50]
filters_min_max['p_1_1_1'] = [0, 100]
filters_min_max['vpd_1_1_1'] = [0, 50]
filters_min_max['rh_1_1_1'] = [0, 100]  # max
filters_min_max['swin_1_1_1'] = [0, 1200]  # min
filters_min_max['ppfd_1_1_1'] = [0, 2400]  # min
filters_min_max['rg_1_1_1'] = [0, 2400]  # min
filters_min_max['ch4_flux'] = [-10, 10]

if not config.from_file:
    config.filters.min_max = filters_min_max

# %% [markdown] id="vmyTKbV1RdjD"
# Параметры фильтрации по отклонению от среднего суточного хода.
# * `sigmas` - допустимый интервал отклонения от среднего хода; вне интервала значения помечаются как отфильтрованные
# * `window` - размер окна в днях для подсчета среднего хода
# * `min_periods` - минимальное число точек в окне. Если меньше - оценка скользящего будет отсутствовать, фильтр не применится.

# %% id="xfRVNYbFYzG3"
filters_window = {}
# Для систем закрытого типа фильтр может быть мягче (например, 3 sigma)
filters_window['co2_flux'] = {'sigmas': 2, 'window': 10, 'min_periods': 4}
filters_window['ch4_flux'] = {'sigmas': 2, 'window': 10, 'min_periods': 4}

# Если удаляются надежные значения - нужно увеличить 'sigmas'
filters_window['ta_1_1_1'] = {'sigmas': 4, 'window': 10, 'min_periods': 4}
filters_window['u_star'] = {'sigmas': 4, 'window': 10, 'min_periods': 4}
for col in ['h', 'le', 'rh_1_1_1', 'vpd_1_1_1']:
    filters_window[col] = {'sigmas': 7, 'window': 10, 'min_periods': 4}
for col in ['swin_1_1_1', 'ppfd_1_1_1']:
    filters_window[col] = {'sigmas': 8, 'window': 10, 'min_periods': 4}

if not config.from_file:
    config.filters.window = filters_window

# %% [markdown] id="KF_MGD7pSGre"
# Параметры фильтрации выше-ниже порога по квантилям (выпадающие строки отфильтровываются)

# %% id="asO_t2tZmiD0"
filters_quantile = {}
filters_quantile['co2_flux'] = [0.01, 0.99]
filters_quantile['ch4_flux'] = [0.01, 0.99]
filters_quantile['co2_strg'] = [0.01, 0.99]

if not config.from_file:
    config.filters.quantile = filters_quantile

# %% [markdown] id="cPiTN288UaP3"
# Параметры для фильтрации по отклонению от соседних точек, фильтры MAD и Hampel.

# %% id="2b3eBVFUq3AU"
filters_madhampel = {}
# filters_madhampel = {i:{'z': 5.5, 'hampel_window': 10} for i in cols_to_investigate if 'p_1_1_1' not in i}
# Более жесткая фильтрация: 'z'=4. Более мягкая: 'z'=7
filters_madhampel['co2_flux'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['ch4_flux'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['le'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['h'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['co2_strg'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['ta_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['rh_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['vpd_1_1_1'] = {'z': 5.5, 'hampel_window': 10}
filters_madhampel['swin_1_1_1'] = {'z': 8.0, 'hampel_window': 10}
filters_madhampel['ppfd_1_1_1'] = {'z': 8.0, 'hampel_window': 10}

if not config.from_file:
    config.filters.madhampel = filters_madhampel

# %% [markdown] id="wVF1vDm4EauW"
# # Импорт и проверка данных

# %% id="Xw5TapK10EhR"
config.input_files, config.import_mode, config.site_name, config.ias_out_version, config.has_meteo = try_auto_detect_input_files(
    config)
data, time_col, meteo_cols, data_freq, config.has_meteo = import_data(config)

gl.points_per_day = int(pd.Timedelta('24h') / data_freq)

# %% id="C8lLDYOWzH2d"
data.columns = data.columns.str.lower()
if not config.has_meteo:
    data["rh_1_1_1"] = data['rh']
    # TODO QOA 1 different units? Elg biomet kPa, but mean 8.6 ?  
    data["vpd_1_1_1"] = data['vpd']

# %% [markdown] id="ipknrLaeByCT"
# Проверка на корректность типа данных (пример: наличие текста там, где должны быть числа):

# %% id="8LawdKUbB1_m"
cols_2_check = ['ppfd_in_1_1_1', 'u_star', 'swin_1_1_1', 'co2_signal_strength',
                'rh_1_1_1', 'vpd_1_1_1', 'rg_1_1_1', 'p_rain_1_1_1',
                'co2_signal_strength_7500_mean', 'CO2SS'.lower(), 'co2_signal_strength',
                'ch4_signal_strength_7500_mean', 'ch4SS'.lower(), 'ch4_signal_strength',
                'p_1_1_1', 'ta_1_1_1', 'co2_strg', 'le', 'h']

data_type_error_flag = False
for col in cols_2_check:
    if col not in data.columns:
        continue
    error_positions = data[col].fillna(0).apply(pd.to_numeric, errors='coerce').isna()
    if error_positions.any():
        ff_log.error(
            f"""Check input files for {col} column near:\n {error_positions[error_positions == True].index.strftime('%d-%m-%Y %H:%M').values} in {'biomet' if len(meteo_cols) > 0 and col in meteo_cols else 'data'} file"""
        )
        data_type_error_flag = True
if data_type_error_flag:
    print("Data have some errors! Please check log file!")
    raise KeyboardInterrupt

# %% [markdown] id="QDHkyl_PruXE"
# # Предобработка

# %% [markdown] id="Nh5MosYXS6aj"
# Переименовываем колонки для единого формата, рассчитываем VPD <-> RH, SWIN <-> RG и PAR <-> SWIN в случае отсутствия.
#

# %% id="mAdYXJFdSRbJ"
have_rh_flag = False
have_vpd_flag = False
have_par_flag = False
have_swin_flag = False
have_rg_flag = False
have_p_flag = False
have_pr_flag = False
have_ppfd_flag = False

for col in data.columns:
    # Eddypro renames
    if col == 'u*':
        print(f"renaming {col} to u_star")
        data = data.rename(columns={col: 'u_star'})
    if 'co2_signal_strength' in col:
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})
    if col in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()] or 'co2_signal_strength' in col:
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})
    if col in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()] or 'ch4_signal_strength' in col:
        print(f"renaming {col} to ch4_signal_strength")
        data = data.rename(columns={col: 'ch4_signal_strength'})
    
    # Biomet renames
    if col == 'ppfd_in_1_1_1':
        print(f"renaming {col} to ppfd_1_1_1")
        data = data.rename(columns={col: 'ppfd_1_1_1'})
    if col == 'sw_in_1_1_1':
        print(f"renaming {col} to swin_1_1_1")
        data = data.rename(columns={col: 'swin_1_1_1'})
    
    if col == "rh_1_1_1":
        have_rh_flag = True
    if col == "vpd_1_1_1":
        have_vpd_flag = True
    if col in ['swin_1_1_1', 'sw_in_1_1_1']:
        have_swin_flag = True
    if col == 'par':
        have_par_flag = True
    if col == 'rg_1_1_1':
        have_rg_flag = True
    if col == 'p_1_1_1':
        have_p_flag = True
    if col == 'p_rain_1_1_1':
        have_pr_flag = True
    if col == 'ppfd_1_1_1':
        have_ppfd_flag = True

if not (have_ppfd_flag or have_swin_flag):
    print("NO PPFD and SWin")
else:
    if not have_ppfd_flag:
        data['ppfd_1_1_1'] = data['swin_1_1_1'] / 0.46
    if not have_swin_flag:
        data['swin_1_1_1'] = 0.46 * data['ppfd_1_1_1']
    have_ppfd_flag = True
    have_swin_flag = True

if not (have_rg_flag or have_swin_flag):
    print("NO RG AND SWIN")
else:
    print("Checking RG-SWIN pair")
    if not have_rg_flag:
        data['rg_1_1_1'] = data['swin_1_1_1']
    if not have_swin_flag:
        data['swin_1_1_1'] = data['rg_1_1_1']
        have_swin_flag = True

if not (have_p_flag or have_pr_flag):
    print("NO P and P_RAIN")
else:
    print("Checking P <-> P_rain pair")
    if not have_p_flag:
        data['p_1_1_1'] = data['p_rain_1_1_1']
    if not have_pr_flag:
        data['p_rain_1_1_1'] = data['p_1_1_1']

if not (have_vpd_flag or have_rh_flag):
    print("NO RH AND VPD")
else:
    if 'ta_1_1_1' in data.columns:
        temp_k = (data['ta_1_1_1'] + 273.15)
    else:
        temp_k = data['air_temperature']
    logE = 23.5518 - (2937.4 / temp_k) - 4.9283 * np.log10(temp_k)
    ehpa = np.power(10, logE)
    if not have_vpd_flag:
        print("calculating vpd_1_1_1 from rh_1_1_1 and air temperature")
        data['vpd_1_1_1'] = ehpa - (ehpa * data['rh_1_1_1'] / 100)
    if not have_rh_flag:
        # TODO QOA 1 possibly an error
        # OA: check tg for the formula
        print("estimating rh_1_1_1 from air temperature")
        data['rh_1_1_1'] = ehpa

if not (have_par_flag or have_swin_flag):
    print("NO PAR and SWin")
else:
    if not have_par_flag:
        data['par'] = data['swin_1_1_1'] / 0.47  # SWin=PAR*0.47
    if not have_swin_flag:
        data['swin_1_1_1'] = 0.47 * data['par']

for col in ['co2_signal_strength_7500_mean', 'CO2SS'.lower()]:
    # print(data.columns.to_list())
    if col in data.columns.to_list():
        print(f"renaming {col} to co2_signal_strength")
        data = data.rename(columns={col: 'co2_signal_strength'})

for col in ['ch4_signal_strength_7700_mean', 'CH4SS'.lower()]:
    # print(data.columns.to_list())
    if col in data.columns.to_list():
        print(f"renaming {col} to ch4_signal_strength")
        data = data.rename(columns={col: 'ch4_signal_strength'})

if not config.has_meteo or 'ta_1_1_1' not in data.columns:
    data['ta_1_1_1'] = data['air_temperature'] - 273.15
    ff_log.info("No Ta_1_1_1 column found, replaced by 'air_temperature'")

# %% [markdown] id="soyyX-MCbaXt"
# ## Получение NEE из потока CO2 и накопления

# %% [markdown] id="lqWwGSMObro4"
# Проверка накопления. Рассчитанное по одному уровню в EddyPro не всегда корректно. Корректность проверяется суточным ходом: должен быть рост запаса в течение ночи, резкое уменьшение утром.

# %% [markdown] id="2yqwO7Uhcjmz"
# Фильтрация co2_strg с удалением значений выше и ниже пороговых квантилей. Заполнение пропусков co2_strg  длиной 3 точки и менее – линейной интерполяцией. Полученные отфильтрованные и заполненные значения co2_strg показываются на графике. Принятие решения, суммировать ли co2_flux и co2_strg для получения NEE или работать дальше с co2_flux.

# %% id="cjt05XXtbr69"
# Пробелы длиной 3 и меньше заполняются линейно
if config.calc_nee and 'co2_strg' in data.columns:
    tmp_data = data.copy()
    tmp_data['co2_strg_tmp'] = tmp_data['co2_strg'].copy()
    tmp_filter_db = {'co2_strg_tmp': []}
    if 'co2_strg' in config.filters.quantile.keys():
        tmp_q_config = {'co2_strg_tmp': config.filters.quantile['co2_strg']}
    else:
        tmp_q_config = {}
    tmp_filter_db = {'co2_strg_tmp': []}
    tmp_data, tmp_filter_db = quantile_filter(tmp_data, tmp_filter_db, tmp_q_config)
    tmp_data.loc[~get_column_filter(tmp_data, tmp_filter_db, 'co2_strg_tmp').astype(bool), 'co2_strg_tmp'] = np.nan
    # tmp_data['co2_strg_tmp'] = tmp_data['co2_strg_tmp'].interpolate(limit=3)
    # tmp_data['co2_strg_tmp'].fillna(bg.calc_rolling(tmp_data['co2_strg_tmp'], rolling_window=10 , step=gl.points_per_day, min_periods=4))
    basic_plot(tmp_data, ['co2_strg_tmp'], config.site_name, tmp_filter_db, steps_per_day=gl.points_per_day)
    print(tmp_q_config, tmp_filter_db, tmp_data['co2_strg_tmp_quantilefilter'].value_counts())

# %% id="2IQ7W6pslYF-"
# Решаем, суммировать ли исходный co2_flux и co2_strg_filtered_filled для получения NEE
if not config.from_file:
    config.calc_with_strg = False  # В случае, если дальше работаем с NEE, оставить True.
ff_log.info(f"config.calc_with_strg is set to {config.calc_with_strg}")
# Для того, чтобы работать дальше с co2_flux, игнорируя co2_strg, поставить False

# %% id="ueuvsNxYdtgs"
if config.calc_nee and 'co2_strg' in data.columns:
    if config.calc_with_strg:
        data['nee'] = (tmp_data['co2_flux'] + tmp_data['co2_strg_tmp']).copy()
    else:
        data['nee'] = data['co2_flux'].copy()
    del tmp_data
    if 'nee' not in cols_to_investigate:
        cols_to_investigate.append('nee')
    
    if not config.from_file:
        for filter_config in [config.qc, config.filters.meteo, config.filters.min_max, config.filters.window,
                              config.filters.quantile,
                              config.filters.madhampel]:
            if 'co2_flux' in filter_config:
                filter_config['nee'] = filter_config['co2_flux']

# %% [markdown] id="mUgwuaFYribB"
# # Обзор статистики по интересующим колонкам

# %% id="dhcplCMbXtkK"
cols_to_investigate = [p for p in cols_to_investigate if p in data.columns]

# %% id="YfusqiotOi3n"
data.loc[:, cols_to_investigate].describe()

fig, axs = plt.subplots(ncols=min(3, len(cols_to_investigate)), nrows=int(np.ceil(len(cols_to_investigate) / 3)),
                        squeeze=False, figsize=(13, 8))

for ind, ax in enumerate(axs.reshape(-1)):
    if ind >= len(cols_to_investigate):
        break
    feature = cols_to_investigate[ind]
    ax.boxplot(data[feature].to_numpy()[~np.isnan(data[feature].to_numpy())])
    ax.set_title(f"Boxplot for {feature}")
plt.tight_layout()
fig.show()

data[cols_to_investigate].describe()

# %% [markdown] id="0oJLXYGbr93S"
# # Фильтрация данных физическая

# %% id="apGNk8eBxgBv"
plot_data = data.copy()
filters_db = {col: [] for col in plot_data.columns.to_list()}
print(plot_data.columns.to_list())

# %% [markdown] id="BL_6XxGGsCBK"
# ## по флагам качества

# %% id="GGwe7_uU1C8U"
plot_data, filters_db = qc_filter(plot_data, filters_db, config.qc)

# %% [markdown] id="M_gKSTNYyzjS"
# ## по порогу CO2SS и CH4SS

# %% id="viq7BZue9Ett"
plot_data, filters_db = meteorological_co2ss_filter(plot_data, filters_db, config.filters.meteo)

# %% id="5RrPfxfiJGhN"
plot_data, filters_db = meteorological_ch4ss_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="qwqVDeH6y73_"
# ## по допустимым значениям RH

# %% id="11isfvNZ9FGu"
plot_data, filters_db = meteorological_rh_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="oSX2h9QzzFkT"
# ## по наличию дождя

# %% id="jz696mc09FlB"
if config.has_meteo:
    plot_data, filters_db = meteorological_rain_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="Xy2y00P1zJtZ"
# ## по ночным и дневным допустимым диапазонам

# %% id="ED_Qh6TS0Qkc"
if config.has_meteo:
    plot_data, filters_db = meteorological_night_filter(plot_data, filters_db, config.filters.meteo)

# %% id="X3Vguu8MK635"
if config.has_meteo:
    plot_data, filters_db = meteorological_day_filter(plot_data, filters_db, config.filters.meteo)

# %% [markdown] id="fzfTJdNe68Eu"
# ## фильтрация зимних периодов, уточните даты!

# %% id="wJ87D57S7A91"
if ('winter_nee_limits' in config.filters.meteo.keys()) or ('winter_ch4_flux_limits' in config.filters.meteo.keys()):
    plot_albedo(plot_data, filters_db)

# %% id="Z_RAYINf67PO"
if config.has_meteo:
    unroll_filters_db = filters_db.copy()
    if not config.from_file:
        config.filters.winter_date_ranges = [
            ['01.01.2023 00:00', '26.03.2023 00:00'],
            ['13.11.2023 00:00', '31.12.2023 00:00'],
        ]
    # date_ranges = []
    # date_ranges.append(['25.8.2014 00:00', '26.8.2014 00:00'])
    plot_data, filters_db = winter_filter(plot_data, filters_db, config.filters.meteo,
                                          config.filters.winter_date_ranges)

# %% [markdown] id="iipFLxf6fu5Y"
# Фильтрация по футпринту
# будет в следующей версии скрипта
#
# `fetch = 1 #или 0. 1 – остаются, 0 – убираются `

# %% [markdown] id="UAdRtCPGq6_y"
# # Фильтрация данных статистическая

# %% [markdown] id="LcwZplknsHJv"
# ## по минимальным и максимальным допустимым значениям

# %% id="FyJaM1zC1DDg"
# if config.has_meteo:
plot_data, filters_db = min_max_filter(plot_data, filters_db, config.filters.min_max)

# %% [markdown] id="j62U1dw8sTEm"
# ## по квантилям

# %% id="aNQ4XDK01DME"
# if config.has_meteo:
plot_data, filters_db = quantile_filter(plot_data, filters_db, config.filters.quantile)

# %% [markdown] id="7Sg76Bwasnb4"
# ## по отклонению от среднего хода

# %% id="uoDvHhoQ2MMe"
plot_data, filters_db = std_window_filter(plot_data, filters_db, config.filters.window)

# %% [markdown] id="iXl5RdINss9D"
# ## Фильтрация выбросов MAD & Hampel

# %% id="gl9cImVr2MO3"
unroll_filters_db = filters_db.copy()
plot_data, tmp_filter = mad_hampel_filter(plot_data, filters_db, config.filters.madhampel)

# %% [markdown] id="iu8MLKyh1AFk"
# ## Ручная фильтрация
#
# Если нужно убрать какой-то срок/сроки вручную
#

# %% id="ADy534At0_fN"
#  фильтр уберет значения от первого до второго включительно
if not config.from_file:
    config.filters.man_ranges = [
        # ['1.5.2023 00:00', '1.6.2023 00:00'],
        # ['25.8.2023 12:00', '25.8.2023 12:00'],
    ]
for man_range in config.filters.man_ranges:
    plot_data, tmp_filter = manual_filter(plot_data, filters_db, col_name="nee", man_range=man_range, value=0,
                                          manual_config=man_range)

# %% [markdown] id="quGbtDaJ_gID"
# ## Сводная таблица результатов фильтрации

# %% id="Pg78qGJ9_miW"
all_filters = {}
for key, filters in filters_db.items():
    if len(filters) > 0:
        pl_data = plot_data.copy()
        for filter_name in filters:
            all_filters[filter_name] = []
            all_filters[filter_name].append(len(pl_data.index))
            filtered_amount = len(pl_data.query(f"{filter_name}==0").index)
            all_filters[filter_name].append(filtered_amount)
            # old_val =  len(pl_data.index)
            pl_data = pl_data.query(f"{filter_name}==1")
            # print(filter_name, filtered_amount, len(pl_data.index) - old_val)
fdf_df = pd.DataFrame(all_filters)

ff_log.info("Какая часть данных от общего количества (в %) была отфильтрована:")
df_stats = fdf_df.iloc[1] / len(plot_data) * 100
ff_log.info('\n' + df_stats.to_string())

# %% [markdown] id="gA_IPavss0bq"
# # Отрисовка рядов

# %% [markdown] id="ijPM6mnJtMv8"
# ## Отрисовка результатов фильтрации данных

# %% id="50Xhczc-BRc2"
plot_terator = iter(cols_to_investigate)

# %% [markdown] id="uat4oESzU4__"
# Для экономии памяти и адекватной работы Google Colab графики будут выводиться поочередно при повторном запуске ячейки.

# %% id="NhNoFAd7DqNN"
col2plot = next(plot_terator, False)

# Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1, co2_signal_strength, ch4_flux
col2plot = 'nee'

# Или закомментировать одну строку выше и запускать повторно для переключения к следующему параметру
if col2plot:
    make_filtered_plot(plot_data, col2plot, col2plot, config.site_name, filters_db)
else:
    print("No more data, start from the begining!")
    plot_terator = iter(cols_to_investigate)

# %% id="ZG_wF2qW-Qwb"
# #линейное заполнение пропусков, limit - сколько может быть пропущенных подряд
# for col in cols_to_investigate:
#   plot_data[col] = plot_data[col].interpolate(limit=5)

# %% id="VtJ8wyx2-XCX"
# #Заполнение ходом
# for col in cols_to_investigate:
#   plot_data[col].fillna(bg.calc_rolling(plot_data[col], rolling_window=10, step=gl.points_per_day, min_periods=7))

# %% [markdown] id="MwuXRVTMtBz2"
# ## Отрисовка среднего хода для отфильтрованных рядов

# %% id="pWDTiucTgRlI"
plot_terator = iter(cols_to_investigate)

# %% id="COKiwe7020D4"
# Пример вычисления среднего хода

col2plot = next(plot_terator, False)
# Можно задать вручную
# col2plot = 'h'#"co2_flux"

# Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
col2plot = ['nee', 'le']
# Или просто запускать повторно для переключения к следующему параметру
if col2plot:
    basic_plot(plot_data, col2plot, config.site_name, filters_db, steps_per_day=gl.points_per_day)
else:
    print("No more data, start from the begining!")
    plot_terator = iter(cols_to_investigate)

# %% [markdown] id="RKEg6YBstXMp"
# ## Тепловые карты потоков для отфильтрованных данных

# %% id="mCUJYURKEL-f"
# Подставить нужное: co2_flux, le, h, co2_strg, ta_1_1_1, rh_1_1_1, vpd_1_1_1, p_1_1_1, swin_1_1_1, ppfd_1_1_1
for col in ['nee', 'le', 'h']:
    # Или просто запускать повторно для переключения к следующему параметру
    plot_nice_year_hist_plotly(plot_data, col, time_col, filters_db)

# %% [markdown] id="EFscf-JZt3_R"
# # Формирование выходных файлов

# %% [markdown] id="dokSxicNtdva"
# ## Файл для REddyProc

# %% [markdown] id="tDqsi61kSeak"
# Создадим шаблон шапки для файла REddyProc и сохраним требуемые переменные, не забыв учесть фильтрацию. Выходной файл - уровня 3.

# %% id="YVu2UrCzLqb4"
output_template = {
    'Year': ['-'], 'DoY': ['-'], 'Hour': ['-'], 'NEE': ['umol_m-2_s-1'], 'LE': ['Wm-2'], 'H': ['Wm-2'],
    'Rg': ['Wm-2'], 'Tair': ['degC'], 'Tsoil': ['degC'], 'rH': ['%'], 'VPD': ['hPa'], 'Ustar': ['ms-1'],
    'CH4flux': ['umol_m-2_s-1']
}
rep_df = plot_data.copy()
for column, filter in filters_db.items():
    filter = get_column_filter(rep_df, filters_db, column)
    rep_df.loc[~filter.astype(bool), column] = np.nan

gl.rep_level3_fpath = gl.out_dir / f"REddyProc_{config.site_name}_{int(plot_data[time_col].dt.year.median())}.txt"
export_rep_level3(gl.rep_level3_fpath, rep_df, time_col, output_template, config, gl.points_per_day)

# %% [markdown] id="e50f7947"
# ## Файл для ИАС
# Файл уровня 2, записывается из первоначально введенных данных **без учета** фильтраций

# %% id="yaLoIQmtzaYd"
if config.has_meteo:
    ias_df: pd.DataFrame = plot_data.copy()
    for column, filter in filters_db.items():
        filter = get_column_filter(ias_df, filters_db, column)
        ias_df.loc[~filter.astype(bool), column] = np.nan
    
    export_ias(gl.out_dir, config.site_name, config.ias_out_version, ias_df, time_col=time_col,
               data_swin_1_1_1=data['swin_1_1_1'])

# %% [markdown] id="Pm8hiMrb_wRW"
# ## Файл для FAT
# Файл уровня 3 (отфильтрованные данные), который годится для ввода в инструмент заполнения пропусков Flux Analysis Tool

# %% [markdown] id="0ll51nOal6Lz"
# ![image.png](data:image/png;base64,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)

# %% id="w9hkPLkB_zd1"
if config.has_meteo:
    fat_output_template = {
        'DoY': ['--'], r'u*': ['m s-1'], 'H': ['W m-2'], 'lE': ['-'], 'NEE': ['umol m-2 s-1'],
        'PPFD': ['umol m-2 s-1'], 'Ta': ['oC'], 'VPD': ['kPa'], 'PPFD_gapfilling': ['umol m-2 s-1'],
        'Ta_gapfilling': ['oC'], 'VPD_gapfilling': ['kPa'], 'period': ['--']
    }
    
    fat_df = plot_data.copy()
    for column, filter in filters_db.items():
        filter = get_column_filter(fat_df, filters_db, column)
        fat_df.loc[~filter.astype(bool), column] = np.nan
    
    export_fat(fat_df, fat_output_template, time_col, gl, config)
    del fat_df

# %% [markdown] id="GQ1bpermu8eq"
# ## Полный файл результатов фильтрации
# Файл содержит исходные переменные (потоки, метеорологические переменные). Колонка "tmp_datetime" - результат формирования единой даты-времени из двух колонок файла full output - date, time. Колонка datetime - результат работы коррекции даты-времени для столбца tmp_datetime. datetime_meteo - результат работы коррекции даты-времени для столбца timestamp_1. Далее файл содержит записи о применении каждого фильтра к каждой переменной (потоки, метеорология) в бинарном формате: 1 – фильтр не применен, 0 – применен.

# %% id="pk1lGANovC5U"
full_column_list = [c for c in plot_data.columns]
full_column_list = full_column_list.insert(0, full_column_list.pop(full_column_list.index(time_col)))
if 'date' in plot_data.columns:
    plot_data.loc[plot_data['date'].isna(), 'date'] = plot_data[time_col].dt.date
if 'time' in plot_data.columns:
    plot_data.loc[plot_data['time'].isna(), 'time'] = plot_data[time_col].dt.time

all_fpath = gl.out_dir / 'output_all.csv'
plot_data.fillna(-9999).to_csv(all_fpath, index=None, columns=full_column_list)
ff_log.info(f"Basic file saved to {all_fpath}")

# %% [markdown] id="-MSrgUD0-19l"
# ## Файл-резюме результатов фильтрации
# Краткий выходной файл после фильтраций. Содержит исходные основные переменные (метео и потоки), отфильтрованные основные переменные (индекс _filtered), интегральный флаг для каждой переменной, средние суточные ходы в окне 30 и 10 дней для отфильтрованных переменных.

# %% id="22dPWc2u-6IG"
columns_to_save = ['Date', 'Time', 'DoY', 'ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg',
                   'ch4_flux', 'u_star']

basic_df = plot_data.copy()

basic_df['Date'] = basic_df[time_col].dt.date
basic_df['Time'] = basic_df[time_col].dt.time
basic_df['DoY'] = np.round(
    basic_df[time_col].dt.dayofyear + basic_df[time_col].dt.hour / 24. + basic_df[time_col].dt.minute / 24. / 60.,
    decimals=3)

if not config.has_meteo:
    basic_df['ta_1_1_1'] = basic_df['air_temperature'] - 273.15
# метео
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
    # print(f"{col}(_[1-9]){{1,4}})")
    col_pos = [bool(re.fullmatch(f"{col}(_[1-9]){{1,4}}", col_in)) for col_in in basic_df.columns]
    if not any(col_pos):
        continue
    else:
        real_col = basic_df.columns[np.argmax(col_pos)]
        basic_df[col] = basic_df[real_col]

# Фильтрованные потоки
for col in ['nee', 'h', 'le', 'co2_strg', 'ch4_flux']:
    if col not in basic_df.columns:
        continue
    basic_df[f"{col}_filtered"] = basic_df[col]
    filter = get_column_filter(basic_df, filters_db, col)
    basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
    columns_to_save.append(f"{col}_filtered")

# Фильтрованные метео
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p']:
    if col not in basic_df.columns:
        continue
    basic_df[f"{col}_filtered"] = basic_df[col]
    filter = get_column_filter(basic_df, filters_db, col)
    basic_df.loc[~filter.astype(bool), f"{col}_filtered"] = np.nan
    columns_to_save.append(f"{col}_filtered")

# флаги
for col in ['ta', 'rh', 'vpd', 'swin', 'ppfd', 'p', 'h', 'le', 'co2_flux', 'co2_strg', 'nee',
            'ch4_flux']:  # ['nee', 'ch4', 'le', 'h']:
    if col not in basic_df.columns:
        continue
    basic_df[f"{col}_integral_flag"] = get_column_filter(basic_df, filters_db, col)
    columns_to_save.append(f"{col}_integral_flag")

# for key, item in filters_db.items():
#   columns_to_save = columns_to_save + item


for col in ['h', 'le', 'nee', 'rg', 'ppfd', 'ta', 'rh', 'vpd', 'ch4_flux']:
    if f"{col}_filtered" not in basic_df.columns:
        print(f"No {col}_filtered in file")
        continue
    col_out = col
    if col == "ppfd":
        col_out = "rg"
    basic_df[f'{col_out}_10d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=10, step=gl.points_per_day,
                                                 min_periods=7)
    basic_df[f'{col_out}_30d'] = bg.calc_rolling(basic_df[f"{col}_filtered"], rolling_window=30, step=gl.points_per_day,
                                                 min_periods=7)
    columns_to_save.append(f'{col_out}_10d')
    columns_to_save.append(f'{col_out}_30d')

basic_df = basic_df[[col for col in columns_to_save if col in basic_df.columns]]
basic_df = basic_df.fillna(-9999)

summary_fpath = gl.out_dir / 'output_summary.csv'
basic_df.to_csv(summary_fpath, index=None)
ff_log.info(f"New basic file saved to {summary_fpath}")
# %% [markdown] id="775a473e"
# # Обработка инструментом REddyProc
# В этом блоке выполняется 1) фильтрация по порогу динамической скорости ветра (u* threshold), 2) заполнение пропусков в метеорологических переменных и 30-минутных потоках, 3) разделение NEE на валовую первичную продукцию (GPP) и экосистемное дыхание (Reco), 4) вычисление суточных, месячных, годовых средних и среднего суточного хода по месяцам.
# %% [markdown] id="a8aa54de"
# ## Технический блок
# Необходим и автоматически запускается, если детектируется окружение Google Colab.  
# Загружает используемые в ячейках скрипты в директорию `src` и подготавливает R окружение.
# %% id="06859169"

ipython_enable_word_wrap()

# 1.3.2 vs 1.3.3 have slightly different last columns
# alternative for windows
# install.packages('https://cran.r-project.org/bin/windows/contrib/4.1/REddyProc_1.3.2.zip', repos = NULL, type = "binary")

setup_colab_r_code = """
install_if_missing <- function(package, version, repos) {
    if (!require(package, character.only = TRUE)) {
        remotes::install_version(package, version = version, upgrade = "never", repos = repos)
        library(package, character.only = TRUE)
    }
}
# sink redirect is required to improve ipynb output
sink(stdout(), type = "message")
install_if_missing("REddyProc", "1.3.3", repos = 'https://cran.rstudio.com/')
sink()
"""
setup_r_env()
from rpy2 import robjects

robjects.r(setup_colab_r_code)

from src.reddyproc.reddyproc_bridge import reddyproc_and_postprocess
from src.reddyproc.postprocess_graphs import RepOutputHandler, RepImgTagHandler, RepOutputGen
from src.reddyproc.preprocess_rg import prepare_rg

# %% [markdown] id="034b04a5"
# ## Фильтрация и заполнение пропусков
#
# Далее `config.reddyproc` - настройки, которые соответствуют опциям [онлайн-инструмента](https://www.bgc-jena.mpg.de/REddyProc/ui/REddyProc.php).
#
# **Необходимо проверить:**  
#
# Включение детектирования условий недостаточной турбулентности  
# `is_to_apply_u_star_filtering=True`  
# Метод Eddy Covariance применим только при развитой турбулентности. При динамической скорости ветра, или скорости трения (столбец *uStar*), ниже определенного порога поток CO2 может быть занижен. Данные о потоках в этих условиях заменяются на пропуски.
#
# Выбор метода разметки сезонов, для каждого из которых отдельно определяется уровень насыщения. `Continuous` - начало сезонов в Марте, Июне, Сентябре, и Декабре, Декабрь при этом включается в *следующий* год. `WithinYear` - каждый год отдельно. `User` - по столбцу *season*.  
# `u_star_seasoning="Continuous"`  
# Итеративная оценка точности вычисленного порога u* (bootstrap)  
# `is_bootstrap_u_star=False`  
#
# По сравнению с исходным инструментом REddyProc в этой тетради добавлена **экспериментальная** возможность подстановки пользовательского значения порога в случае, когда порог невозможно рассчитать (например, если недостаточно данных или отсутствует солнечная коротковолновая радиация *Rg*). Для травянистых экосистем можно использовать `0.01`, для лесных - `0.1`, для отключения подстановки - `None`.  
# `ustar_threshold_fallback=0.01`  
# REddyProc по умолчанию применяет порог uStar только в ночное время, для определения которого требуется столбец *Rg*. Следующая **экспериментальная** опция позволяет использовать теоретическое значение `"Rg_th_Py"` или `"Rg_th_REP"`, либо игнорировать отсутствие *Rg* и применить порог ко всем данным без учета времени суток - `None`:  
# `ustar_rg_source="Rg"`  
#
# В случае ошибок фильтрации будет предупреждение в логе ячейки и повторная попытка запуска с переходом к заполнению пропусков.
# Заполнение пропусков в 30-минутных потоках соответствует онлайн-инструменту и включено по умолчанию.
#
# Включение и выбор одного или обоих методов разделения потока C02 на валовую первичную продукцию (GPP) и дыхание экосистемы (Reco). Метод `Reichstein05` проводит разделение по ночным данным, метод `Lasslop10` - по дневным данным.
# `is_to_apply_partitioning=True`  
# `partitioning_methods=["Reichstein05", "Lasslop10"]`  
# При отсутствии данных об Rg разделение выполняться не будет! Для корректного завершения работы блока в этом случае поставьте  
# `is_to_apply_partitioning=False`  
#
# Широта, долгота, временная зона  
# `latitude = 56.5`  
# `longitude = 32.6`  
# `timezone = +3`  
#
# По температуре воздуха или почвы будет происходить заполнение  
# `temperature_data_variable="Tair"`
# либо
# `temperature_data_variable="Tsoil"`
#
# **Опции, изменение которых не предполагается в этой тетради:**
#
# В EddyProc доступен только метод подвижной точки `RTw` для определения порога uStar  
# `u_star_method="RTw"`  
# Заполнение пробелов в 30-минутных потоках  
# `is_to_apply_gap_filling=True`  
#
# **Дополнительные опции (согласованы с предыдущими секциями):**  
#
# Название станции, которое будет продублировано в названиях выходных файлов:    
# `site_id=ias_output_prefix`  
# Файл, из которого загружаются временные ряды:  
# `input_file=str(rep_input_fpath)`  
# Директория, в которую инструмент пишет контрольные изображения, базовую статистику по пропускам, заполненные ряды:  
# `output_dir=str(out_dir / 'reddyproc')`
# %% id="278caec5"

config_reddyproc = RepConfig(
    is_to_apply_u_star_filtering=True,
    # if default REP cannot detect threshold, this value may be used instead; None to disable
    ustar_threshold_fallback=0.01,
    # REP ustar requires Rg to detect nights; when real data is missing, 3 workarounds are possible
    # "Rg_th_Py", "Rg_th_REP" - estimate by theoretical algs,
    # "Rg" - by real data, "" - ignore Rg and filter both days and nights
    ustar_rg_source="Rg",
    is_bootstrap_u_star=False,
    # u_star_seasoning: one of "WithinYear", "Continuous", "User"
    u_star_seasoning="Continuous",
    
    is_to_apply_partitioning=True,
    
    # partitioning_methods: one or both of "Reichstein05", "Lasslop10"
    partitioning_methods=["Reichstein05", "Lasslop10"],
    
    latitude=56.5,
    longitude=32.6,
    timezone=+3.0,
    
    # "Tsoil"
    temperature_data_variable="Tair",
    
    # do not change
    site_id=config.site_name,
    u_star_method="RTw",
    is_to_apply_gap_filling=True,
    input_file=str(gl.rep_level3_fpath),
    output_dir=str(gl.out_dir / 'reddyproc'),
)

if not config.from_file:
    config.reddyproc = config_reddyproc

prepare_rg(config.reddyproc)
ensure_empty_dir(config.reddyproc.output_dir)
gl.rep_out_info, config.reddyproc = reddyproc_and_postprocess(config.reddyproc, gl.repo_dir)

# %% [markdown] id="0bed439c"
# ## Контрольные графики
# Отображение отдельных графиков из онлайн-инструмента в удобной для проверки форме.  
# Заполненные данные, графики и проверочную статистику можно скачать одним архивом по кнопке **Download eddyproc outputs**.
#
# **Дополнительные опции:**  
#   
# Порядок и набор графиков формируется автоматически в переменной `output_sequence`, которую также можно поменять или переобъявить с помощью тэгов.  
# Тэги именно для этого варианта тетради будут видны после запуска ячейки по вызову `display_tag_info`.

# %% id="e66a94ab"
rep_out_dir = Path(config.reddyproc.output_dir)
tag_handler = RepImgTagHandler(main_path=rep_out_dir, rep_cfg=config.reddyproc, rep_out_info=gl.rep_out_info,
                               img_ext='.png')
rog = RepOutputGen(tag_handler)

output_sequence: tuple[str | list[str], ...] = (
    "## Тепловые карты",
    rog.hmap_compare_row('NEE_*'),
    rog.hmap_compare_row('LE_f'),
    rog.hmap_compare_row('H_f'),
    "## Суточный ход",
    rog.diurnal_cycle_row('NEE_*'),
    rog.diurnal_cycle_row('LE_f'),
    rog.diurnal_cycle_row('H_f'),
    "## 30-минутные потоки и суточные средние",
    rog.flux_compare_row('NEE_*'),
    rog.flux_compare_row('LE_f'),
    rog.flux_compare_row('H_f')
)

roh = RepOutputHandler(output_sequence=output_sequence, tag_handler=tag_handler, out_info=gl.rep_out_info)
roh.prepare_images_safe()
gl.rep_arc_exclude_files = roh.img_proc.raw_img_duplicates

rep_arc_path = rep_out_dir / (gl.rep_out_info.fnames_prefix + '.zip')
create_archive(arc_path=rep_arc_path, dirs=rep_out_dir, top_dir=rep_out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt'], exclude_files=roh.img_proc.raw_img_duplicates)

colab_add_download_button(rep_arc_path, 'Download eddyproc outputs')

roh.display_images_safe()

tag_handler.display_tag_info(roh.extended_tags())

# %% [markdown] id="HEead6faY22W"
# # Выгрузка результатов
#
# Результаты работы всех сегментов тетради можно скачать одним архивом по кнопке **Download outputs**.  
#
# Если кнопка ниже не появилась, нужно запустить ячейку еще раз или скачать выходные файлы в разделе Файлы, директория output. В обобщающих файлах с индексами в названии _hourly (суточные ходы отфильтрованных, а также заполненных переменных), _daily (средние суточные значения), _monthly (средние месячные значения) и _yearly (значения за год, если данных меньше - за весь период обработки) индекс _sqc означает долю оставшихся после фильтраций значений (но без учета фильтра REddyProc на u*), а колонки с индексами _f означают итоговые заполненные данные после всех ячеек тетради.

# %% id="E4rv4ucOX8Yz"
FFConfig.save(config, gl.out_dir / f'config_{config.site_name}.yaml')

arc_path = gl.out_dir / 'FluxFilter_output.zip'
create_archive(arc_path=arc_path, dirs=[gl.out_dir, config.reddyproc.output_dir], top_dir=gl.out_dir,
               include_fmasks=['*.png', '*.csv', '*.txt', '*.log', '*.yaml'], exclude_files=gl.rep_arc_exclude_files)
colab_add_download_button(arc_path, 'Download outputs')
