#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Нужно реализовать простое HTTP API сервиса скоринга. Шаблон уже есть в api.py, тесты в test.py.
# API необычно тем, что польщователи дергают методы POST запросами. Чтобы получить результат
# пользователь отправляет в POST запросе валидный JSON определенного формата на локейшн /method

# Структура json-запроса:

# {"account": "<имя компании партнера>", "login": "<имя пользователя>", "method": "<имя метода>",
#  "token": "<аутентификационный токен>", "arguments": {<словарь с аргументами вызываемого метода>}}

# account - строка, опционально, может быть пустым
# login - строка, обязательно, может быть пустым
# method - строка, обязательно, может быть пустым
# token - строка, обязательно, может быть пустым
# arguments - словарь (объект в терминах json), обязательно, может быть пустым

# Валидация:
# запрос валиден, если валидны все поля по отдельности

# Структура ответа:
# {"code": <числовой код>, "response": {<ответ вызываемого метода>}}
# {"code": <числовой код>, "error": {<сообщение об ошибке>}}

# Аутентификация:
# смотри check_auth в шаблоне. В случае если не пройдена, нужно возвращать
# {"code": 403, "error": "Forbidden"}

# Метод online_score.
# Аргументы:
# phone - строка или число, длиной 11, начинается с 7, опционально, может быть пустым
# email - строка, в которой есть @, опционально, может быть пустым
# first_name - строка, опционально, может быть пустым
# last_name - строка, опционально, может быть пустым
# birthday - дата в формате DD.MM.YYYY, с которой прошло не больше 70 лет, опционально, может быть пустым
# gender - число 0, 1 или 2, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности и если присутсвует хоть одна пара
# phone-email, first name-last name, gender-birthday с непустыми значениями.

# Ответ:
# в ответ выдается произвольное число, которое больше или равно 0
# {"score": <число>}
# или если запрос пришел от валидного пользователя admin
# {"score": 42}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"score": 5.0}}

# Метод clients_interests.
# Аргументы:
# client_ids - массив числе, обязательно, не пустое
# date - дата в формате DD.MM.YYYY, опционально, может быть пустым

# Валидация аругементов:
# аргументы валидны, если валидны все поля по отдельности.

# Ответ:
# в ответ выдается словарь <id клиента>:<список интересов>. Список генерировать произвольно.
# {"client_id1": ["interest1", "interest2" ...], "client2": [...] ...}
# или если произошла ошибка валидации
# {"code": 422, "error": "<сообщение о том какое поле невалидно>"}

# $ curl -X POST  -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "token": "d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f24091386050205c324687a0", "arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
# -> {"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4": ["cinema", "geek"]}}

# Требование: в результате в git должно быть только два(2!) файлика: api.py, test.py.
# Deadline: следующее занятие

import re
import json
import datetime
import logging
import hashlib
import random
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from abc import ABCMeta, abstractmethod

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
EMPTY_VALUES = (None, (), [], {}, '')


# region Fields
class BaseField:
    """Базовый класс для полей"""
    __metaclass__ = ABCMeta

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    @abstractmethod
    def validate(self, value): pass


class CharField(BaseField):
    """Текстовоге поле"""

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError("Не верный тип параметра {0} - {1}. Праматр должен быть типа {2}".format(value, type(value), type(str)))


class ArgumentsField(BaseField):
    """Поле аргументов"""

    def validate(self, value):
        if not isinstance(value, dict):
            raise TypeError(
                "Не верный тип параметра {} - {}. Праматр должен быть типа {}".format(value, type(value), type(dict)))


class EmailField(CharField):
    """Поле e-mail"""

    def validate(self, value):
        super(EmailField, self).validate(value)
        if "@" not in value:
            raise TypeError("Не верный тип параметра {}. Должен быть e-mail : example@ex.com".format(value))


class PhoneField(BaseField):
    """Телефонный номер"""

    def validate(self, value):
        if not re.match(r'(^7[\d]{10}$)', str(value)):
            raise TypeError("Не верный тип параметра {}. Должен быть телефон, формат: 7ХХХХХХХХХХ".format(value))


class DateField(BaseField):
    """Дата в формате ДД.ММ.ГГГГ"""

    def validate(self, value):
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise TypeError("Не верный тип параметра {}. Должена быть дата, формат: ДД.ММ.ГГГГ".format(value))


