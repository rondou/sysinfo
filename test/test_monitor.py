# -*- coding: utf-8 -*-

from typing import Any, Callable, Dict, List, Optional, Union, NewType, Iterable, TypeVar
from src.sysinfo import monitor
import json


def test_info_meta_path(mocker):
    meta = monitor.Meta2(path='/test/1')

    load_json_data_from_json_file = mocker.patch('src.sysinfo.monitor.load_json_data_from_json_file', return_value=None)
    mocker.patch('src.sysinfo.monitor.monitor_generator', return_value=None)

    monitor.info(meta)

    load_json_data_from_json_file.assert_called_with(meta.path)


def test_info_dump_json(mocker):
    meta = monitor.Meta2(path='/test/2')

    mocker.patch('src.sysinfo.monitor.load_json_data_from_json_file', return_value=None)
    mocker.patch('src.sysinfo.monitor.monitor_generator', return_value={"key1": 123, "key2": "456", "key3": True})

    assert json.loads(monitor.info(meta)) == json.loads('{"key3": true, "key1": 123, "key2": "456"}')


def test_info_raises(mocker):
    meta = monitor.Meta2(path='/test/3')
    mocker.patch('src.sysinfo.monitor.load_json_data_from_json_file',
                 side_effect=json.JSONDecodeError(msg='test', doc='{"keys"}', pos=7))

    assert monitor.info(meta) == 'JSONDecodeError'


def test_load_json_file(mocker):
    json_load = mocker.patch('json.load', return_value=None)

    with mocker.patch('builtins.open', new_callable=mocker.mock_open()) as m:
        monitor.load_json_data_from_json_file('/test/4')

        m.assert_called_once_with('/test/4')
        assert json_load.called


def test_dict_objectization2(mocker):
    meta = {
      "type": "built_in",
      "func": "process_info",
      "args": [],
      "kwargs": {},
      "rtype": "string",
      "concurrent": True
    }

    dict_obj2 = mocker.patch('jsonpickle.decode', return_value=None)
    monitor.dict_objectization2(meta, monitor.Meta2)

    assert json.loads(dict_obj2.call_args[0][0]) == json.loads('''
                                                               {"type": "built_in",
                                                                "args": [],
                                                                "rtype": "string",
                                                                "kwargs": {},
                                                                "concurrent": true,
                                                                "func": "process_info",
                                                                "py/object": "src.sysinfo.monitor.Meta2"}
                                                               ''')
