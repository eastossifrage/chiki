# coding: utf-8
import re
import os
import sys
import time
import random
import string
import traceback
import requests
from datetime import datetime, date
from StringIO import StringIO
from flask import jsonify, current_app, request

__all__ = [
    'strip', 'json_success', 'json_error',
    'datetime2best', 'time2best', 'today',
    'err_logger', 'parse_spm', 'get_spm', 'get_version', 'get_os', 'get_platform',
    'get_channel', 'get_ip', 'is_ajax', 'str2datetime', 'is_json', 'is_empty',
    'randstr', 'AttrDict', 'url2image', 'retry', 'tpl_data', 'get_module',
]


def down(url, source=None):
    if source:
        return StringIO(requests.get(url, headers=dict(Referer=source)).content)
    return StringIO(requests.get(url).content)


def get_format(image):
    format = image.split('.')[-1]
    if format in ['jpg', 'jpeg']:
        return 'jpg'
    if format in ['gif', 'bmp', 'png', 'ico']:
        return format
    return ''


def url2image(url, source=None):
    return dict(stream=down(url, source=source), format=get_format(url)) if url else None


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def today():
    return datetime.strptime(str(date.today()), '%Y-%m-%d')


def strip(val, *args):
    if not val:
        return val

    if isinstance(val, dict):
        return dict((x, strip(y) if x not in args else y) for x, y in val.iteritems())
    if isinstance(val, list):
        return list(strip(x) for x in val)
    if hasattr(val, 'strip'):
        return val.strip()
    return val


def json_success(**kwargs):
    kwargs['code'] = 0
    return jsonify(kwargs)


def json_error(**kwargs):
    kwargs['code'] = -1
    return jsonify(kwargs)


def datetime2best(input):
    tmp = datetime.now() - input
    if tmp.days in [0, -1]:
        seconds = tmp.days * 86400 + tmp.seconds
        if seconds < -3600:
            return '%d小时后' % (-seconds // 3600)
        elif seconds < -60:
            return '%d分钟后' % (-seconds // 60)
        elif seconds < 0:
            return '%d秒后' % -seconds
        elif seconds < 60:
            return '%d秒前' % seconds
        elif seconds < 3600:
            return '%d分钟前' % (seconds // 60)
        else:
            return '%d小时前' % (seconds // 3600)
    elif tmp.days < -365:
        return '%d年后' % (-tmp.days // 365)
    elif tmp.days < -30:
        return '%d个月后' % (-tmp.days // 30)
    elif tmp.days < -1:
        return '%d天后' % -(tmp.days + 1)
    elif tmp.days < 30:
        return '%d天前' % tmp.days
    elif tmp.days < 365:
        return '%d个月前' % (tmp.days // 30)
    else:
        return '%d年前' % (tmp.days // 365)


def time2best(input):
    if type(input) != datetime:
        input = datetime.fromtimestamp(input)
    return datetime2best(input)


def err_logger(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            current_app.logger.error(traceback.format_exc())
    return wrapper


def parse_spm(spm):
    if spm:
        spm = spm.replace('unknown', '0')
    if spm and re.match(r'^(\d+\.)+\d+$', spm):
        res = map(lambda x: int(x), spm.split('.'))
        while len(res) < 5: res.append(0)
        return res[:5]
    return 0, 0, 0, 0, 0


def get_spm():
    spm = request.args.get('spm')
    if spm:
        return spm

    spm = []
    oslist = ['ios', 'android', 'windows', 'linux', 'mac']
    plist = ['micromessenger', 'weibo', 'qq']
    ua = request.args.get('User-Agent', '').lower()

    for index, os in enumerate(oslist):
        if os in ua:
            spm.append(index + 1)
            break
    else:
        spm.append(index + 1)

    for index, p in enumerate(plist):
        if p in ua:
            spm.append(index + 1)
            break
    else:
        spm.append(index + 1)

    spm.append(1001)
    spm.append(0)

    return '.'.join([str(x) for x in spm])


def get_version():
    return parse_spm(get_spm())[3]


def get_channel():
    return parse_spm(get_spm())[2]


def get_os():
    return parse_spm(get_spm())[0]


def get_platform():
    return parse_spm(get_spm())[1]


def get_ip():
    if 'Cdn-Real-Ip' in request.headers:
        return request.headers['Cdn-Real-Ip']
    if 'X-Real-Forwarded-For' in request.headers:
        return request.headers['X-Real-Forwarded-For'].split(',')[0]
    if 'X-FORWARDED-FOR' in request.headers:
        return request.headers['X-FORWARDED-FOR'].split(',')[0]
    return request.headers.get('X-Real-Ip') or request.remote_addr


def is_ajax():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.args.get('is_ajax', 'false') == 'true' \
        or request.headers['Accept'].startswith('application/json')


def is_api():
    return 'API' in current_app.config.get('ENVVAR', '')


def is_json():
    return is_api() or is_ajax()


def is_empty(fd):
    fd.seek(0)
    first_char = fd.read(1)
    fd.seek(0)
    return not bool(first_char)


def str2datetime(datestr):
    try:
        return datetime.strptime(datestr, '%Y-%m-%d %H:%M:%s')
    except ValueError:
        return datetime.min


def randstr(x=32):
    a = lambda: random.choice(string.ascii_letters + string.digits)
    return ''.join(a() for _ in range(x))


def retry(times=3):
    def wrapper(func):
        for i in range(times):
            try:
                func()
                break
            except:
                pass
        return func
    return wrapper


def tpl_data(color="#33aaff", **kwargs):
    res = dict()
    for key, value in kwargs.iteritems():
        res[key] = dict(value=value, color=color)
    return res


def get_module():

    def main_module_name():
        mod = sys.modules['__main__']
        file = getattr(mod, '__file__', None)
        return file and os.path.splitext(os.path.basename(file))[0]

    def modname(fvars):

        file, name = fvars.get('__file__'), fvars.get('__name__')
        if file is None or name is None:
            return None

        if name == '__main__':
            name = main_module_name()
        return name

    return modname(globals())
