#!/usr/bin/env python3
"""
This module allow to programmatically manipulate NetworkManager's vpn entries.

For now you can :
  - Connect to a specified Vpn
  - Disconnect all vpn connections
  - Change the user/password of a specified Vpn

Behind the wood, this module use NetworkManager python library to perform dbus call to the NetworkManager service.

Doc for dbus and NetworkManager : https://developer.gnome.org/NetworkManager/unstable/spec.html
"""

__author__ = 'maxisoft'

import os
import configparser
import subprocess
import shlex
import time

from urllib.request import urlopen

import NetworkManager


_SYSTEM_CON_PATH = '/etc/NetworkManager/system-connections'


def _waituntil(predicate, timeout, period=0.25):
    mustend = time.time() + timeout
    while time.time() < mustend:
        if predicate():
            return True
        time.sleep(period)
    return False


def _check_super_user():
    euid = os.geteuid()
    if euid != 0:
        raise EnvironmentError("need to be root")


class VpnHelper(object):
    def __init__(self):
        _check_super_user()

    @classmethod
    def list_vpn_connections(cls):
        return filter(
            lambda conn: conn.GetSettings()['connection']['type'] == 'vpn',
            NetworkManager.Settings.ListConnections())

    @classmethod
    def get_vpn_connection(cls, name):
        for conn in NetworkManager.Settings.ListConnections():
            settings = conn.GetSettings()
            if settings['connection']['type'] == 'vpn' and settings['connection']['id'] == name:
                return conn

    @classmethod
    def disconnect(cls):
        vpns = cls.get_active_vpn_connections()
        for vpn in vpns:
            cls.deactivate_conn(vpn)

    @classmethod
    def get_active_vpn_connections(cls):
        return filter(lambda conn: conn.Vpn, NetworkManager.NetworkManager.ActiveConnections)

    @classmethod
    def activate_conn(cls, conn):
        NetworkManager.NetworkManager.ActivateConnection(conn, cls.get_active_device(), "/")

    @classmethod
    def deactivate_conn(cls, conn):
        NetworkManager.NetworkManager.DeactivateConnection(conn)

    @classmethod
    def get_active_device(cls):
        for dev in NetworkManager.NetworkManager.GetDevices():
            if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED and dev.Managed:
                return dev

    @classmethod
    def restart_network_manager(cls, checkmaxtry=3):
        subprocess.Popen(shlex.split("systemctl restart NetworkManager"))
        while not cls.internet_on() and checkmaxtry:
            checkmaxtry -= 1
        return bool(checkmaxtry)

    @classmethod
    def update_vpn_conf(cls, vpn, user, password):
        configfilepath = os.path.join(_SYSTEM_CON_PATH, vpn)

        with open(configfilepath) as configfile:
            config = configparser.ConfigParser()
            config.read_file(configfile)

        config.set('vpn', 'user', user)
        config.set('vpn', 'password-flags', str(0))
        if not config.has_section('vpn-secrets'):
            config.add_section('vpn-secrets')

        config.set('vpn-secrets', 'password', password)

        with open(configfilepath, 'w') as configfile:
            config.write(configfile)

        popen = subprocess.Popen(
            shlex.split('nmcli con reload'))  # configuration has changed so tell it to NetworkManager
        return popen.wait() == 0

    @classmethod
    def internet_on(cls, url='http://ip.maxisoft.ga/', timeout=8):
        try:
            urlopen(url, timeout=timeout)
            return True
        except Exception:
            pass
        return False

    def connect(self, vpn, user=None, password=None, wait=True):
        if user and not password:
            raise ValueError('password must be set')

        vpnconn = self.get_vpn_connection(vpn)
        if not vpnconn:
            raise EnvironmentError('''There's no vpn called "%s"''' % vpn)

        if user:
            self.update_vpn_conf(vpn, user, password)

        self.activate_conn(vpnconn)

        if wait:
            def cond_wait():
                vpnsdict = {vpn.Uuid: vpn for vpn in self.get_active_vpn_connections()}
                uuid = vpnconn.GetSettings()['connection']['uuid']
                vpn = vpnsdict.get(uuid)
                if not vpn or vpn.State == NetworkManager.NM_ACTIVE_CONNECTION_STATE_DEACTIVATED:
                    raise OSError('unable to connect to vpn')
                return vpn.State == NetworkManager.NM_ACTIVE_CONNECTION_STATE_ACTIVATED

            return _waituntil(cond_wait, 20)
