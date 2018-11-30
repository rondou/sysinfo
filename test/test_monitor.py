# -*- coding: utf-8 -*-

from typing import Any, Callable, Dict, List, Optional, Union, NewType, Iterable, TypeVar
from sysinfo import monitor
import json


def test_info_meta_path(mocker):
    meta = monitor.Meta2(path='/test/1')

    load_json_data_from_json_file = mocker.patch('sysinfo.monitor.load_json_data_from_json_file', return_value=None)
    mocker.patch('sysinfo.monitor.monitor_generator', return_value=None)

    monitor.info(meta)

    load_json_data_from_json_file.assert_called_with(meta.path)


def test_info_dump_json(mocker):
    meta = monitor.Meta2(path='/test/2')

    mocker.patch('sysinfo.monitor.load_json_data_from_json_file', return_value=None)
    mocker.patch('sysinfo.monitor.monitor_generator', return_value={"key1": 123, "key2": "456", "key3": True})

    assert json.loads(monitor.info(meta)) == json.loads('{"key3": true, "key1": 123, "key2": "456"}')


def test_info_raises(mocker):
    meta = monitor.Meta2(path='/test/3')
    mocker.patch('sysinfo.monitor.load_json_data_from_json_file',
                 side_effect=json.JSONDecodeError(msg='test', doc='{"keys"}', pos=7))

    assert monitor.info(meta) == 'JSONDecodeError'


def test_load_json_file(mocker):
    json_load = mocker.patch('json.load', return_value=None)

    with mocker.patch('builtins.open', new_callable=mocker.mock_open()) as m:
        monitor.load_json_data_from_json_file('/test/4')

        m.assert_called_once_with('/test/4')
        assert json_load.called
