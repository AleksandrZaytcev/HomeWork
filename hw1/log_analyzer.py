#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import argparse
import gzip
import glob
import sys
import re
import datetime

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
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
    parser = argparse.ArgumentParser(description='Log Analyzer')
    parser.add_argument('-l', '--log_path', help='Путь к лог файлам')
    parser.add_argument('-j', '--json', help='Сохранить в json файл', action='store_true')
    return parser.parse_args()


# region Чтение файла
def get_latest_file(path):
    files = glob.glob("{0}{1}".format(path, '/nginx-access-ui.log-*'))
    if files:
        latest_file = max(files, key=get_file_date)
        return latest_file
    return None


def get_file_date(path):
    file_date = re.match(r'^.*-(\d+)\.?\w*$', path)
    if file_date:
        return datetime.strptime(file_date.group(1), '%Y%m%d')
    raise RuntimeError('Не правильный формат именования лог файла')


# endregion



def read_file_by_rows(path):
    if path.endswith(".gz"):
        log = gzip.open(path, 'rb')
    else:
        log = open(path)
    for line in log:
        yield line
    log.close()


def main():
    args = parse_args()
    log_path = args.log_path

    if log_path is None:
        log_path = get_latest_file(CONFIG['LOG_DIR'])

    if log_path:
        try:
            #  todo реализовать анлаиз лог файла
        except Exception as err:
            print str(err)
            sys.exit(1)
    else:
        print "В директории {} не найдены файлы логов".format(CONFIG['LOG_DIR'])


if __name__ == "__main__":
    main()
