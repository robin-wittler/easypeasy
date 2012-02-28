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
from models import get_used_tags
from models import create_all
from models import BlogEntry
from models import NoResultFound

from flask import g
from flask import Flask
from flask import abort
from flask import url_for
from flask import request
from flask import session
from flask import redirect
from flask import render_template

from functools import wraps

app = Flask(__name__)
app.secret_key = config.secret_key
app.debug = config.debug
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_connect_string

db.init_app(app)
max_per_page = config.max_entries_per_page

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username', None) is None:
            return redirect(url_for('blog_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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
    g.tags = get_used_tags()
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
    g.tags = get_used_tags()
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
    g.tags = get_used_tags()
    return render_template('child.html', g=g)

@app.route('/blog/by/id/<int:blog_id>', methods=['POST', 'GET'])
def blog_by_id(blog_id):
    
    query = BlogEntry.getAll()
    query = BlogEntry.addBlogIdFilter(query, blog_id)
    query = query.paginate(1, per_page=max_per_page)

    if 'page' in request.path:
        endpoint = request.path.rsplit('/', 1)[0]
    else:
        endpoint = os.path.join(request.path, 'page')

    g.paginate = query
    g.left_sidebar = True
    g.endpoint = endpoint
    g.blog_name = config.blog_name
    g.title = '%s' %(g.paginate.items[0].name)
    g.blog_subtitle = config.blog_subtitle
    g.tags = get_used_tags()
    return render_template('child.html', g=g)

@app.route('/blog/by/name/<name>', methods=['POST', 'GET'])
def blog_by_name(name):
    
    query = BlogEntry.getAll()
    query = BlogEntry.addNameFilter(query, name)
    query = query.paginate(1, per_page=max_per_page)

    if 'page' in request.path:
        endpoint = request.path.rsplit('/', 1)[0]
    else:
        endpoint = os.path.join(request.path, 'page')

    g.paginate = query
    g.left_sidebar = True
    g.endpoint = endpoint
    g.blog_name = config.blog_name
    g.title = '%s' %(g.paginate.items[0].name)
    g.blog_subtitle = config.blog_subtitle
    g.tags = get_used_tags()
    return render_template('child.html', g=g)


@app.route('/blog/edit/<int:blog_id>', methods=['POST', 'GET'])
@login_required
def blog_edit(blog_id):
    query = BlogEntry.getAll()
    query = BlogEntry.addBlogIdFilter(query, blog_id)
    
    if not query.one().username == session['username']:
        return abort(401)

    g.blog_entry = query.one()
    g.left_sidebar = False
    g.blog_name = config.blog_name
    g.blog_subtitle = config.blog_subtitle
    g.title = 'Edit entry: %s' %(g.blog_entry.name)

    return render_template('edit.html', g=g)
    
@app.route('/blog/update/<int:blog_id>', methods=['POST', 'GET'])
@login_required
def blog_update(blog_id):
    query = BlogEntry.getAll()
    query = BlogEntry.addBlogIdFilter(query, blog_id)
    blog_entry = query.one()

    if not blog_entry.username == session['username']:
        return abort(401)

    need_update = False

    headline = request.form.get('headline', blog_entry.headline)

    if headline != blog_entry.headline:
        blog_entry.headline = headline
        need_update = True

    payload = request.form.get('payload', blog_entry.payload)

    if payload != blog_entry.payload:
        blog_entry.changePayload(payload)
        need_update = True

    new_tags = set()
    str_new_tags = request.form.get('tags', 'Untagged')
    if not str_new_tags:
        str_new_tags = 'Untagged'

    for tag in str_new_tags.split(','):
        new_tags.add(tag)

    old_tags = set(t.name for t in blog_entry.tags)
    if new_tags != old_tags:
        blog_entry.tags = []
        for tag in new_tags:
            blog_entry.addTag(tag)
        need_update = True

    if need_update:
        blog_entry.updateModifiedDate()
        db.session.add(blog_entry)
        db.session.commit()
    
    return redirect('/blog/by/id/%s' %(blog_entry.id))

@app.route('/blog/new', methods=['POST', 'GET'])
@login_required
def blog_new():
    g.left_sidebar = False
    g.blog_name = config.blog_name
    g.blog_subtitle = config.blog_subtitle
    g.title = 'Make a new Entry for'
    return render_template('create.html', g=g)

@app.route('/blog/create', methods=['POST', 'GET'])
@login_required
def blog_create():
    name = request.form.get('name')
    headline = request.form.get('headline')
    if not headline:
        headline = name
    tag_str = request.form.get('tags')
    payload = request.form.get('payload')
    tags = list()

    for tag in tag_str.split(','):
        tags.append(tag.lstrip().rstrip())
    
    blog_entry = BlogEntry(name, payload, session['username'], headline=headline, tags=tags)

    db.session.add(blog_entry)
    db.session.commit()

    return redirect('/blog/by/id/%s' %(blog_entry.id))

@app.route('/blog/login', methods=['POST', 'GET'])
@app.route('/blog/login/', methods=['POST', 'GET'])
@app.route('/blog/login/<username>', methods=['POST', 'GET'])
def blog_login(username=None):
    if request.method == 'GET':
        next = request.args.get('next', '')
        return render_template('login2.html', username=username, next=next)
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

            next = request.form.get('next', '')
            if next:
                return redirect(next)
            return redirect(url_for('blog'))



if __name__ == '__main__':
    app.run()
