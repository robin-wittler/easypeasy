#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# TODO 
# - cleanup unused imports
# - Try to make exctract work
# - write comments
# - write documentation
# - implement some additional caching

import os
import config

from models import db
from models import User
from models import Group
from models import groups
from models import tags
from models import Tag
from models import create_all
from models import BlogEntry
from models import NoResultFound

from flask import g
from flask import json
from flask import Flask
from flask import abort
from flask import escape
from flask import jsonify
from flask import url_for
from flask import request
from flask import session
from flask import redirect
from flask import render_template

app = Flask(__name__)
app.secret_key = config.secret_key
app.debug = config.debug
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_connect_string

db.init_app(app)
max_per_page = 2

class Error(Exception):
    pass

class LoginError(Error):
    pass

class UserCredentialsError(LoginError):
    def __str__(self):
        return 'Wrong Username or Password.'

class MissingFieldValue(LoginError):
    def __init__(self, field):
        self.field = field

    def __str__(self):
        return 'Missing Value for Field: %s' %(self.field)

@app.route('/')
def index(*args, **kwargs):
    return redirect(url_for('blog'))

@app.route('/blog/', methods=['POST', 'GET'])
@app.route('/blog/page/<int:page>', methods=['POST', 'GET'])
def blog(page=None):
    
    if page is None:
        page = 1

    query = BlogEntry.getAll()
    query = query.paginate(page, per_page=max_per_page)

    if 'page' in request.path:
        endpoint = request.path.rsplit('/', 1)[0]
    else:
        endpoint = os.path.join(request.path, 'page')

    g.paginate = query
    g.left_sidebar = True
    g.endpoint = endpoint
    g.blog_name = config.blog_name
    g.title = 'Blog for'
    g.blog_subtitle = config.blog_subtitle
    g.Tag = Tag
    return render_template('child.html', g=g)

@app.route('/blog/by/date/<int:year>', methods=['POST', 'GET'])
@app.route('/blog/by/date/<int:year>/page/<int:page>', methods=['POST', 'GET'])
@app.route('/blog/by/date/<int:year>/<int:month>', methods=['POST', 'GET'])
@app.route('/blog/by/date/<int:year>/<int:month>/page/<int:page>', methods=['POST', 'GET'])
@app.route('/blog/by/date/<int:year>/<int:month>/<int:day>', methods=['POST', 'GET'])
@app.route('/blog/by/date/<int:year>/<int:month>/<int:day>/page/<int:page>', methods=['POST', 'GET'])
def blog_by_date(year=None, month=None, day=None, page=None):

    if page is None:
        page = 1

    query = BlogEntry.getAll()

    if all((year is not None, month is not None, day is not None)):
        query = BlogEntry.addCreationDayFilter(query, year, month, day)

    elif all((year is not None, month is not None)):
        query = BlogEntry.addCreationMonthFilter(query, year, month)

    elif year is not None:
        query = BlogEntry.addCreationYearFilter(query, year)


    query = query.paginate(page, per_page=max_per_page)

    if 'page' in request.path:
        endpoint = request.path.rsplit('/', 1)[0]
    else:
        endpoint = os.path.join(request.path, 'page')


    g.paginate = query
    g.BlogEntry = BlogEntry
    g.left_sidebar = True
    g.Tag = Tag
    g.endpoint = endpoint
    g.blog_name = config.blog_name
    bf = 'Blog for'
    if year is not None:
        what = '/'.join(map(lambda x: str(x), filter(None, (g.year, g.month, g.day))))
    else:
        what = ''
    g.title = '%s %s' %(bf, what)
    g.blog_subtitle = config.blog_subtitle
    return render_template('child.html', g=g)


@app.route('/blog/by/tag/<tag>', methods=['POST', 'GET'])
@app.route('/blog/by/tag/<tag>/page/<int:page>', methods=['POST', 'GET'])
def blog_by_tag(tag, page=None):
    
    if page is None:
        page = 1

    query = BlogEntry.getAll()
    query = BlogEntry.addTagFilter(query, tag)
    query = query.paginate(page, per_page=max_per_page)

    if 'page' in request.path:
        endpoint = request.path.rsplit('/', 1)[0]
    else:
        endpoint = os.path.join(request.path, 'page')

    g.paginate = query
    g.left_sidebar = True
    g.endpoint = endpoint
    g.blog_name = config.blog_name
    g.title = 'Blog for %s' %(tag)
    g.blog_subtitle = config.blog_subtitle
    g.Tag = Tag
    return render_template('child.html', g=g)

@app.route('/login', methods=['POST', 'GET'])
@app.route('/login/', methods=['POST', 'GET'])
@app.route('/login/<username>', methods=['POST', 'GET'])
def login(username=None):
    if request.method == 'GET':
        return render_template('login2.html', username=username)
    else:
        form_username = request.form.get('username', None)
        form_password = request.form.get('password', None)

        try:
            if not form_username:
                raise MissingFieldValue('username')

            if not form_password:
                raise MissingFieldValue('password')

            try:
                user = User.query.filter_by(username=form_username).one()
            except NoResultFound, error:
                raise UserCredentialsError
            else:
                if not user.checkPassword(form_password):
                    raise UserCredentialsError

        except (UserCredentialsError, MissingFieldValue), error:
            return render_template('login2.html', error=error, username=form_username)
        else:
            if not form_username in session:
                session['username'] = form_username
                session['ip'] = request.remote_addr
            return redirect(url_for('blog'))



if __name__ == '__main__':
    app.run()
