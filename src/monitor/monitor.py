# -*- coding: utf-8 -*-
import os
import sys

import json
import jsontofu
import jsonpickle
import psutil
import socket

from typing import Any, Dict, List, Optional, NewType, TypeVar
from subprocess import Popen, PIPE
from dataclasses import dataclass

af_map = {
    socket.AF_INET: 'IPv4',
    socket.AF_INET6: 'IPv6',
    psutil.AF_LINK: 'MAC',
}

duplex_map = {
    psutil.NIC_DUPLEX_FULL: "full",
    psutil.NIC_DUPLEX_HALF: "half",
    psutil.NIC_DUPLEX_UNKNOWN: "?",
}


@dataclass
class Meta:
    type: str
    func: Optional[str] = None
    cmd: Optional[str] = None
    concurrent: Optional[bool] = None
    rtype: Optional[str] = 'json'
    path: Optional[str] = None
    args: Optional[List] = None
    kwargs: Optional[Dict] = None


class BuiltIn:

    @staticmethod
    def cpu_info(*args, **kwargs) -> dict:
        result: dict = {}
        result['loadavg'] = os.getloadavg()
        result['percent'] = psutil.cpu_percent(interval=1)
        result['count'] = psutil.cpu_count()
        return result

    @staticmethod
    def process_info(*args, **kwargs) -> dict:
        result: dict = {}

        attrs = ['pid', 'cpu_percent', 'memory_percent', 'name', 'cpu_times',
                 'create_time', 'memory_info', 'status']

        for p in psutil.process_iter():
            try:
                pinfo = p.as_dict(attrs, ad_value='')
            except psutil.NoSuchProcess:
                continue

            try:
                user = p.username()
            except KeyError:
                if os.name == 'posix':
                    if pinfo['uids']:
                        user = str(pinfo['uids'].real)
                    else:
                        user = None
                else:
                    raise
            except psutil.Error:
                user = None

            sub_config = {}
            sub_config['user'] = user
            sub_config['command'] = pinfo['name'].strip() or '?'
            result[pinfo['pid']] = sub_config

        return result

    @classmethod
    def memory_info(cls, *args, **kwargs) -> dict:
        return cls.namedtuple_to_dict(psutil.virtual_memory())

    @classmethod
    def swap_info(cls, *args, **kwargs) -> dict:
        return cls.namedtuple_to_dict(psutil.swap_memory())

    @classmethod
    def disk_info(cls, *args, **kwargs) -> dict:
        return cls.namedtuple_to_dict(psutil.disk_usage('/'))

    @staticmethod
    def protocol_port_info() -> list:
        return [pconn.laddr.port for pconn in psutil.net_connections() if pconn]

    @classmethod
    def network_info(cls, *args, **kwargs) -> dict:
        ifconfig: dict = {}
        stats = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)
        for nic, addrs in psutil.net_if_addrs().items():
            sub_config = {}
            if nic in stats:
                stat: dict = {}
                st = stats[nic]
                stat['speed'] = st.speed
                stat['duplex'] = duplex_map[st.duplex]
                stat['mtu'] = st.mtu

                ifconfig['stats'] = stat

            if nic in io_counters:
                incoming: dict = {}
                outgoing: dict = {}
                io = io_counters[nic]
                incoming['bytes'] = io.bytes_recv
                incoming['pkts'] = io.packets_recv
                incoming['errs'] = io.errin
                incoming['drops'] = io.dropin

                outgoing['bytes'] = io.bytes_sent
                outgoing['pkts'] = io.packets_sent
                outgoing['errs'] = io.errin
                outgoing['drops'] = io.dropin

                sub_config['incomming'] = incoming
                sub_config['outgoing'] = outgoing

            for addr in addrs:
                family: dict = {}
                family['address'] = addr.address
                if addr.broadcast: family['broadcast'] = addr.broadcast
                if addr.netmask: family['netmask'] = addr.netmask
                if addr.ptp: family['p2p'] = addr.ptp
                sub_config[af_map.get(addr.family, addr.family)] = family

            ifconfig[nic] = sub_config

        return ifconfig

    @staticmethod
    def namedtuple_to_dict(res) -> dict:
        data: dict = {}
        for k in res._fields:
            data[k] = getattr(res, k)

        return data


def load_json_data_from_json_file(path: str) -> dict:
    data: dict = None
    with open(path) as json_data_file:
        data = json.load(json_data_file)

    return data


def dict_objectization(data: dict, clz):
    try:
        obj = jsontofu.decode(data, clz)
        obj
    except Exception as e:
        print(data)
        print("error = ", e)
        obj = None

    return obj


def r_type_generator(res: str, rtype: str):
    result = None

    try:
        if rtype == 'json':
            result = json.loads(res)
        elif rtype == 'string':
            result = str(res)
        elif rtype == 'integer':
            result = int(res)
        else:
            result = res
    except json.JSONDecodeError:
        result = res

    return result


def built_in(meta: Meta) -> str:
    try:
        info = getattr(BuiltIn, meta.func)(meta.args, meta.kwargs)
    except AttributeError:
        return "BuiltIn is not able to handle {}".format(str(meta.func))

    return json.dumps(info)


def executable(meta: Meta) -> str:
    stdout, stderr = Popen([meta.cmd] + meta.args, stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate()
    return stdout.decode('utf-8')


def shell(meta: Meta) -> str:
    stdout, stderr = Popen(meta.cmd, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate()
    return stdout.decode('utf-8')


def info(meta: Meta) -> str:
    return json.dumps(monitor_generator(data=load_json_data_from_json_file(meta.path)))


def monitor_generator(data: dict):
    reflection_reality_data = None
    keys = data.keys()

    if '__meta__' in keys:
        meta = dict_objectization(data['__meta__'], Meta)
        res = getattr(sys.modules[__name__], meta.type)(meta)
        return r_type_generator(res, meta.rtype)

    else:
        reflection_reality_data = {}

        for k in keys:
            d = monitor_generator(data[k])
            reflection_reality_data[k] = d

    return reflection_reality_data


if __name__ == '__main__':
    data = load_json_data_from_json_file(path='/Users/rondouchen/workspace/Flo/reality_monitor/etc/reality_monitor.json')
    result = monitor_generator(data=data)

    j = json.dumps(result)

    print(j)