class BirthDayField(DateField):
    """День рожденье(не больше 70)"""

    def validate(self, value):
        super(BirthDayField, self).validate(value)
        if (datetime.datetime.today() - datetime.datetime.strptime(value, '%d.%m.%Y')).days / 365 > 70:
            raise TypeError(
                "Не верный тип параметра {}. Должена быть дата, формат: ДД.ММ.ГГГГ,(не более 70 лет)".format(value))


class GenderField(BaseField):
    """Пол"""

    def validate(self, value):
        if value not in GENDERS:
            raise TypeError(
                "Не верный тип параметра {}. Пол задается цифрой: 1(unknown), 2(male) или 3(female)".format(value))


class ClientIDsField(BaseField):
    """Идентификато клиента"""

    def validate(self, values):
        if not isinstance(values, list):
            raise TypeError("Не верный тип параметра {0}. Праматр должен быть типа {1}".format(values, type(list)))
        if not all(isinstance(item, int) and item >= 0 for item in values):
            raise TypeError("Не верный тип параметра {0}. Все значения должны быть больше 0".format(values))


# endregion

# region Request

class MetaRequest(type):
    """Метакласс запроса """

    def __new__(mcs, name, bases, attributes):
        fields = []
        for field_name, field in attributes.items():
            if isinstance(field, BaseField):
                field._name = field_name
                fields.append((field_name, field))

        new_class = super(MetaRequest, mcs).__new__(mcs, name, bases, attributes)
        new_class.fields = fields
        return new_class


class Request(object):
    """Запрос"""
    __metaclass__ = MetaRequest

    def __init__(self, **kwargs):
        self._errors = {}
        self.base_fields = []
        for field, value in kwargs.items():
            setattr(self, field, value)
            self.base_fields.append(field)

    def validate(self):
        for name, field in self.fields:
            if name not in self.base_fields:
                if field.required:
                    self._errors[name] = "Обязательно поле"
                continue

            value = getattr(self, name)
            if value in EMPTY_VALUES and not field.nullable:
                self._errors[name] = "Поле не может быть пустым"

            try:
                field.validate(value)
            except TypeError as ex:
                self._errors[name] = ex.message

    @property
    def errors(self):
        return self._errors

    def is_valid(self):
        return not self.errors


class ClientsInterestsRequest(Request):
    """Запрос интересов клиента"""
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    """Запрос на онлайн-счет"""

    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super(OnlineScoreRequest, self).validate()
        if not self._errors:
            pairs = [
                ("phone", "email"),
                ("first_name", "last_name"),
                ("gender", "birthday")
            ]
            if not any(all(name in self.base_fields for name in fields) for fields in pairs):
                self._errors["arguments"] = "Не корректный список аргументов"


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=True)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


# endregion


def check_auth(request):
    """проверка аутентификации"""
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


# region Handler
class ClientsInterestsHandler(object):
    """Обработчик запросов клиента"""
    interests = ["Coding", "Python", "DevOps", "Books", "Music", "Cars", "Travel", "Snowboarding"]

    def processing_handler(self, request, context):
        client_interests = ClientsInterestsRequest(**request.arguments)
        client_interests.validate()
        if not client_interests.is_valid():
            return client_interests.errors, INVALID_REQUEST

        response = {cid: random.sample(self.interests, 2) for cid in client_interests.client_ids}
        context["nclients"] = len(client_interests.client_ids)
        return response, OK


class OnlineScoreHandler(object):
    """Обработка онлайн-оценки"""

    def processing_handler(self, request, context):
        online_score = OnlineScoreRequest(**request.arguments)
        online_score.validate()
        if not online_score.is_valid():
            return online_score.errors, INVALID_REQUEST

        context["has"] = online_score.base_fields
        score = 42 if request.is_admin else random.randint(0, 100)
        return {"score": score}, OK


def method_handler(request, ctx):
    handlers = {
        "clients_interests": ClientsInterestsHandler,
        "online_score": OnlineScoreHandler,
    }
    try:
        method_request = MethodRequest(**request["body"])
    except Exception as ex:
        return ex.message, INVALID_REQUEST

    method_request.validate()

    if not method_request.is_valid():
        return method_request.errors, INVALID_REQUEST
    if not check_auth(method_request):
        return "Forbidden", FORBIDDEN

    return handlers[method_request.method]().processing_handler(method_request, ctx)


# endregion

class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, str, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
