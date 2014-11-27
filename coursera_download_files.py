

#! /usr/bin/env python2.7
'Download all the class files to a local directory'

import os, re, dumbdbm, time, gzip, cStringIO, threading, sys, argparse

from collections import namedtuple
from multiprocessing.pool import ThreadPool as Pool
from pprint import pprint

# Web scrapping modules
import mechanize, cookielib
from BeautifulSoup import BeautifulSoup


Response = namedtuple('Response', ['code', 'msg', 'compressed', 'written'])

dirname = 'files'

def urlretrieve(url, filename, cache={}, lock=threading.Lock()):
    'Read contents of an open url, use etags and decompress if needed'    
    request = urllib2.Request(url)
    #request.add_header('Cache-Control', 'no-cache')
    # Not expecting compressed files
    #request.add_header('Accept-Encoding', 'gzip')
    with lock:
        if ('etag ' + url) in cache:
            request.add_header('If-None-Match', cache['etag ' + url])
        if ('mod ' + url) in cache:
            request.add_header('If-Modified-Since', cache['mod ' + url])

    try:
        u = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        return Response(e.code, e.msg, False, False)
    content = u.read()
    u.close()

    compressed = u.info().getheader('Content-Encoding') == 'gzip'
    #if compressed:                                       
    #    content = gzip.GzipFile(fileobj=cStringIO.StringIO(content), mode='rb').read()
    #else:

    soup = BeautifulSoup(content)
    # Let's take HTML out! soup.body(text=True) returns this as a list of **unicode**
    content = str(''.join(soup.body(text=True)))

    written = writefile(filename, content) 

    with lock:
        etag = u.info().getheader('Etag')
        if etag:
            cache['etag ' + url] = etag
        timestamp = u.info().getheader('Last-Modified')
        if timestamp:
            cache['mod ' + url] = timestamp

    return Response(u.code, u.msg, compressed, written)

def writefile(filename, content):
    "Only write content if it is not already written."
    try:
        with open(filename, 'rb') as f:
            curr_content = f.read()
            if curr_content == content:
                return False
    except IOError:
        pass
    with open(filename, 'wb') as f:
        f.write(content)
    return True

def download(target, dirname=dirname):
    'Retrieve a target url, save it as given filename and return the download status as a string'
    url, filename = target[0], target[1] if len(target) > 1 else target[0].split('/')[-1]
    filename = filename.rsplit('/', 1)[-1]
    fullname = os.path.join(dirname, filename)
    r = urlretrieve(url, fullname, etags)
    if r.code != 200:
        return '%3d  %-16s %s --> %s' % (r.code, r.msg, url, fullname)
    written = '(updated)' if r.written else '(current)'
    return '%3d%1s %-16s %-55s --> %-25s -> %s' % \
           (r.code, r.compressed, r.msg, url, fullname, fullname)


def parseCmdlineOptions():
    options = argparse.Options()
    # Option parsing from command line will be performed later
    return options

def login(browser):
    br.set_handle_robots(False)
    # Set cookie container
    cj = cookielib.CookieJar()
    br.set_cookiejar(cj)
    # Allow refresh of the content
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    # Set the fake user-agent and rest of headers to emulate the browser
    br.addheaders = [('User-agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'),
                     ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                     ('Accept-Encoding', 'gzip,deflate,sdch'),                  
                     ('Accept-Language', 'en-US,en;q=0.8'),                     
                     ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
                    ]

    logger = logging.getLogger("mechanize")
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    # Set the login url for coursera, the final url for the lectures is enclosed within the url here.
    br.open('https://accounts.coursera.org/signin?course_id=973439&r=https%3A%2F%2Fclass.coursera.org%2Fprogfun-005%2Flecture&user_action=class&topic_name=Functional%20Programming%20Principles%20in%20Scala')

    soup = BeautifulSoup(response.get_data())

    # Look for the right parts in the login form and fill them. Click in the button
    soup.select("signin-email").string("my-username")
    soup.select("signin-password").string("my-password")
    soup.select("btn bt-success coursera-signin-button").


if __name__ == '__main__':
    try:
        os.mkdir(dirname)
    except OSError:
        pass

    coursera_course_url = 'https://class.coursera.org/progfun-005/lecture'

    # Set up mechanize to perform login and handle redirection to the download area.
    br = mechanize.Browser()
    if login(br):
        pass

    etags = dumbdbm.open(os.path.join(dirname, 'etag_db'))
    try:    
        content = urllib2.urlopen(files_url)
        content_html = content.read()
        print (' Index page downloaded, parsing files to download').center(117, '=')
        soup = BeautifulSoup(content_html)
        targets = []
        for link in soup.findAll('a'):
            parts = content.geturl().split('/')
            # parts will be 'http:','','whatever','whatever','whatever','index.html'
            parts.pop(1)
            parts[0] = 'http:/'
            parts.pop(-1)
            parts.append(link.get('href'))
            # parts from BeautifulSoup are unicode, but key searching above will be string
            fullurl = str('/'.join(parts))
            targets.append([fullurl, link.text])        
        print (' Starting download at %s ' % time.ctime()).center(117)        
        mapper = Pool(25).imap if sys.version_info < (2, 7) else Pool(25).imap_unordered
        for line in mapper(download, targets):
            print line

    finally:
        etags.close()

