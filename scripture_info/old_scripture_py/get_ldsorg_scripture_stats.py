import urllib2
import mechanize #good for getting pages -- supports cookies, etc.
import lxml.html #a good html parser, fast, handles broken html, etc.
import cookielib
import time
import random
import json
import pprint

SLEEP = 5

def init_browser():
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

def get_page(mech_browser, url):
    r = mech_browser.open(url)
    html = r.read()
    return html

def get_verses_words(mech_browser, url, main_content_style='verses'):
    '''return tuple of (num_verses, num_words, [nwords, nwords, nwords,...], [text, text, ...])'''
    html = get_page(mech_browser, url)
    doc = lxml.html.fromstring(html)
    main_content = doc.find_class(main_content_style) #returns a list, but there should just be one 'verses' class element on the page
    if main_content:
        main_content = main_content[0]
        verse_markers = main_content.find_class('verse')
        if verse_markers:
            for v in verse_markers:
                v.drop_tree() #get rid of verse number, but keep tail (the first few words of the verse)
                    #if I wanted to get rid of tail text too, I could write v.getparent().remove(v)
        footnote_markers = main_content.find_class('studyNoteMarker')
        if footnote_markers:
            for s in footnote_markers:
                s.drop_tree() #remove footnote markers (e.g. 'a', 'b', 'c')
        #all_verses = main_content.findall('p')
        #num_verses = len(all_verses)
        num_verses = 0
        verse_word_lens = []
        verse_texts = []
        verse_urls = []
        for num, verse in enumerate(main_content.iter('p'),1):
            text = verse.text_content().strip()
            uri = verse.attrib.get('uri')  
            # for verses with text outside (and in between) the <p> tags like
            # D&C 84:99, iterate through all tags between <p> tags to add their
            # text
            next_el = verse.getnext()
            while next_el is not None and next_el.tag != 'p':
                text += next_el.text_content().strip() + ' '
                next_el = next_el.getnext()
            #if uri:
            #    verse_urls.append('http://www.lds.org'+uri+'?lang=eng')
            else:
                verse_urls.append('')
            verse_word_lens.append(len(text.split()))
            verse_texts.append(text) # DAY FIXME - figure out what to do with summaries like at chapter heads and in the middle of js-h 1
            num_verses += 1
            #print "%d: %s" % (num, verse.text_content())
        return (num_verses, sum(verse_word_lens), verse_word_lens, verse_texts, verse_urls)

def get_chapter_info(mech_browser, url_name_list, sleep=SLEEP, verbose=False, main_content_style='verses'):
    '''Take a list of tuples with url and names (e.g. [ ('http://blah', 'Mormon 3'), (...,...), ...] ) and return
    a list of tuples of (name, num_verses, num_words, [nwords, nwords, ...], [text, text, ...])'''
    results = []
    if verbose: print 'Getting: '
    for url, name in url_name_list:
        if verbose: print name,
        num_verses, num_words, verse_lens, verse_texts, verse_urls = get_verses_words(mech_browser, url, main_content_style=main_content_style)
        results.append( (name, num_verses, num_words, verse_lens, verse_texts, verse_urls) )
        time.sleep(sleep+random.uniform(-1*sleep/2.0, sleep/2.0))
    if verbose: print ''
    return results

def get_doctrine_and_covenants_info(outfile='dandc_info.json', sleep=SLEEP, verbose=False, limit=None):
    url_and_names = []
    for section in range(1, 138+1):
        url_and_names.append(('http://www.lds.org/scriptures/dc-testament/dc/%d?lang=eng#' % section, 'D&C %d'%section))

    #dc_info = get_chapter_info(url_and_names[:3], verbose=True) #DEBUG
    if limit and isinstance(limit, int):
        dc_info = get_chapter_info(url_and_names[:limit], sleep=sleep, verbose=verbose)
    else:
        dc_info = get_chapter_info(url_and_names, sleep=sleep, verbose=verbose)

    od_url_and_names = []
    for od in range(1, 2+1):
        od_url_and_names.append(('http://www.lds.org/scriptures/dc-testament/od/%d?lang=eng#' % od, 'D&C Official Declaration %d'%od))

    od_info = get_chapter_info(od_url_and_names, sleep=sleep, verbose=verbose, main_content_style='article')

    info = dc_info + od_info
    f = open(outfile, 'w')
    f.write(json.dumps(info))
    f.close()
    return info

