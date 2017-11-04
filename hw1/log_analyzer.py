#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import collections
import json
from argparse import ArgumentParser
from datetime import datetime
import sys
import gzip
import glob
import re
import os

import math

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./Logs"
}


def parse_args():
    """
    Разбор аргументов командной строки

    Варианты запуска:
    $ ./log_analyzer.py
    $ ./log_analyzer.py --log_path                  (путь к лог файлу)
    $ ./log_analyzer.py -f json                     (сохранить в файле json)
    $ ./log_analyzer.py --log_path --format json    (путь к лог файлам + сохранение в файле json)
    """
    parser = ArgumentParser(description='Log Analyzer')
    parser.add_argument('-l', '--log_path', help='Путь к лог файлам')
    parser.add_argument('-j', '--json', help='Сохранить в json файл', action='store_true')
    return parser.parse_args()


# region Чтение файла
def get_latest_file(path):
    """Получение файла с максимальной датой(последнего файла)"""
    files = glob.glob("{0}{1}".format(path, '/nginx-access-ui.log-*.gz'))
    if files:
        latest_file = max(files, key=get_file_date)
        return latest_file
    return None


def get_file_date(path):
    """Получение даты из имени файла"""
    date = re.search(r'[0-9]{8}', path).group(0)
    if date:
        return datetime.strptime(date, '%Y%m%d')
    raise RuntimeError('Не правильный формат именования лог файла')


def read_file_by_rows(path):
    """Чтение файла по строкам"""
    if path.endswith(".gz"):
        log = gzip.open(path, 'rb')
    else:
        log = open(path)
    for line in log:
        yield line
    log.close()
# endregion


# region Анавлиз лог файла
def get_report(log, total_time, limit=100):
    """Получение отчета"""
    report = []
    one_percent = float(len(log) / 100.0)
    one_time_percent = float(total_time / 100.0)

    for url, times in log.items():
        count = len(times)
        time_sum = sum(times)
        report.append({
            'url': url,
            'time_max': max(times),
            'count': count,
            'time_sum': round(time_sum, 3),
            'count_perc': round(count / one_percent, 3),
            'time_perc': round(time_sum / one_time_percent, 3),
            'time_p50': round(percentile(times, 50), 3),
            'time_p95': round(percentile(times, 95), 3),
            'time_p99': round(percentile(times, 99), 3)
        })
    return report[:limit]


def parse_line(line):
    """Разбор строки"""
    url = "-"

    search_result = re.search(r'\s\/\S*', line)
    if search_result:
        url = search_result.group(0).rstrip()

    return {
        'url': url,
        'request_time': float(re.search(r'[0-9]*.[0-9]*$', line).group(0)),
    }


def percentile(lst, p):
    index = (p / 100.0) * len(lst)
    if math.floor(index) == index:
        result = (lst[int(index) - 1] + lst[int(index)]) / 2.0
    else:
        result = lst[int(math.floor(index))]
    return result


def log_analysis(path, is_json):
    """Анализ файла лога"""
    report_format = 'json' if is_json else 'html'
    report_date = datetime.strftime(get_file_date(path), '%Y.%m.%d')
    report_path = '{0}/report-{1}.{2}'.format(CONFIG['REPORT_DIR'], report_date, report_format)
    if os.path.isfile(report_path):
        print "Отчет {0} уже существует".format(report_path)
        sys.exit(0)
    print "Чтение {0} файла...".format(path)

    total_time = 0
    log = collections.defaultdict(list)
    try:
        for line in read_file_by_rows(path):
            parsed_line = parse_line(line)
            total_time += parsed_line['request_time']
            log[parsed_line['url']].append(parsed_line['request_time'])
        report = get_report(log, total_time, CONFIG['REPORT_SIZE'])
        report_save(report, report_path)
        print "Отчет сформирован в файле {0}".format(report_path)
    except Exception as err:
        print "Не корректные данные в лог файле {0}".format(path)
        print str(err)

# endregion


# region Сохрание отчета

def report_save(report, file_path):
    """Сохранение отчета"""
    if file_path.endswith('.html'):
        with open('report.html', 'r') as f:
            file_data = f.read()
        file_data = file_data.replace('$table_json', json.dumps(report))
        with open(file_path, 'w') as f:
            f.write(file_data)
    elif file_path.endswith('.json'):
        with open(file_path, 'w') as f:
            json.dump(report, f)
    else:
        raise RuntimeError('Unexpected report file format')

# endregion


def main():
    args = parse_args()
    log_path = args.log_path

    if log_path is None:
        log_path = get_latest_file(CONFIG['LOG_DIR'])

    if log_path:
        try:
            log_analysis(log_path, args.json)
        except Exception as err:
            print str(err)
            sys.exit(1)
    else:
        print "В директории {} не найдены файлы логов".format(CONFIG['LOG_DIR'])


if __name__ == "__main__":
    main()

    sys.argv.append('-j')
    main()
