#!/usr/bin/env python3
from vpnhelper import VpnHelper
import argparse

__author__ = 'maxisoft'

parser = argparse.ArgumentParser(description='rasdial like interface', prefix_chars='-/')
parser.add_argument('vpn', metavar='vpn', type=str, nargs='?',
                   help='the vpn name')
parser.add_argument('user', metavar='user', type=str, nargs='?',
                   help='the user to login')
parser.add_argument('password', metavar='password', type=str, nargs='?',
                   help='the password to login')
parser.add_argument('/disconnect', '/d', '-d', '--disconnect', dest='disconnect', action='store_true',
                   help='disconnect the vpn')

args = parser.parse_args()

vpnhelper = VpnHelper()

if args.disconnect:
    vpnhelper.disconnect()
elif args.vpn:  # connection
    if args.user:  # 1st case : use new user/password
        if not args.password:
            parser.error("user parameter requires password parameter")
        vpnhelper.connect(args.vpn, args.user, args.password)
    else:  # 2nd case use system stored user/password
        vpnhelper.connect(args.vpn)
else:  # show infos
    connections = list(vpnhelper.get_active_vpn_connections())
    connslen = len(connections)
    if connslen:
        print("Active vpn connection%s:" % ('s' if connslen > 1 else ''))
        for vpn in connections:
            print(vpn.Connection.GetSettings()['connection']['id'])
        print()
    else:
        print('No active vpn connection')


