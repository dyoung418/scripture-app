import urllib2
import mechanize #good for getting pages -- supports cookies, etc.
import lxml.html #a good html parser, fast, handles broken html, etc.
import cookielib
import time
import random
import json
import operator
import itertools
import re
import pprint

SLEEP = 5

def _init_browser():
    '''Set options for mechanize so it acts most closely like a browser'''
    br = mechanize.Browser()
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # Want debugging messages?
    #br.set_debug_http(True)
    #br.set_debug_redirects(True)
    #br.set_debug_responses(True)

    # User-Agent 
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    return br

def _get_page(mech_browser, url):
    retry = retry_limit = 3
    while retry > 0:
        retry -= 1
        try:
            r = mech_browser.open(url)
            html = r.read()
        except mechanize.HTTPError as e:
            if retry > 0:
                print 'received error: ', e, ': trying again' #internal server error - let loop go to try again
            else:
                print 'received error: ', e, ': reached retry limit -- exiting.'
        else:
            break
    if r: r.close()
    return html

def scrape_chapter(mech_browser, url, main_content_style='verses'):
    '''reads url (an lds.org page of one chapter) and returns tuple of
    (num_verses, num_words, [nwords, nwords, nwords,...], [text, text, ...])'''
    html = _get_page(mech_browser, url)
    doc = lxml.html.fromstring(html)
    main_content = doc.find_class(main_content_style) #returns a list, but there should just be one 'verses' class element on the page
    if main_content:
        main_content = main_content[0]
        verse_markers = main_content.find_class('verse')
        if verse_markers:
            for v in verse_markers:
                v.drop_tree() #get rid of verse number, but keep tail (the first few words of the verse)
                    #if I wanted to get rid of tail text too, I could write v.getparent().remove(v)
                    # DAY reminder: "text" is the portion that falls inside open and close tags
                    #               "tail" is text that falls between two different tags
                    # Example
                    #           <tag>text here</tag> more text<newtag></newtag>
                    #
                    # "text" is "text here"
                    # "tail" is " more text"
        footnote_markers = main_content.find_class('studyNoteMarker')
        if footnote_markers:
            for s in footnote_markers:
                s.drop_tree() #remove footnote markers (e.g. 'a', 'b', 'c')
        num_verses = 0
        verse_word_lens = []
        verse_texts = []
        for num, verse in enumerate(main_content.iter('p'),1):
            text = verse.text_content().strip()
            uri = verse.attrib.get('uri')  #not doing anything with this right now
            # for verses with text outside (and in between) the <p> tags like
            # D&C 84:99, iterate through all tags between <p> tags to add their
            # text
            next_el = verse.getnext()
            while next_el is not None and next_el.tag != 'p':
                text += next_el.text_content().strip() + ' '
                next_el = next_el.getnext()
            verse_word_lens.append(len(text.split()))
            verse_texts.append(text) # DAY FIXME - figure out what to do with summaries like at chapter heads and in the middle of js-h 1
            num_verses += 1
            #print "%d: %s" % (num, verse.text_content())
        return (num_verses, sum(verse_word_lens), verse_word_lens, verse_texts)

def scrape_book(mech_browser, book_name, url_name_list, sleep=SLEEP, verbose=False):
    '''Scrape a book of scripture (as in book of Genesis), or just an arbitrarly list of chapter pages from
    url_name_list.
    url_name_list is a list of tuples with url, names and main_content_style (e.g. [ ('http://blah', 'Mormon 3', 'verses'), (...,...), ] )
    Return a list of tuples of (name, num_verses, num_words, [nwords, nwords, ...], [text, text, ...])'''
    chapter_results = []
    if verbose: print 'Getting: '
    for url, name, main_content_style in url_name_list:
        if verbose: print name,
        num_verses, num_words, verse_lens, verse_texts = scrape_chapter(mech_browser, url, main_content_style=main_content_style)
        chapter_results.append( (name, num_verses, num_words, verse_lens, verse_texts) )
        time.sleep(sleep+random.uniform(-1*sleep/2.0, sleep/2.0))
    if verbose: print ''
    num_chapters = len(chapter_results)
    num_verses = sum(itertools.imap(operator.itemgetter(1), chapter_results))
    num_words = sum(itertools.imap(operator.itemgetter(2), chapter_results))
    return [book_name, num_chapters, num_verses, num_words, chapter_results]

