#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Robin Wittler'
__contact__ = 'real@the-real.org'
__version__ = '0.0.1'

import werkzeug
import blog
import models
import argparse
import textwrap


env = werkzeug.create_environ('/blog', 'http://localhost:5000/')
ctx = blog.app.request_context(env)
# now we have a valid request context and are able to use flask-sqlalchemy

class SyncDB(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        models.create_all()
        ctx.pop()
        parser.exit(0)


def getopts():
    description = 'A managment tool for the easypeasy blog.'
    epilog = textwrap.dedent("""
    Copyright (C) 2012  Robin Wittler.
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    """
    )

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s ' + __version__,
    )

    parser.add_argument(
        'syncdb',
        action=SyncDB,
    )

    args = parser.parse_args()
    if not args._get_args() or args._get_kwargs():
        parser.print_help()
        parser.exit(0)

    return args


if __name__ == '__main__':
    getopts()
