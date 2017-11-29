#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2

import jinja2
import urllib, urllib2
import json
import uuid
import os
from google.appengine.api import users
from webapp2_extras import sessions

from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Comment(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add=True)
    comment = ndb.StringProperty(indexed=False)
    uid = ndb.StringProperty(indexed=False)
    umail = ndb.StringProperty(indexed=False)
DEFAULT_GUESTBOOK_NAME = 'default_guestbook'
def comment_key(comment_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.
    We use guestbook_name as the key.
    """
    return ndb.Key('comment', comment_name)
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()


class MainHandler(BaseHandler):
    def get(self):
        user = users.get_current_user()
        self.response.write('<h3>Talking Board</h3>')
        topic = self.request.get('topic')
        ip = self.request.remote_addr
        # download and parse JSON
        response = urllib2.urlopen('http://www.geoplugin.net/json.gp?ip=' + ip)
        data = json.load(response)
        ip_name = data['geoplugin_countryName']
        if user:
            name = user.nickname()
            logout_url = users.create_logout_url('/')
            greeting = 'Welcome, {}! (<a href="{}">sign out</a>)'.format(
            name, logout_url)
        else:
            login_url = users.create_login_url('/')
            greeting = '<a href="{}">Sign in</a>'.format(login_url)

        if(topic):
            comment_query = Comment.query(ancestor=comment_key(topic)).order(-Comment.date)
            comments = comment_query.fetch()
        else:
            comments = ""

        self.response.write(greeting)
        template_values = {
            'topic': topic,
            'comments': comments,
            'ip': ip,
            'ipname': ip_name,
            'user': user

        }
        template = JINJA_ENVIRONMENT.get_template('q4temp.html')
        self.response.write(template.render(template_values))


    def post(self):
        user = users.get_current_user()
        topic = self.request.get('topic')
        comment = self.request.get('comment')
        if user and topic and comment:
            c = Comment(parent=comment_key(topic))
            c.uid = user.user_id()
            c.umail = user.email()
            c.comment = comment
            c.put()

        query_params = {'topic': topic}
        self.redirect('/?' + urllib.urlencode(query_params))




config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'testkey11111',
}
app = webapp2.WSGIApplication([
    ('/', MainHandler),
],
config=config,
debug=True)
