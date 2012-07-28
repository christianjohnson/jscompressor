# Copyright Christian Johnson 2012

import cgi
import hashlib
import webapp2
import urllib
import logging
from google.appengine.api import memcache
from google.appengine.api import urlfetch

COMPRESSIONS = ['WHITESPACE_ONLY', 'SIMPLE_OPTIMIZATIONS', 'ADVANCED_OPTIMIZATIONS']
URL = 'http://closure-compiler.appspot.com/compile'

def check_memcache(key, compilation_level):
  md5_key = hashlib.md5(key).hexdigest()
  return memcache.get(md5_key + ':' + compilation_level)

class MainHandler(webapp2.RequestHandler):
  """Redirect to GitHub."""
  
  def get(self):
    self.redirect("http://christianjohnson.github.com/jscompressor/")

class Compress(webapp2.RequestHandler):
  """"Class to handle compression requests.
  
  Args:
    RequestHandler: WebApp RequestHandler
  """
  
  def get(self):
    self.response.headers['Content-Type'] = 'text/plain'
    cache_time = urllib.unquote(cgi.escape(self.request.get(
        'cache_time', '3600')))
    compilation_level = str(urllib.unquote(cgi.escape(
        self.request.get('compilation_level', COMPRESSIONS[0]))))
    js_code = urllib.unquote(cgi.escape(self.request.get('js_code', '')))
    code_url = urllib.unquote(cgi.escape(self.request.get('code_url', '')))
    
    # Check Memcache
    if js_code and code_url:
      key = js_code + code_url
    elif js_code:
      key = js_code
    elif code_url:
      key = code_url
    
    data = check_memcache(key, compilation_level)
    
    if data is not None:
      self.response.out.write(data)
      return
    
    params = urllib.urlencode([
        ('code_url', code_url),
        ('js_code', js_code),
        ('compilation_level', compilation_level),
        ('output_format', 'text'),
        ('output_info', 'compiled_code'),
    ])
    
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    result = urlfetch.fetch(url=URL, payload=params, method=urlfetch.POST,
                            headers=headers)
    
    if result.status_code == 200:
      try:
        memcache.add(hashlib.md5(key).hexdigest() + ':' + compilation_level, 
                     result.content, 
                     int(cache_time))
        self.response.out.write(result.content)
      except ValueError:
        self.response.out.write("Error: Cache time not a valid number.")
    else:
      self.response.out.write("Error: Please try again soon.")

app = webapp2.WSGIApplication([('/compress', Compress),
                               ('/', MainHandler)], debug=True)
