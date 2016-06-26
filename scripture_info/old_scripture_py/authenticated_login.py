import urllib2
import cookielib

#theurl = 'http://quac-gviz.corp.google.com/topqueries?period=W2012W06&searchResultLimit=10&geography=US&category=0&metric=QUERIES&tq=select%20*%20order%20by%20queries%20desc&tqx=reqId:0;out:html'
theloginurl = 'https://login.facebook.com/login.php'
theurl = 'http://www.facebook.com'
username = raw_input('username [dannyyoung]: ')
if not username:
    username = 'dannyyoung'
password = raw_input("Enter password: ")
OTP = raw_input("Enter OTP: ")
cookie_filename = "google.cookies"
#password = 'XXXXXX'
# a great password

passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
# this creates a password manager
passman.add_password(None, theurl, username, password)
# because we have put None at the start (for Realm) it will always
# use this username/password combination for  urls
# for which `theurl` is a super-url

authhandler = urllib2.HTTPBasicAuthHandler(passman)
# create the AuthHandler

cookiejar = cookielib.MozillaCookieJar(cookie_filename)
# create the cookiejar (optional)

opener = urllib2.build_opener(
    urllib2.HTTPCookieProcessor(cookiejar),
    authhandler
)

opener.addheaders = [
    ('User-agent', ('Mozilla/4.0 (compatible; MSIE 6.0; '
                           'Windows NT 5.2; .NET CLR 1.1.4322)'))
]
# spoof the User-agent (optional)


urllib2.install_opener(opener)
# All calls to urllib2.urlopen will now use our handler
# Make sure not to include the protocol in with the URL, or
# HTTPPasswordMgrWithDefaultRealm will be very confused.
# You must (of course) use it when fetching the page though.

pagehandle = urllib2.urlopen(theloginurl)
pagehandle = urllib2.urlopen(theloginurl)
# Do this twice, once to set the cookie and again to log in
pagehandle = urllib2.urlopen(theurl)
# authentication is now handled automatically for us

contents = pagehandle.read()
open("page_output.html", "w").write(contents)
