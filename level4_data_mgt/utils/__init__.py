# -*- coding: utf-8 -*-
from level4_data_mgt import app
from flask import url_for
from urllib.parse import urlparse, urlunparse
import hashlib

def url(endpoint, absolute=None, scheme=None, **kwargs):
    endpoint = endpoint if endpoint is not None else request.endpoint
    o = urlparse(url_for(endpoint, _external=absolute, **kwargs))
    app.logger.info(o, kwargs)
    if absolute:
        scheme = scheme if scheme is not None else o.scheme
        return urlunparse((scheme, o.netloc, o.path, "", o.query, ""))
    return urlunparse(("", "", o.path, "", o.query, ""))

def gen_md5(string):
    return hashlib.md5(string).hexdigest()

def merge_expr_obj(dict1, dict2):
    result = {}
    keys = dict1.keys()
    for key in keys:
        if isinstance(dict1.get(key), list):
            result[key] = dict1.get(key)
            result[key][0:0] = dict2.get(key)
        elif isinstance(dict1.get(key), str):
            if dict1.get(key) == dict2.get(key):
                result[key] = dict1.get(key)
            else:
                result[key] = [dict1.get(key)]
                if isinstance(dict2.get(key), str):
                    result[key][0:0] = [dict2.get(key)]
                else:
                    result[key][0:0] = dict2.get(key)
    return result

def merge_dicts(func, *args):
    # 返回空列表
    if len(args) == 0:
        return args
    if len(args) == 1:
        return args[0]
    else:
        return func(args[0], merge_dicts(func, *args[1:]))

def uniq_item(dict1):
    for key, value in dict1.items():
        if isinstance(value, list) and len(set(value)) == 1:
            dict1[key] = list(set(value))
    return dict1