import psycopg2
import os
import urllib.parse as urlparse

def get_db_conn_params():
    url = urlparse.urlparse(os.environ['DATABASE_URL'])
    return {'dbname': url.path[1:], 'user': url.username, 'password': url.password, 'host': url.hostname}
