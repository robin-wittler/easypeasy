#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# TODO 
# - cleanup unused imports
# - Try to make exctract work
# - write comments
# - write documentation
# - implement some additional caching

import config
import calendar
import textile
import datetime
import sqlalchemy
from sqlalchemy.sql import cast
from sqlalchemy.sql import extract
from lxml.html.clean import Cleaner
from flaskext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.interfaces import PoolListener
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

# This enforce 'pragma foreign_keys=ON' for a db connect
class SQLiteForeignKeysListener(PoolListener):
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute('pragma foreign_keys=ON')


# This enforce 'pragma foreign_keys=ON' for a sqlite db type
class StrictSQLAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        super(StrictSQLAlchemy, self).apply_driver_hacks(app, info, options)
        if info.drivername == 'sqlite':
            options.setdefault('listeners', []).append(SQLiteForeignKeysListener())

db = StrictSQLAlchemy()

class Error(Exception):
    pass

class DayOutOfRange(Error):
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    def __str__(self):
        return (
            'In the year %s at month %s is no day %s' 
            %(self.year, self.month, self.day)
        )

class MonthOutOfRange(Error):
    def __init__(self, year, month):
        self.year = year
        self.month = month

    def __str__(self):
        return (
            'Month %s is out of range for year %s'
            %(self.month, self.year)
        )

