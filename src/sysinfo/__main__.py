# -*- coding: utf-8 -*-

import argparse
import json
import os
import pkg_resources
import platform

from . import monitor


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', default='', help='json script path')
    parser.add_argument('-d', '--default', default=False, help='use default script', action='store_true')
    parser.add_argument('-show', '-show--defaultscript', default='', help='show default json script', action='store_true')
    return parser.parse_args(), parser


def create_default_json_file():
    config_dir = os.getenv('APPDATA') if platform.system() == "Windows" \
        else os.path.expandvars(os.path.join("$HOME", ".config"))
    default_json = os.path.join(config_dir, 'Flo', 'built_in.json')

    if os.path.isfile(default_json):
        return default_json

    built_in_func = ('cpu_info', 'disk_info', 'process_info', 'swap_info', 'memory_info', 'netstat_info')
    data = {}
    for func in built_in_func:
        meta = {
            "__meta__": {
                "type": "built_in",
                "func": "",
                "args": [],
                "kwargs": {},
                "rtype": "string",
                "concurrent": False
            }
        }

        meta['__meta__']['func'] = func
        data[func] = meta

    with open(default_json, 'w') as f:
        json.dump(data, f)

    return default_json


def default_json_file():
    return pkg_resources.resource_filename(__name__, 'etc/built_in.json')


def main():
    args, argsrser = parse_args()

    source_path = None
    if args.show:
        print(json.dumps(monitor.load_json_data_from_json_file(path=default_json_file())))

    elif args.source:
        source_path = args.source

    elif args.default:
        source_path = default_json_file()
        if not os.path.isfile(source_path):
            source_path = create_default_json_file()


    if source_path:
        data = monitor.load_json_data_from_json_file(path=source_path)
        result = monitor.monitor_generator(data=data)

        j = json.dumps(result)

        print(j)

if __name__ == '__main__':
    main()
