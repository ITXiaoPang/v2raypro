#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import json
import base64
import getpass
import requests


__author__ = "ITXiaoPang"
__mtime__ = "2018/7/11"


v2ray_1 =\
    ""
v2ray_2 = v2ray_1

v2ray_list = (v2ray_1,)
cache = "/tmp/V2Ray.txt"


curr_user = getpass.getuser()
v2ray_conf_path = f"/Users/{curr_user}/syncthing/Settings/V2Ray/"
v2ray_template = f"config.json.example"

v2ray_proxy_flag_start = "//proxy_start"
v2ray_proxy_flag_end = "//proxy_end"

v2ray_conf = f"{v2ray_conf_path}/config.json"


all_proxy_code = []
all_proxy_decode = []


def check_file_r_ok(_file: str):
    if os.path.exists(_file) and os.access(_file, os.R_OK):
        ret = 0
    else:
        ret = 1
        print(f"文件不存在或不可读：{_file}")
    return ret


def check_file_w_ok(_file: str):
    if not os.path.exists(_file):
        try:
            with open(_file, mode="w", encoding="utf-8") as f:
                f.close()
        except IOError:
            print(f"文件创建失败:{_file}")

    if os.access(_file, os.W_OK):
        ret = 0
    else:
        ret = 2
        print(f"文件不可写：{_file}")
    return ret


def check_env(checkpoints: list):
    return list(filter(lambda x: x if x != 0 else False, checkpoints))


def update_cache():
    print("开始更新缓存")
    list_text = ''
    for curr_list_url in v2ray_list:
        print(f"读取{curr_list_url}")
        try:
            my_response = requests.get(curr_list_url)
            if my_response.status_code == requests.codes.ok:
                list_text = ''.join([list_text, my_response.text, os.linesep])
            else:
                print(f'读取失败:{my_response.status_code}，跳过该订阅')
        except Exception as ex_update_cache:
            print(ex_update_cache)
            print(f'读取失败:{my_response.status_code}，跳过该订阅')
            continue

    print(f"写入文件{cache}")
    try:
        with open(cache, mode="w", encoding="utf-8") as f:
            f.write(list_text)
    except IOError as ex_update_cache:
        print(f"缓存更新失败，错误：{ex_update_cache}")
    else:
        print(f"缓存更新成功:{cache}")


def base64decode(my_str: str):
    missing_padding = 4 - len(my_str) % 4
    if missing_padding:
        my_str += '=' * missing_padding
    return base64.urlsafe_b64decode(my_str)


def decode_cache():
    if check_file_r_ok(cache) == 0:
        print(f"读取文件{cache}")
        try:
            with open(cache, mode="r", encoding="utf-8") as f_chinalist_cache:
                f_chinalist_cache_lines = f_chinalist_cache.readlines()
                for curr_line in f_chinalist_cache_lines:
                    level_1 = str(base64decode(curr_line).decode()).split('\n')
                    level_2 = list(filter(lambda x: x if x != '' else False, level_1))
                    all_proxy_code.extend(level_2)
        except IOError as ex:
            print(f"缓存读取失败，错误：{ex}")

        level_3 = list(map(lambda x: base64decode(str(x).replace('vmess://', '')).decode(), all_proxy_code))
        for curr_proxy in level_3:
            all_proxy_decode.append(
                json.loads(curr_proxy)
            )


def generate_proxy():
    templates = []
    for i in all_proxy_decode:
        template = {
          "address": i["add"],
          "port": int(i["port"]),
          "users": [
            {
              "id": i["id"],
              "alterId": int(i["aid"]),
              "security": i["type"],
              "level": 0
            }
          ],
          "remark": i["ps"]
        }
        templates.append(json.dumps(template))
    ret = ','.join(templates)
    return ret


def write_to_template():
    try:
        print(f"读取模板{v2ray_template}")
        with open(v2ray_template, mode="r", encoding="utf-8") as f_v2ray_template:
            v2ray_template_text = f_v2ray_template.read()
        comment_proxy = re.compile(f"{v2ray_proxy_flag_start}(.*?){v2ray_proxy_flag_end}", re.DOTALL)
        if comment_proxy.findall(v2ray_template_text):
            result_proxy, number_proxy = comment_proxy.subn(generate_proxy(), v2ray_template_text)
            print(f"写入规则文件{v2ray_conf}")
            with open(v2ray_conf, mode="w", encoding="utf-8") as f_v2ray_gfw_conf:
                f_v2ray_gfw_conf.write(result_proxy)
        else:
            raise ModuleNotFoundError
    except IOError as ex:
        print(f"规则写入失败，错误：{ex}")
    except ModuleNotFoundError:
        print(f"未找到指定标记{v2ray_proxy_flag_start}和{v2ray_proxy_flag_end}")
    else:
        print("规则写入成功")


if __name__ == "__main__":
    err_codes = check_env(
        [
            check_file_r_ok(v2ray_template),
            check_file_w_ok(cache),
            check_file_w_ok(v2ray_conf)
        ]
    )
    if err_codes:
        print("程序退出。")
        exit(err_codes[0])

    update_cache()
    decode_cache()
    all_proxy_decode = list(filter(lambda x: x if '.' in x['add'] else False, all_proxy_decode))
    write_to_template()
