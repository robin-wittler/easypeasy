#!/usr/bin/env python
# -*- coding: utf-8 -*-

# in case of sqlite
db_connect_string = 'sqlite:////tmp/easypeasy.db'

# in case of postgres
#db_connect_string = 'postgresql://<username>:<password>@<host>:<port>/<database>'

# the secrect key to encrypt cookies
secret_key = 'Please change me'

# to enable debug (use this only for non-production enviroment)
debug = True

# the name of the blog
blog_name = 'Alsobs.de'

# the blog subtitle
blog_subtitle = 'Die tun nur so als ob!'

# how many blog entries per page?
max_entries_per_page = 2
