#!/usr/bin/env python3

#
# Copyright (c) 2017-2020 Kevin Steves <kevin.steves@pobox.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import argparse
import ipaddress
import os
import sys
import time

libpath = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(libpath, os.pardir, 'lib')]
import pan.xapi

DEFAULT_TAGS = ['tag01', 'tag02']
DEFAULT_NETWORK = '10.0.0.0/8'
DEFAULT_CHUNK = 1024
DEFAULT_TIMEOUT = None
DEFAULT_PERSISTENT = None


def main():
    args = parse_args()

    if args.print:
        xapi = None
    else:
        try:
            xapi = pan.xapi.PanXapi(tag=args.t)
        except pan.xapi.PanXapiError as e:
            print('pan.xapi.PanXapi:', e, file=sys.stderr)
            sys.exit(1)

    if args.login or args.register:
        doit(xapi, args, add=True)
    if args.logout or args.unregister:
        doit(xapi, args, delete=True)

    sys.exit(0)


def parse_args():
    def valid_net(x):
        try:
            ipaddress.ip_network(x)
        except ValueError as e:
            raise argparse.ArgumentTypeError(e)

        return x

    parser = argparse.ArgumentParser(usage='%(prog)s [options]')
    parser.add_argument('-t',
                        help='.panrc tagname')
    parser.add_argument('-n',
                        type=int,
                        required=True,
                        help='number of ip mappings')
    parser.add_argument('--net',
                        type=valid_net,
                        default=DEFAULT_NETWORK,
                        help='starting network (default: %s)' %
                        DEFAULT_NETWORK)
    parser.add_argument('--chunk',
                        type=int,
                        default=DEFAULT_CHUNK,
                        help='chunk size (default: %d)' %
                        DEFAULT_CHUNK)
    parser.add_argument('--timeout',
                        type=int,
                        default=DEFAULT_TIMEOUT,
                        help='ip-user timeout in minutes (default: %s)' %
                        str(DEFAULT_TIMEOUT))
    parser.add_argument('--login',
                        action='store_true',
                        help='login users (ip-user)')
    parser.add_argument('--logout',
                        action='store_true',
                        help='logout users')
    parser.add_argument('--register',
                        action='store_true',
                        help='register tags (registered-ip)')
    parser.add_argument('--unregister',
                        action='store_true',
                        help='unregister tags')
    parser.add_argument('--persistent',
                        type=int,
                        choices=[0, 1],
                        help='registered-ip persistent attribute '
                        '(default: %s)' %
                        str(DEFAULT_PERSISTENT))
    parser.add_argument('--tags',
                        nargs='+',
                        default=DEFAULT_TAGS,
                        help='registered-ip tags (default: %s)' %
                        ' '.join(DEFAULT_TAGS))
    parser.add_argument('--print',
                        action='store_true',
                        help='print XML uid-message documents only')
    args = parser.parse_args()

    return args


def doit(xapi, args, add=False, delete=False):
    begin = time.time()
    n = 0
    net = ipaddress.ip_network(args.net).hosts()

    while True:
        ips = []
        chunk_n = 0
        while n < args.n and chunk_n < args.chunk:
            try:
                ips.append(next(net))
            except StopIteration:
                print('network too small for %d mappings' % args.n,
                      file=sys.stderr)
                sys.exit(1)

            chunk_n += 1
            n += 1

        if args.login and add:
            action = 'login'
            login_logout(args, action, xapi, ips)
        if args.logout and delete:
            action = 'logout'
            login_logout(args, action, xapi, ips)
        if args.register and add:
            action = 'register'
            register_unregister(args, action, xapi, ips)
        if args.unregister and delete:
            action = 'unregister'
            register_unregister(args, action, xapi, ips)

        if n == args.n:
            break

    if args.print:
        return

    end = time.time()
    elapsed = end - begin

    print('elapsed %.2f chunk %d num %d' % (elapsed, args.chunk, args.n))
    print('%.2f %ss/sec' % (args.n / elapsed, action))


def login_logout(args, action, xapi, ips):
    entry = '''\
      <entry name="{0}" ip="{1}"{2}/>
'''

    uid_message = '''\
<uid-message>
  <type>update</type>
  <payload>
    <{0}>
{1}\
    </{0}>
  </payload>
</uid-message>
'''

    entries = []
    attributes = ''
    if args.login and args.timeout is not None:
        attributes += ' timeout="%s"' % args.timeout
    [entries.append(entry.format('user-' + str(x), x,
                                 attributes)) for x in ips]

    cmd = uid_message.format(action, ''.join(entries))
    api_request(args, xapi, cmd)


def register_unregister(args, action, xapi, ips):
    member = '''\
          <member>{0}</member>
'''

    entry = '''\
      <entry ip="{0}"{1}>
        <tag>
{2}\
        </tag>
      </entry>
'''

    uid_message = '''\
<uid-message>
  <type>update</type>
  <payload>
    <{0}>
{1}\
    </{0}>
  </payload>
</uid-message>
'''

    members = []
    [members.append(member.format(x)) for x in args.tags]
    entries = []
    attributes = ''
    if args.register and args.persistent is not None:
        attributes += ' persistent="%d"' % args.persistent
    [entries.append(entry.format(str(x), attributes,
                                 ''.join(members))) for x in ips]

    cmd = uid_message.format(action, ''.join(entries))
    api_request(args, xapi, cmd)


def api_request(args, xapi, cmd):
    if args.print:
        print(cmd, file=sys.stderr, end='')
        return

    try:
        xapi.user_id(cmd=cmd)
    except pan.xapi.PanXapiError as e:
        print('pan.xapi.PanXapi:', e, file=sys.stderr)
        print(cmd, file=sys.stderr, end='')
        sys.exit(1)


if __name__ == '__main__':
    main()