def get_pearl_of_great_price_info(outfile='pgp_info.json', sleep=SLEEP, verbose=False, limit=None):
    url_base = 'http://www.lds.org/scriptures/pgp/%s/%d?lang=eng'
    books = [('moses', 8), ('abr', 5), ('js-m', 1), ('js-h', 1), ('a-of-f', 1)]
    url_and_names = []
    for book, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book, ch), book+' %d'%ch) )
    if limit and isinstance(limit, int):
        info = get_chapter_info(url_and_names[:limit], sleep=sleep, verbose=verbose)
    else:
        info = get_chapter_info(url_and_names, sleep=sleep, verbose=verbose)
    f = open(outfile, 'w')
    f.write(json.dumps(info))
    f.close()
    return info
        
            

def get_book_of_mormon_info(outfile='bom_info.json', sleep=SLEEP, verbose=False, limit=None):
    url_base = 'http://www.lds.org/scriptures/bofm/%s/%d?lang=eng'
    books = [('1-ne', 22), ('2-ne', 33), ('jacob', 7), ('enos', 1), ('jarom', 1), ('omni', 1),
             ('w-of-m', 1), ('mosiah', 29), ('alma', 63), ('hel', 16), ('3-ne', 30), ('4-ne', 1),
             ('morm', 9), ('ether', 15), ('moro', 10)]
    url_and_names = []
    for book, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book, ch), book+' %d'%ch) )
    if limit and isinstance(limit, int):
        info = get_chapter_info(url_and_names[:limit], sleep=sleep, verbose=verbose)
    else:
        info = get_chapter_info(url_and_names, sleep=sleep, verbose=verbose)
    f = open(outfile, 'w')
    f.write(json.dumps(info))
    f.close()
    return info

def get_old_testament_info(outfile='ot_info.json', sleep=SLEEP, verbose=False, limit=None):
    url_base = 'http://www.lds.org/scriptures/ot/%s/%d?lang=eng'
    books = [('gen', 50), ('ex', 40), ('lev', 27), ('num', 36), ('deut', 34), ('josh', 24),
             ('judg', 21), ('ruth', 4), ('1-sam', 31), ('2-sam', 24), ('1-kgs', 22), ('2-kgs', 25),
             ('1-chr', 29), ('2-chr', 36), ('ezra', 10), ('neh', 13), ('esth', 10), ('job', 42),
             ('ps', 150), ('prov', 31), ('eccl', 12), ('song', 8), ('isa', 66), ('jer', 52),
             ('lam', 5), ('ezek', 48), ('dan', 12), ('hosea', 14), ('joel', 3), ('amos', 9),
             ('obad', 1), ('jonah', 4), ('micah', 7), ('nahum', 3), ('hab', 3), ('zeph', 3),
             ('hag', 2), ('zech', 14), ('mal', 4)]
    url_and_names = []
    for book, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book, ch), book+' %d'%ch) )
    if limit and isinstance(limit, int):
        info = get_chapter_info(url_and_names[:limit], sleep=sleep, verbose=verbose)
    else:
        info = get_chapter_info(url_and_names, sleep=sleep, verbose=verbose)
    f = open(outfile, 'w')
    f.write(json.dumps(info))
    f.close()
    return info

def get_new_testament_info(outfile='nt_info.json', sleep=SLEEP, verbose=False, limit=None):
    url_base = 'http://www.lds.org/scriptures/nt/%s/%d?lang=eng'
    books = [('matt', 28), ('mark', 16), ('luke', 24), ('john', 21), ('acts', 28), ('rom', 16),
             ('1-cor', 16), ('2-cor', 13), ('gal', 6), ('eph', 6), ('philip', 4), ('col', 4),
             ('1-thes', 5), ('2-thes', 3), ('1-tim', 6), ('2-tim', 4), ('titus', 3), ('philem', 1),
             ('heb', 13), ('james', 5), ('1-pet', 5), ('2-pet', 3), ('1-jn', 5), ('2-jn', 1),
             ('3-jn', 1), ('jude', 1), ('rev', 22)]
    url_and_names = []
    for book, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book, ch), book+' %d'%ch) )
    if limit and isinstance(limit, int):
        info = get_chapter_info(url_and_names[:limit], sleep=sleep, verbose=verbose)
    else:
        info = get_chapter_info(url_and_names, sleep=sleep, verbose=verbose)
    f = open(outfile, 'w')
    f.write(json.dumps(info))
    f.close()
    return info