def scrape_scripture(script_name, url_base, books, sleep=SLEEP, verbose=False):
    '''Scrape all the information for an entire scripture (as in Old Testament, or Book of Mormon)
    Return a datastructure with information about the scripture in the following
    format:  [ scripture_name, url_base, n_books, n_chapters, n_verses, n_words,
               [ book_name1, n_chapters, n_verses, n_words,
                   [ chapter_name1, n_verses, n_words, [nversewords, nversewords, ...],
                                                       [versetext, versetext, ...]
                   ],
                   [ chapter_name2, ...etc ], ...etc
                ], ...etc
             ]
    inputs: script_name is the name of the scripture (e.g. nt for new testament)
    url_base is the url with a %s for the book name (i.e. matt) and a %d for
    the chapter number, books is a list of tuples: [ (book, book_nickname, n_chapters), (...), ...]'''
    br = _init_browser()
    url_and_names = []
    book_results = []
    for book, book_nickname, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book_nickname, ch), book+' %d'%ch, 'article' if book_nickname=='od' else 'verses') )
        info = scrape_book(br, book, url_and_names, sleep=sleep, verbose=verbose)
        book_results.append(info)
        url_and_names = []
    num_books = len(books)
    num_chapters = sum(itertools.imap(operator.itemgetter(1), book_results))
    num_verses = sum(itertools.imap(operator.itemgetter(2), book_results))
    num_words = sum(itertools.imap(operator.itemgetter(3), book_results))
    return [script_name, url_base, num_books, num_chapters, num_verses, num_words, book_results]

def get_all_script_info():       
    my_sleep = 1
    scripts = [
                ['pgp', 'http://www.lds.org/scriptures/pgp/%s/%d?lang=eng',
                   [('Moses', 'moses', 8), ('Abraham', 'abr', 5), (u'Joseph Smith\u2014Matthew', 'js-m', 1),
                    (u'Joseph Smith\u2014History', 'js-h', 1), ('Articles of Faith', 'a-of-f', 1)
                ]],
                ['bofm', 'http://www.lds.org/scriptures/bofm/%s/%d?lang=eng',
                   [('1 Nephi', '1-ne', 22), ('2 Nephi', '2-ne', 33), ('Jacob', 'jacob', 7),
                    ('Enos', 'enos', 1), ('Jarom', 'jarom', 1), ('Omni', 'omni', 1),
                    ('Words of Mormon', 'w-of-m', 1), ('Mosiah', 'mosiah', 29), ('Alma', 'alma', 63),
                    ('Helaman', 'hel', 16), ('3 Nephi', '3-ne', 30), ('4 Nephi', '4-ne', 1),
                    ('Mormon', 'morm', 9), ('Ether', 'ether', 15), ('Moroni', 'moro', 10)
                ]],
                ['nt', 'http://www.lds.org/scriptures/nt/%s/%d?lang=eng',
                   [('Matthew', 'matt', 28), ('Mark', 'mark', 16), ('Luke', 'luke', 24),
                    ('John', 'john', 21), ('Acts', 'acts', 28), ('Romans', 'rom', 16),
                    ('1 Corinthians', '1-cor', 16), ('2 Corinthians', '2-cor', 13),
                    ('Galatians', 'gal', 6), ('Ephesians', 'eph', 6), ('Philippians', 'philip', 4),
                    ('Colossians', 'col', 4), ('1 Thessalonians', '1-thes', 5),
                    ('2 Thessalonians', '2-thes', 3), ('1 Timothy', '1-tim', 6),
                    ('2 Timothy', '2-tim', 4), ('Titus', 'titus', 3), ('Philemon', 'philem', 1),
                    ('Hebrews', 'heb', 13), ('James', 'james', 5), ('1 Peter', '1-pet', 5),
                    ('2 Peter', '2-pet', 3), ('1 John', '1-jn', 5), ('2 John', '2-jn', 1),
                    ('3 John', '3-jn', 1), ('Jude', 'jude', 1), ('Revelation', 'rev', 22)
                ]],
                ['ot', 'http://www.lds.org/scriptures/ot/%s/%d?lang=eng',
                   [('Genesis', 'gen', 50), ('Exodus', 'ex', 40), ('Leviticus', 'lev', 27),
                    ('Numbers', 'num', 36), ('Deuteronomy', 'deut', 34), ('Joshua', 'josh', 24),
                    ('Judges', 'judg', 21), ('Ruth', 'ruth', 4), ('1 Samuel', '1-sam', 31),
                    ('2 Samuel', '2-sam', 24), ('1 Kings', '1-kgs', 22), ('2 Kings', '2-kgs', 25),
                    ('1 Chronicles', '1-chr', 29), ('2 Chronicles', '2-chr', 36), ('Ezra', 'ezra', 10),
                    ('Nehemiah', 'neh', 13), ('Esther', 'esth', 10), ('Job', 'job', 42),
                    ('Psalms', 'ps', 150), ('Proverbs', 'prov', 31), ('Ecclesiastes', 'eccl', 12),
                    ('Song of Solomon', 'song', 8), ('Isaiah', 'isa', 66), ('Jeremiah', 'jer', 52),
                    ('Lamentations', 'lam', 5), ('Ezekiel', 'ezek', 48), ('Daniel', 'dan', 12),
                    ('Hosea', 'hosea', 14), ('Joel', 'joel', 3), ('Amos', 'amos', 9), ('Obadiah', 'obad', 1),
                    ('Jonah', 'jonah', 4), ('Micah', 'micah', 7), ('Nahum', 'nahum', 3),
                    ('Habakkuk', 'hab', 3), ('Zephaniah', 'zeph', 3), ('Haggai', 'hag', 2),
                    ('Zechariah', 'zech', 14), ('Malachi', 'mal', 4)
                ]],
                ['dc-testament', 'http://www.lds.org/scriptures/dc-testament/%s/%d?lang=eng#',
                   [('D&C', 'dc', 138), ('D&C Official Declarations', 'od', 2)
                ]]
            ]

    for s in scripts:
        info = scrape_scripture(s[0], s[1], s[2], sleep=my_sleep, verbose=True)
        try:
            f = open(s[0]+'_info.json', 'w')
            f.write(json.dumps(info))
            print ''
            print 'Finished writing %s to file' % s[0]+'_info.json'
            print ''
        finally:
            f.close()

