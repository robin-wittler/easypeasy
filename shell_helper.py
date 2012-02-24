#!/usr/bin/python
# -*- coding: utf-8 -*-


import werkzeug
import blog
import models

env = werkzeug.create_environ('/blog', 'http://localhost:5000/')
ctx = blog.app.request_context(env)
ctx.push()
# now we have a valid request context and are able to use flask-sqlalchemy

