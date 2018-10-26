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
    def cpu_info() -> dict:
        result: dict = {}
        result['loadavg'] = os.getloadavg()
        result['percent'] = psutil.cpu_percent(interval=1)
        result['count'] = psutil.cpu_count()
        return result

    @classmethod
    def disk_info(cls) -> dict:
        return cls.namedtuple_to_dict(psutil.disk_usage('/'))

    @staticmethod
    def protocol_port_info() -> list:
        return [pconn.laddr.port for pconn in psutil.net_connections() if pconn]

    @staticmethod
    def bytes2human(n):
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.2f%s' % (value, s)
        return '%.2fB' % (n)

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
                incoming['bytes'] = cls.bytes2human(io.bytes_recv)
                incoming['pkts'] = io.packets_recv
                incoming['errs'] = io.errin
                incoming['drops'] = io.dropin

                outgoing['bytes'] = cls.bytes2human(io.bytes_sent)
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

    if rtype == 'json':
        result = json.loads(res)
    elif rtype == 'string':
        result = str(res)

    return result


def built_in(meta: Meta) -> str:
    info = getattr(BuiltIn, meta.func)(meta.args, meta.kwargs)

    return json.dumps(info)

    #return "in_progress"


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
        #print(meta)
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