def get_scripture_info(url_base, books, sleep=SLEEP, verbose=False, limit=None, main_content_style='verses'):
    '''Get a datastructure with information about the scripture in the following
    format:  [ [ chapter_name, n_verses, n_words, [nversewords, nversewords, ...],
                 [versetext, versetext, ...], [verseurl, verseurl, ...]
               ],
               [ chapter_name, ...etc ]
             ]
    inputs: url_base is the url with a %s for the book name (i.e. matt) and a %d for
    the chapter number, books is a list of tuples: [ (book, n_chapters), (...), ...]'''
    br = init_browser()
    url_and_names = []
    for book, num_chaps in books:
        for ch in range(1, num_chaps+1):
            url_and_names.append( (url_base%(book, ch), book+' %d'%ch) )
    if limit and isinstance(limit, int):
        info = get_chapter_info(br, url_and_names[:limit], sleep=sleep, verbose=verbose,
                                main_content_style='article' if book=='od' else main_content_style)
    else:
        info = get_chapter_info(br, url_and_names, sleep=sleep, verbose=verbose,
                                main_content_style='article' if book=='od' else main_content_style)
    return info

def simplify_info(files):
    for fname in files:
        try:
            f = open(fname+'_info.json', 'r')
            data = json.loads(f.read())
        finally:
            f.close()
        print '%s: read item with %d entries.  Each entry has %d items' % (fname, len(data), len(data[0]))

def get_all_script_info():       
    my_sleep = 4
    scripts = [
                [ 'dandc', 'http://www.lds.org/scriptures/dc-testament/%s/%d?lang=eng#',
                  [('dc', 138), ('od', 2)]
                ],
                [ 'pgp', 'http://www.lds.org/scriptures/pgp/%s/%d?lang=eng',
                  [('moses', 8), ('abr', 5), ('js-m', 1), ('js-h', 1), ('a-of-f', 1)]
                ],
                [ 'bom', 'http://www.lds.org/scriptures/bofm/%s/%d?lang=eng',
                  [('1-ne', 22), ('2-ne', 33), ('jacob', 7), ('enos', 1), ('jarom', 1), ('omni', 1),
                   ('w-of-m', 1), ('mosiah', 29), ('alma', 63), ('hel', 16), ('3-ne', 30), ('4-ne', 1),
                   ('morm', 9), ('ether', 15), ('moro', 10)]
                ],
                [ 'nt', 'http://www.lds.org/scriptures/nt/%s/%d?lang=eng',
                  [('matt', 28), ('mark', 16), ('luke', 24), ('john', 21), ('acts', 28), ('rom', 16),
                   ('1-cor', 16), ('2-cor', 13), ('gal', 6), ('eph', 6), ('philip', 4), ('col', 4),
                   ('1-thes', 5), ('2-thes', 3), ('1-tim', 6), ('2-tim', 4), ('titus', 3), ('philem', 1),
                   ('heb', 13), ('james', 5), ('1-pet', 5), ('2-pet', 3), ('1-jn', 5), ('2-jn', 1),
                   ('3-jn', 1), ('jude', 1), ('rev', 22)]
                ],
                [ 'ot', 'http://www.lds.org/scriptures/ot/%s/%d?lang=eng',
                  [('gen', 50), ('ex', 40), ('lev', 27), ('num', 36), ('deut', 34), ('josh', 24),
                   ('judg', 21), ('ruth', 4), ('1-sam', 31), ('2-sam', 24), ('1-kgs', 22), ('2-kgs', 25),
                   ('1-chr', 29), ('2-chr', 36), ('ezra', 10), ('neh', 13), ('esth', 10), ('job', 42),
                   ('ps', 150), ('prov', 31), ('eccl', 12), ('song', 8), ('isa', 66), ('jer', 52),
                   ('lam', 5), ('ezek', 48), ('dan', 12), ('hosea', 14), ('joel', 3), ('amos', 9),
                   ('obad', 1), ('jonah', 4), ('micah', 7), ('nahum', 3), ('hab', 3), ('zeph', 3),
                   ('hag', 2), ('zech', 14), ('mal', 4)]
                ]
            ]
    for s in scripts:
        info = get_scripture_info( s[1], s[2], sleep=my_sleep, verbose=True)
        try:
            f = open(s[0]+'_info.json', 'w')
            f.write(json.dumps(info))
        finally:
            f.close()

    
if __name__ == '__main__':
    
##    get_all_script_info()
    simplify_info(['dandc', 'bom', 'pgp'])
    print "Done."
