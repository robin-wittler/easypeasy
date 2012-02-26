#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Robin Wittler'
__contact__ = 'real@the-real.org'
__version__ = '0.0.1'
__license__ = 'GPL3'

import re
import sys
import blog
import models
import getpass
import werkzeug
import argparse
import textwrap


env = werkzeug.create_environ('/blog', 'http://localhost:5000/')
ctx = blog.app.request_context(env)

tag_splitter = re.compile('\s*,\s*')
# now we have a valid request context and are able to use flask-sqlalchemy

class CreateDB(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        models.create_all()
        ctx.pop()
        parser.exit(0)

class AddUser(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        firstpw = getpass.getpass(prompt='Enter Password for User %s: ' %(values))
        secondpw = getpass.getpass(prompt='Repeat Password for User %s: ' %(values))
        if not firstpw == secondpw:
            print 'Password missmatch!'
            parser.exit(1)

        user = models.User(values, firstpw)
        models.db.session.add(user)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class DelUser(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        user = models.User.query.filter_by(username=values).one()
        models.db.session.delete(user)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class ShowUsers(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        print 'Users:'
        print '------'
        for user in models.User.query.all():
            print '%r' %(user)
        ctx.pop()
        parser.exit(0)

class AddGroup(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        group = models.Group(values)
        models.db.session.add(group)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class DelGroup(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        group = models.Group.query.filter_by(name=values).one()
        models.db.session.delete(group)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class ShowGroups(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        print 'Groups:'
        print '-------'
        for group in models.Group.query.all():
            print '%r' %(group)
        ctx.pop()
        parser.exit(0)

class AddUser2Group(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        user, group = values
        user = models.User.query.filter_by(username=user).one()
        user.addGroup(group)
        models.db.session.add(user)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class DelUserFromGroup(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        ctx.push()
        user, group = values
        user = models.User.query.filter_by(username=user).one()
        group = models.Group.query.filter_by(name=group).one()
        user.groups.remove(group)
        models.db.session.add(user)
        models.db.session.commit()
        ctx.pop()
        parser.exit(0)

class AddEntry(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        user, name, tags, content = values
        if content == '-':
            content = sys.stdin.read()

        if not tags == 'NONE':
            tags = tag_splitter.split(tags)
        else:
            tags = ['Untagged']
        ctx.push()
        entry = models.BlogEntry(name, content, user, tags=tags)
        models.db.session.add(entry)
        models.db.session.commit()
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
        '--createdb',
        nargs=0,
        action=CreateDB,
        help='initially creates the db.'
    )

    parser.add_argument(
        '--adduser',
        action=AddUser,
        metavar='USER',
        help='add a user to easypeasy.'
    )

    parser.add_argument(
        '--deluser',
        action=DelUser,
        metavar='USER',
        help='delete a easypeasy user.'
    )

    parser.add_argument(
        '--listusers',
        action=ShowUsers,
        nargs=0,
        help='list all easypeasy users.'
    )

    parser.add_argument(
        '--addgroup',
        action=AddGroup,
        metavar='GROUP',
        help='add a group to easypeasy.'
    )

    parser.add_argument(
        '--delgroup',
        action=DelGroup,
        metavar='GROUP',
        help='delete a easypeasy group.'
    )

    parser.add_argument(
        '--listgroups',
        nargs=0,
        action=ShowGroups,
        help='list all easypeasy groups.'
    )

    parser.add_argument(
        '--adduser2group',
        nargs=2,
        action=AddUser2Group,
        metavar=('USER', 'GROUP'),
        help='add a user to a group.'
    )

    parser.add_argument(
        '--remove-user-from-group',
        nargs=2,
        action=DelUserFromGroup,
        metavar=('USER', 'GROUP'),
        help='remove a user from a group'
    )

    parser.add_argument(
        '--addentry',
        nargs=4,
        metavar=('USER', 'NAME', 'TAGS', 'CONTENT'),
        action=AddEntry,
        help=(
            'add a blogentry for a user. If content is \'-\' ' +
            'then content will be taken from stdin. ' +
            'Tags must be comma seperated - or (if untagged) Tags must ' +
            'be the word NONE. (And remeber to quote if your tags include spaces).'
        )
    )

    args = parser.parse_args()
    if not args._get_args() or args._get_kwargs():
        parser.print_help()
        parser.exit(0)

    return args


if __name__ == '__main__':
    getopts()