groups = db.Table(
    'groups',
    db.Column('group_name', db.String(80), db.ForeignKey('group.name')),
    db.Column('user_name', db.String(80), db.ForeignKey('user.username')),
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    blogs = db.relationship('BlogEntry', backref='user', lazy='dynamic')
    groups = db.relationship(
            'Group',
            secondary=groups,
            backref=db.backref('users', lazy='dynamic'),
    )

    def __init__(self, username, password):
        self.username = username
        if not self.isPwHashed(password):
            self.password = self.hashPassword(password)
        else:
            self.password = password

    def hashPassword(self, password):
        return generate_password_hash(password)

    def checkPassword(self, password):
        if not self.isPwHashed(self.password):
            raise ValueError(
                'Calling checkPassword but self.password is not hashed'
            )
        return check_password_hash(self.password, password)

    def isPwHashed(self, password):
        try:
            algo, salt, pw = password.split('$')
            if not algo.startswith('sha'):
                raise Exception
        except:
            return False
        else:
            return True

    def addGroup(self, name):
        group = Group.query.filter_by(name=name).one()

        # we dont want the same group occur more then once
        if group in self.groups:
            return

        self.groups.append(group)

    def removeGroup(self, name):
        self.groups.remove(Group.query.filter_by(name=name).one())
 

    def __repr__(self):
        return (
            '<User(username="%s", password="%s", groups="%s", blogentries="%s") object at %s>'
            %(
                self.username,
                self.password,
                ', '.join(map(lambda x: str(x), self.groups)),
                ', '.join(map(lambda x: str(x), self.blogs.all())), 
                hex(id(self))
            )
        )

    def __str__(self):
        return '%s' %(self.username)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s(name="%s") object at %s>' %(self.__class__.__name__, self.name, hex(id(self)))

    def __str__(self):
        return self.name

tags = db.Table(
    'tags',
    db.Column('tag_name', db.String(80), db.ForeignKey('tag.name')),
    db.Column('blog_name', db.String(255), db.ForeignKey('blog_entry.name')),
)

def get_used_tags():
    all_used_tags = db.session.query(tags).all()
    return set(tag[0] for tag in all_used_tags)

class BlogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    headline = db.Column(db.String(255), unique=True, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False)
    modified_date = db.Column(db.DateTime, nullable=False)
    tags = db.relationship(
            'Tag',
            secondary=tags,
            backref=db.backref('pages', lazy='dynamic'),
    )
    payload = db.Column(db.Text, nullable=False)
    html_payload = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)

    @classmethod
    def getRangeForDayQuery(cls, year, month, day):
        last_day_of_month = calendar.monthrange(year, month)[-1]
        if day == last_day_of_month:
            if month == 12:
                _month = 1
                _year = year + 1
                _day = 1
            else:
                _month = month
                _year = year
                _day = day + 1

        elif day == 1:
            if month == 1:
                month_ = 12
                year_ = year - 1
                day_ = calendar.monthrange(year_, month_)[-1]
            else:
                month_ = month
                year_ = year
                day_ = day - 1
        else:
            _month = month
            _year = year
            _day = day + 1
            month_ = month
            year_ = year
            day_ = day - 1
        return ((_year, _month, _day ,0, 0, 0, 000000), (year_, month_, day_, 23, 59, 59, 999999))

    @classmethod
    def getAll(cls):
        return cls.query.order_by(cls.creation_date)

    @classmethod
    def addUserFilter(cls, query, username):
        return query.filter_by(username=username)

    @classmethod
    def addBlogIdFilter(cls, query, blog_id):
        return query.filter_by(id=blog_id)

    @classmethod
    def addTagFilter(cls, query, tag):
        tag = Tag.query.filter_by(name=tag).one()
        return query.filter(cls.tags.contains(tag))

    @classmethod
    def addNameFilter(cls, query, name):
        return query.filter_by(name=name)

    @classmethod
    def addHeadlineFilter(cls, query, headline):
        return query.filter_by(headline=headline)

    @classmethod
    def addCreationYearFilter(cls, query, year):
        year = int(year)
        return query.filter(
            db.and_(
                cls.creation_date >= datetime.date(year, 1, 1),
                cls.creation_date < datetime.date(year + 1, 1, 1)
            )
        )

    @classmethod
    def addCreationMonthFilter(cls, query, year, month):
        year = int(year)
        month = int(month)
        
        if not month in xrange(1, 13):
            raise MonthOutOfRange(year, month)

        last_day_of_month = calendar.monthrange(year, month)[-1]

        # XXX make this a real month query with extract - but there is some error
        # in the sqlalchemy extract handling. so - for now we are happy with that what we have.
        # the code below expands to somewhat like:
        # "EXTRACT(<Mapper at 0x2efed50; BlogEntry>.creation_date FROM :param_1)"
        # which raises an error, because of the <Mapper at 0x2efed50; BlogEntry> stuff.
        # return query.filter(extract(cls.creation_date, 'month') = month)
        
        return query.filter(
            db.and_(
                cls.creation_date >= datetime.date(year, month, 1),
                cls.creation_date <= datetime.date(year, month, last_day_of_month)
            )
        )

    @classmethod
    def addCreationDayFilter(cls, query, year, month, day):
        year = int(year)
        month = int(month)
        day = int(day)
        
        last_day_of_month = calendar.monthrange(year, month)[-1]
        if not day in xrange(1, last_day_of_month +1):
            raise DayOutOfRange(year, month, day)

        gt_day, le_day = cls.getRangeForDayQuery(year, month, day)

        return query.filter(
            db.and_(
                cls.creation_date < datetime.datetime(*gt_day),
                cls.creation_date > datetime.datetime(*le_day)
            )
        )


    @classmethod
    def addModifiedYearFilter(cls, query, year):
        year = int(year)
        return query.filter(
            db.and_(
                cls.modified_date >= datetime.date(year, 1, 1),
                cls.modified_date < datetime.date(year + 1, 1, 1)
            )
        )
 
    @classmethod
    def addModifiedMonthFilter(cls, query, year, month):
        
        year = int(year)
        month = int(month)

        if not month in xrange(1, 13):
            raise MonthOutOfRange(year, month)
        
        last_day_of_month = calendar.monthrange(year, month)[-1]
        return query.filter(
            db.and_(
                cls.modified_date >= datetime.date(year, month, 1),
                cls.modified_date <= datetime.date(year, month, last_day_of_month)
            )
        )


    @classmethod
    def addModifiedDayFilter(cls, query, year, month, day):
        
        year = int(year)
        month = int(month)
        day = int(day)

        if not month in xrange(1, 13):
            raise MonthOutOfRange(year, month)
        
        last_day_of_month = calendar.monthrange(year, month)[-1]
        if not day in xrange(1, last_day_of_month +1):
            raise DayOutOfRange(year, month, day)

        gt_day, le_day = cls.getRangeForDayQuery(year, month, day)

        return query.filter(
            db.and_(
                cls.modified_date < datetime.datetime(*gt_day),
                cls.modified_date > datetime.datetime(*le_day)
            )
        )

    @classmethod
    def iterQuery(cls, query):
        for q in query.all():
            yield q

  
    def __init__(self, name, payload, username, headline=None, creation_date=None, modified_date=None, tags=None):
        self.name = name
        fallback_date = datetime.datetime.now()
        if creation_date is None:
            self.creation_date = fallback_date
        else:
            self.creation_date = creation_date

        if modified_date is None:
            self.modified_date = fallback_date
        else:
            self.modified_date = modified_date

        self.payload = payload
        self.html_payload = self.sanitizeHtml(textile.textile(self.payload))
        self.username = username

        if headline is None:
            self.headline = self.name
        else:
            self.headline = headline

        if tags is not None:
            for tag in tags:
                self.addTag(tag)
        else:
            self.addTag('Untagged')


    def changePayload(self, payload):
        self.payload = payload
        self.html_payload = self.sanitizeHtml(textile.textile(self.payload))
        return True

    def __repr__(self):
        return (
            '<%s(name="%s", creation_date="%s", modified_date="%s", tags="%s", username="%s", headline="%s") object at %s>'
            %(
                self.__class__.__name__,
                self.name,
                self.creation_date,
                self.modified_date,
                self.tags,
                self.username,
                self.headline,
                hex(id(self))
            )
        )

    def __str__(self):
        return self.name

    def sanitizeHtml(self, html):
        cleaner = Cleaner(links=False)
        return cleaner.clean_html(html)

    def addTag(self, name):
        if not name:
            name = 'Untagged'

        try:
            tag = Tag.query.filter_by(name=name).one()
        except NoResultFound:
            tag = Tag(name)
            db.session.add(tag)
            db.session.commit()

        # we dont want the same tag occur more then once
        if tag in self.tags:
            return

        self.tags.append(tag)

        # now there is a tag - so we must remove the untagged tag
        # if it is set.
        untagged = Tag.query.filter_by(name='Untagged').one()
        if untagged in self.tags and len(self.tags) > 1:
            self.tags.remove(untagged)

    def removeTag(self, name):
        try:
            self.tags.remove(Tag.query.filter_by(name=name).one())
        except NoResultFound:
            # hmm, should we do something here?
            pass

    def updateModifiedDate(self):
        self.modified_date = datetime.datetime.now()
        

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s(name="%s") object at %s>' %(self.__class__.__name__, self.name, hex(id(self)))

    def __str__(self):
        return self.name


def create_all():
    db.create_all()
    # add the default 'Untagged' tag.
    tag = Tag('Untagged')
    db.session.add(tag)
    db.session.commit()
