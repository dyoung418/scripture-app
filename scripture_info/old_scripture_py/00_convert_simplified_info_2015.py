import json, os.path

def getComplexInfo():
    try:
        f = open('all_scripts_basic_info.json', 'r')
        inputInfo = json.load(f)
    finally:
        f.close()
    return inputInfo

def simplifyComplexInfo(complexInfo):
    '''
    complex format:
    [
      [scripture_info_dict, [list of book info] ],
      [scripture_info_dict, [list of book info] ], ...
    ]
    The scripture_info_dict is a dictionary with keys 'name', 'books',
    'chapters', 'verses', 'words'.

    book info format:
        [ [ book_info_dict, [list of chapter info] ],
          [ book_info_dict, [list of chapter info] ],
        ]
        In more detail, the book_info_dict and chapter information looks as follows:
        [
          [ {'name': 'Genesis', 'chapters': 123, 'verses': 123, 'words': 123},
            [
              [ {'name': 'Genesis 1', 'verses': 123, 'words': 123},
                [verse_words, verse_words, verse_words, ...],
                [verse_text, verse_text, verse_text, ...]
              ]
              [ {'name': 'Genesis 2', 'verses': 123, 'words': 123},
                [verse_words, verse_words, verse_words, ...]
                [verse_text, verse_text, verse_text, ...]
              ], ...
            ]
          ],
              
          [ {'name': 'Exodus', 'chapters': 123, 'verses': 123, 'words': 123},
            [
              [ {'name': 'Exodus 1', 'verses': 123, 'words': 123},
                [verse_words, verse_words, verse_words, ...]
                [verse_text, verse_text, verse_text, ...]
              ]
              [ {'name': 'Exodus 2', 'verses': 123, 'words': 123},
                [verse_words, verse_words, verse_words, ...]
                [verse_text, verse_text, verse_text, ...]
              ], ...
            ]
          ],

    Simplified format:
    [
        { 'name':'bofm',
          'numBooks':15,
          'numChapters':239, #redundant, but include in top-level only
          'numVerses':6604,  #redundant, but include in top-level only
          'numWords':266936,  #redundant, but include in top-level only
          'bookNames':['1st Nephi', '2nd Nephi', ...],
          'bookChapters':[[22, 5, ...], [12, 4, ..]], #list of numBook lists
          'chapterVerses':[18, 35, ...], #this will have sum(bookChapters) entries (ordered by bookNames)
          'chapterWords':[354, 415, ...] #this will have sum(bookChapters) entries (ordered by bookNames)
        },
        { 'name':'dc-testament',
           etc.
        }
    ] #this will have 5 entries (bofm, dc-testament, pgp, ot, nt)
    '''
    outputInfo = []
    for scriptureList in complexInfo:
        # Scripture
        bookNames = []
        bookChapters = []
        chapterVerses = []
        chapterWords = []
        scripture = scriptureList[0]
        bookInput = scriptureList[1]
        scriptureDict = {}
        scriptureDict['name'] = scripture['name']
        scriptureDict['numBooks'] = scripture['books']
        scriptureDict['numChapters'] = scripture['chapters']
        scriptureDict['numVerses'] = scripture['verses']
        scriptureDict['numWords'] = scripture['words']
        for bookList in bookInput:
            # Book
            book = bookList[0]
            chapterList = bookList[1]
            bookNames.append(book['name'])
            bookChapters.append(book['chapters'])
            for chapter in chapterList:
                chapterVerses.append(chapter['verses'])
                chapterWords.append(chapter['words'])
        scriptureDict['bookNames'] = bookNames
        scriptureDict['bookChapters'] = bookChapters
        scriptureDict['chapterVerses'] = chapterVerses
        scriptureDict['chapterWords'] = chapterWords
        outputInfo.append(scriptureDict)
    return outputInfo

def writeSimpleInfo(simpleInfo):
    try:
        f = open('00_all_scripts_simple_info.json', 'w')
        f.write(json.dumps(simpleInfo))
    finally:
        f.close()

if __name__ == '__main__':
    writeSimpleInfo(simplifyComplexInfo(getComplexInfo()))
            
        
    
    