def simplify_info(scriptures=None):
    if scriptures==None:
        scriptures = ['dc-testament', 'bofm', 'pgp', 'ot', 'nt']
    all_scripts = []
    for fname in scriptures:
        try:
            f = open(fname+'_info.json', 'r')
            data = json.loads(f.read())
        except:
            "Could not read %s" % name+'_info.json'
            break
        finally:
            f.close()
        scripture_name = data[0]
        url = data[1]
        total_books = data[2]
        total_chapters = data[3]
        total_verses = data[4]
        total_words = data[5]
        book_list = data[6]
        print '%s: read item with %d entries.  Each entry has %d items' % (scripture_name,
                                                                           len(book_list),
                                                                           len(book_list[0]))
        simple_book_list = []
        for book in book_list:
            book_name = book[0]
            book_chapters = book[1]
            book_verses = book[2]
            book_words = book[3]
            chapter_list = book[4]

            simple_chapter_list = []
            for chapter in chapter_list:
                simple_chapter_list.append(chapter[:3]) # keep chap_name, #verses, #words; drop the text and anything after
            simple_book_list.append( (book_name, book_chapters, book_verses, book_words, simple_chapter_list) )
        all_scripts.append( [scripture_name, url, total_books, total_chapters,
                             total_verses, total_words, simple_book_list] )
    return all_scripts


def generate_book_chapter_list(sleep=1):
    '''Used once to generate the "scripts" list used in get_all_script_info()
    It goes online and looks at all the books within a scripture and captures how many chapters each
    has.
    Note that I just manually copy/past the output from a terminal window into the
    get_all_script_info code.'''
    standard_works = [
        'bofm',
        'pgp',
        'nt',
        'ot'
        ] # structure of D&C is different and simple: two books (dc, od), (138, 2) chapters
    url_base = r'http://www.lds.org/scriptures/'
    result = []
    br = mechanize.Browser()
    for scripture in standard_works:
        books_list = []
        time.sleep(sleep)
        print 'Getting', scripture
        html = _get_page(br, url_base+scripture+r'?lang=eng')
        doc = lxml.html.fromstring(html)
        toc = doc.find_class('table-of-contents') #returns a list, but there should only be one
        if toc:
            book_section = toc[0].find_class('books') #might not be there, but if it is, it is a better starting place
            if book_section:
                toc = book_section
        else:
            print 'No table of contents found for %s' % scripture
            continue
        for t in toc: # there might be more than one if I used the book_section (one for each column)
            books = t.findall(r'.//a[@href]') # the links in this section will be the books in the scripture
            for book in books:
                name = book.text_content()
                href = book.attrib.get('href')
##                match = re.find( url_base+r'([^?]+)\?lang=eng', href)
##                if match:
##                    nickname = match.group(1)
                if href.startswith(url_base):
                    nickname = href[len(url_base)+len(scripture)+1:-1*len('?lang=eng')]
                    if nickname.endswith('/1'): nickname = nickname[:-2] #books with one chapter include '/1'. strip it off
                    print nickname,
                    time.sleep(sleep)
                    chapter_page_html = _get_page(br, href)
                    chap_doc = lxml.html.fromstring(chapter_page_html)
                    jtc = chap_doc.find_class('jump-to-chapter')
                    if jtc is None or len(jtc) == 0: #then this book has only one chapter
                        num_chapters = 1
                    else:
                        num_chapters = len(jtc[0].findall(r'.//a'))
                    books_list.append( (name, nickname, num_chapters) )
        result.append( [scripture, url_base+scripture+'/%s/%d?lang=eng', books_list] )
    print result
    return result

        
if __name__ == '__main__':
    
##    generate_book_chapter_list()    
##    get_all_script_info()
    info = simplify_info(scriptures=['dc-testament', 'bofm', 'pgp', 'ot', 'nt'])
    try:
        f = open('all_scripts_basic_info.json', 'w')
        f.write(json.dumps(info))
    finally:
        f.close()
    print ""
    print "Done."
