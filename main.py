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
import cgi
import hashlib
import webapp2
import urllib
from google.appengine.api import memcache
from google.appengine.api import urlfetch

COMPRESSIONS = ['WHITESPACE_ONLY', 'SIMPLE_OPTIMIZATIONS', 
                'ADVANCED_OPTIMIZATIONS']

URL = 'http://closure-compiler.appspot.com/compile'


def check_memcache(key):
  md5_key = hashlib.md5(key).hexdigest()
  return memcache.get(md5_key)


class MainHandler(webapp2.RequestHandler):

  def get(self):
    cache_time = urllib.unquote(cgi.escape(self.request.get(
        'cache_time', '3600')))
    compilation_level = urllib.unquote(cgi.escape(
        self.request.get('compilation_level', COMPRESSIONS[0])))
    js_code = urllib.unquote(cgi.escape(self.request.get('js_code', '')))
    code_url = urllib.unquote(cgi.escape(self.request.get('code_url', '')))
    
    # Check Memcache
    if js_code and code_url:
      key = js_code + code_url
    elif js_code:
      key = js_code
    elif code_url:
      key = code_url
    
    data = check_memcache(key)
    if data is not None:
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(data)
      return
    
    
    params = urllib.urlencode([
        ('code_url', code_url),
        ('js_code', js_code),
        ('compilation_level', compilation_level),
        ('output_format', 'text'),
        ('output_info', 'compiled_code'),
    ])
    
    headers = { 'Content-type': 'application/x-www-form-urlencoded' }
    result = urlfetch.fetch(url=URL, payload=params, method=urlfetch.POST,
                            headers=headers)
    
    if result.status_code == 200:
      memcache.add(hashlib.md5(key).hexdigest(), result.content, 
          int(cache_time))
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write(result.content)

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
