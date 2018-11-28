# -*- coding: utf-8 -*-

from typing import Any, Callable, Dict, List, Optional, Union, NewType, Iterable, TypeVar
from sysinfo import monitor
from unittest.mock import MagicMock



def test_info():
    meta = monitor.Meta2(path='/test/123')

    monitor.load_json_data_from_json_file = MagicMock()
    monitor.load_json_data_from_json_file.return_value = 'test'

    monitor.monitor_generator = MagicMock()
    monitor.monitor_generator.return_value = None

    monitor.info(meta)

    monitor.load_json_data_from_json_file.assert_called_with(meta.path)
