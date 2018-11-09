# -*- coding: utf-8 -*-
import os
import sys

import json
import jsonpickle
import psutil
import socket

from subprocess import Popen, PIPE

AF_INET6 = getattr(socket, 'AF_INET6', object())

proto_map = {
    (socket.AF_INET, socket.SOCK_STREAM): 'tcp',
    (AF_INET6, socket.SOCK_STREAM): 'tcp6',
    (socket.AF_INET, socket.SOCK_DGRAM): 'udp',
    (AF_INET6, socket.SOCK_DGRAM): 'udp6',
}

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


class Meta2:
    type = None
    func = None
    cmd = None
    concurrent = None
    rtype = 'json'
    path = None
    args = None
    kwargs = None

    def __init__(self,
                type = None,
                func = None,
                cmd = None,
                concurrent = None,
                rtype = 'json',
                path = None,
                args = None,
                kwargs = None):

        self.type = type
        self.func = func
        self.cmd = cmd
        self.concurrent = concurrent
        self.rtype = rtype
        self.path = path
        self.args = args
        self.kwargs = kwargs


class BuiltIn:

    @staticmethod
    def cpu_info(*args, **kwargs) -> dict:
        retdict = {}
        retdict['loadavg'] = os.getloadavg()
        retdict['percent'] = psutil.cpu_percent(interval=1)
        retdict['count'] = psutil.cpu_count()
        return retdict

    @staticmethod
    def process_info(*args, **kwargs) -> dict:
        retdict = {}

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
            retdict[pinfo['pid']] = sub_config

        return retdict

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

    @staticmethod
    def netstat_info(*args, **kwargs) -> list:
        retlist = []

        proc_names = {}
        for p in psutil.process_iter():
            p_dict = p.as_dict(attrs=['pid', 'name'])
            proc_names[p_dict['pid']] = p_dict['name']

        for c in psutil.net_connections(kind='inet'):
            netstat = {}
            netstat['proto'] = proto_map[(c.family, c.type)]
            netstat['laddr'] = "%s:%s" % (c.laddr)
            netstat['raddr'] = "%s:%s" % (c.raddr) if c.raddr else '-'
            netstat['procname'] = proc_names.get(c.pid, '?')[:15]
            netstat['pid'] = c.pid or '-'

            retlist.append(netstat)

        return retlist

    @classmethod
    def network_info(cls, *args, **kwargs) -> dict:
        ifconfig = {}
        stats = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)
        for nic, addrs in psutil.net_if_addrs().items():
            sub_config = {}
            if nic in stats:
                stat = {}
                st = stats[nic]
                stat['speed'] = st.speed
                stat['duplex'] = duplex_map[st.duplex]
                stat['mtu'] = st.mtu

                ifconfig['stats'] = stat

            if nic in io_counters:
                incoming = {}
                outgoing = {}
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
                family = {}
                family['address'] = addr.address
                if addr.broadcast: family['broadcast'] = addr.broadcast
                if addr.netmask: family['netmask'] = addr.netmask
                if addr.ptp: family['p2p'] = addr.ptp
                sub_config[af_map.get(addr.family, addr.family)] = family

            ifconfig[nic] = sub_config

        return ifconfig

    @staticmethod
    def namedtuple_to_dict(res) -> dict:
        data = {}
        for k in res._fields:
            data[k] = getattr(res, k)

        return data


def load_json_data_from_json_file(path: str) -> dict:
    data = None
    with open(path) as json_data_file:
        data = json.load(json_data_file)

    return data


def dict_objectization2(data: dict, clz):
    data['py/object'] = ".".join([clz.__module__, clz.__name__])
    return jsonpickle.decode(json.dumps(data))


def r_type_generator(res: str, rtype: str):
    result = None

    try:
        if rtype == 'json':
            result = json.loads(res)
        elif rtype == 'string':
            result = str(res)
        elif rtype == 'integer':
            result = int(res)
        elif rtype == 'splitlines':
            result = json.loads(json.dumps(list(res.splitlines())))
        else:
            result = res
    except json.JSONDecodeError:
        result = res

    return result


def built_in(meta) -> str:
    try:
        info = getattr(BuiltIn, meta.func)(meta.args, meta.kwargs)
    except AttributeError:
        return "BuiltIn is not able to handle {}".format(str(meta.func))

    return json.dumps(info)


def executable(meta) -> str:
    stdout, stderr = Popen([meta.cmd] + meta.args, stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate()
    return stdout.decode('utf-8')


def shell(meta) -> str:
    stdout, stderr = Popen(meta.cmd, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE).communicate()
    return stdout.decode('utf-8')


def info(meta) -> str:
    try:
        data = load_json_data_from_json_file(meta.path)
    except FileNotFoundError:
        return "FileNotFoundError"
    except json.JSONDecodeError:
        return "JSONDecodeError"

    return json.dumps(monitor_generator(data=data))


def monitor_generator(data: dict):
    reflection_reality_data = None
    keys = data.keys()

    if '__meta__' in keys:
        meta = dict_objectization2(data['__meta__'], Meta2)
        res = getattr(sys.modules[__name__], meta.type)(meta)
        return r_type_generator(res, meta.rtype)

    else:
        reflection_reality_data = {}

        for k in keys:
            d = monitor_generator(data[k])
            reflection_reality_data[k] = d

    return reflection_reality_data


if __name__ == '__main__':
    pass
