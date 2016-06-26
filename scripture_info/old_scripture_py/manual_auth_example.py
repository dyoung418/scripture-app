import urllib2
import sys
import re
import base64
from urlparse import urlparse

theurl = 'http://www.someserver.com/somepath/somepage.html'
# if you want to run this example you'll need to supply
# a protected page with your username and password

theurl = 'http://quac-gviz.corp.google.com/topqueries?period=W2012W06&searchResultLimit=10&geography=US&category=0&metric=QUERIES&tq=select%20*%20order%20by%20queries%20desc&tqx=reqId:0;out:html'
#theloginurl = 'https://login.facebook.com/login.php'
#theurl = 'http://www.facebook.com'
username = raw_input('username [dannyyoung]: ')
if not username:
    username = 'dannyyoung'
password = raw_input("Enter password: ")
OTP = raw_input("Enter OTP: ")


req = urllib2.Request(theurl)
req.addheaders = [
            ('User-agent', ('Mozilla/4.0 (compatible; MSIE 6.0; '
                           'Windows NT 5.2; .NET CLR 1.1.4322)'))
            ]
try:
    handle = urllib2.urlopen(req)
except IOError, e:
    # here we *want* to fail
    print "Here we wanted to fail"
    print e
except e:
    print "Failed for some unexpected reason"
    print e
else:
    # If we don't fail then the page isn't protected
    print "This page isn't protected by authentication."
    sys.exit(1)

if not hasattr(e, 'code') or e.code != 401:
    # we got an error - but not a 401 error
    print "This page isn't protected by authentication."
    print 'But we failed for another reason.'
    print e
    sys.exit(1)

print e

authline = e.headers['www-authenticate']
print authline
# this gets the www-authenticate line from the headers
# which has the authentication scheme and realm in it


authobj = re.compile(
    r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
    re.IGNORECASE)
# this regular expression is used to extract scheme and realm
matchobj = authobj.match(authline)

if not matchobj:
    # if the authline isn't matched by the regular expression
    # then something is wrong
    print 'The authentication header is badly formed.'
    print authline
    sys.exit(1)

scheme = matchobj.group(1)
realm = matchobj.group(2)
# here we've extracted the scheme
# and the realm from the header
if scheme.lower() != 'basic':
    print 'This example only works with BASIC authentication.'
    sys.exit(1)

base64string = base64.encodestring(
                '%s:%s' % (username, password))[:-1]
authheader =  "Basic %s" % base64string
req.add_header("Authorization", authheader)
try:
    handle = urllib2.urlopen(req)
except IOError, e:
    # here we shouldn't fail if the username/password is right
    print "It looks like the username or password is wrong."
    sys.exit(1)
thepage = handle.read()
