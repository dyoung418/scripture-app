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


    WebApp format (5 separate files):

    example: filename bofm.json

    {books: ['1st Nephi', '2nd Nephi', ...],
     chapWordsByBook: [ [209, 190, ...],  // 1st Nephi (# entries=#chapters, 
                                    //            value=#words in that chapter)
                  [188, 309, ...],  // 2nd Nephi
                  ...
                ]
    }

    '''
    outputList = []
    for scriptureList in complexInfo:
        # Scripture
        bookNames = []
        bookChapters = []
        chapterVerses = []
        chapterWords = []
        scriptureSummary = scriptureList[0]
        bookInput = scriptureList[1]

        outputDict = {}
        outputDict['name'] = scriptureSummary['name']
        outputDict['info'] = {}
        outputDict['info']['chapWordsByBook'] = [] # this will be a list of lists.  (one list for each book)

        for bookList in bookInput:
            # Book
            bookSummary = bookList[0]
            chapterList = bookList[1]
            bookNames.append(bookSummary['name'])
            bookChapters.append(bookSummary['chapters'])
            chapWords = []
            chapVerses = [] # don't plan on using this, but will gather for possible future use.
            for chapterSummary in chapterList:
                chapVerses.append(chapterSummary['verses'])
                chapWords.append(chapterSummary['words'])
            outputDict['info']['chapWordsByBook'].append(chapWords)
        outputDict['info']['books'] = bookNames
        outputList.append(outputDict)
        #print(outputDict)
    return outputList

def writeWebAppInfo(simpleInfoList):
    print(simpleInfoList)
    for bookDict in simpleInfoList:
        with open('{}.json'.format(bookDict['name']), 'w') as f:
            f.write(json.dumps(bookDict['info']))

if __name__ == '__main__':
    writeWebAppInfo(simplifyComplexInfo(getComplexInfo()))
            
        
    
    
