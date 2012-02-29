Notes:
------

Easypeasy is inteded to be a simple blog.
It is under heavy development and incomplete.
As a example, it lacks totaly of any design - the css files
are some sort of dummys.


TODO:
-----

* arrange the jinja2 templates new to make it more flexible
* remove unused imports
* cleanup code
* write tests
* switch to flask-login
* ...

To start do the following:
--------------------------


1. edit config.py so it fit your needs
2. call: python manage.py --createdb
3. call: python manage.py --adduser <username>
4. to test easypeasy, call: python blog.py
   or create a valid wsgi enviroment for your httpd

