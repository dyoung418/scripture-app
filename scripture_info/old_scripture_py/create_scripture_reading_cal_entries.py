
from apiclient.discovery import build
from apiclient.oauth import OAuthCredentials

import httplib2
import oauth2 as oauth

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from oauth2client.client import AccessTokenRefreshError

import logging
import pprint
import datetime, calendar


FLOW = OAuth2WebServerFlow(
    client_id='222187858874.apps.googleusercontent.com',
    client_secret='5aubG5F0dIe5yoApuVxiSRNO',
    scope='https://www.googleapis.com/auth/calendar',
    user_agent='DAY calendar app/1.0')

CALENDAR = 'danny@youngshome.com'

def prepare_credentials(flow=None, cred_filename='calendar.dat'):
    """Handles auth. Reuses credentialss if available or runs the auth flow."""

    # If the credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    if not flow: flow=FLOW
    storage = Storage(cred_filename)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
      credentials = run(flow, storage)
    return credentials


def retrieve_service(http, service_name='calendar', version='v3'):
    """Retrieves API service via the discovery service."""

    # Construct a service object via the discovery service.
    service = build(service_name, version, http=http)
    return service


def initialize_service(flow=None, cred_filename='calendar.dat', service_name='calendar', version='v3'):
    """Builds instance of service from discovery data and does auth."""

    if not flow: flow=FLOW
    # Create an httplib2.Http object to handle our HTTP requests.
    http = httplib2.Http()

    # Prepare credentials, and authorize HTTP object with them.
    credentials = prepare_credentials(flow=flow, cred_filename=cred_filename)
    http = credentials.authorize(http)

    # Retrieve service.
    return retrieve_service(http, service_name=service_name, version=version)

def create_cal_event(service, calendarId=CALENDAR, summary='automatic calendar event', location='',
                     start='2012-06-15T10:00:00.000-07:00', end='2012-06-15T10:00:00.000-07:00',
                     attendee_email=CALENDAR,
                     colorID='1'):
    '''Create a calendar event.  Must be provided an authorized Google calendar service object'''
    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': start
        },
        'end': {
            'dateTime': end
        },
        'attendees': [
            {
                'email': attendee_email
            },
        ],
        'colorId': colorID
    }

    created_event = service.events().insert(calendarId=calendarId, body=event).execute()

    print 'Created event at id: ', created_event['id']
    return created_event['id']

def delete_cal_event(service, eventID=None, calendarID=None, prompt=True):
    '''Delete single calendar event identified by eventID.'''
    if not eventID or not calendarID:
        return
    else:
        confirmed_delete = not prompt
        if prompt:
            if raw_input("Confirm deletion of %s? "%eventID) in ['y', 'Y', 'yes']:
                confirmed_delete = True
            else: confirmed_delete = False
        if confirmed_delete:
            service.events().delete(calendarId=calendarID, eventId=eventID).execute()
    

def delete_matching_cal_events(service, calendarID=CALENDAR,  q=None, batchsize=10):
    '''Delete all calendar events that match query criteria.  Will prompt to confirm'''
    if not calendarID or not q:
        return
    else:
        events = service.events().list(calendarId=calendarID, maxResults=batchsize,
                                           singleEvents=True, orderBy='startTime', q=q).execute()
        #pprint.pprint(events) #debug
        while True:
            for n, event in enumerate(events['items']):
                print "%d: %s - %s" % (n, event['summary'], str(event['start']))
            answer = raw_input("Delete <ALL>, <STOP>, delete <num> or skip these and show [NEXT]: ")
            try:
                del_index = int(answer)
            except ValueError:
                if answer == 'STOP':
                    break
                elif answer == 'NEXT':
                    pass
                elif answer == 'ALL':
                    for num, e in enumerate(events['items']):
                        print "Deleting %d: %s - %s" % (num, e['summary'], str(e['start']))
                        service.events().delete(calendarId=calendarID,
                                            eventId=e['id']).execute()
            else:
                if del_index < len(events['items']):
                    e = events['items'][del_index]
                    if raw_input("Delete entry %d: %s, %s? [YES]" % (del_index, e['id'], str(e['start']))) in ['YES']:
                        service.events().delete(calendarId=calendarID,
                                            eventId=e['id']).execute()
            page_token = events.get('nextPageToken')
            if page_token:
                events = service.events().list(calendarId=calendarID, pageToken=page_token, maxResults=batchsize).execute()
            else:
                break

            



def calendar_tests():
    #logging.getLogger().setLevel(logging.DEBUG)

    service = initialize_service()

    try:
        ###########################
        #Get list of calendars
        calendar_list = service.calendarList().list().execute()
        #pprint.pprint(calendar_list) #DEBUG
        print ' '.join([entry['summary'] for entry in calendar_list['items']]) #note that this doesn't get additional pages with 'nextPageToken'
        while True:
            for calendar_list_entry in calendar_list['items']:
                #print calendar_list_entry['summary']
                pass
            page_token = calendar_list.get('nextPageToken')
            if page_token:
                calendar_list = service.calendarList().list(pageToken=page_token).execute()
            else:
                break

        ###########################
        #Get metadata for a calendar
        calendar = service.calendars().get(calendarId=CALENDAR).execute()
        pprint.pprint(calendar)

        ###########################
        #Get colors for a calendar
        colors = service.colors().get().execute()
        pprint.pprint(colors)
        # Print available calendarListEntry colors.
##        for id, color in colors['calendar'].iteritems():
##            print 'Calendar colorId: %s' % id
##            print '  Background: %s' % color['background']
##            print '  Foreground: %s' % color['foreground']
##        # Print available event colors.
##        for id, color in colors['event'].iteritems():
##            print 'Event    colorId: %s' % id
##            print '  Background: %s' % color['background']
##            print '  Foreground: %s' % color['foreground']

        ###########################
        #Get events in a calendar
        events = service.events().list(calendarId=CALENDAR, maxResults=5,
                                       timeMin='2012-06-01T00:00:00-08:00', q='vacation').execute()
        #pprint.pprint(events)
        print '\n'.join([entry['summary']+' : '+ str(entry['start']) for entry in events['items']]) #note that this doesn't get additional pages with 'nextPageToken'

##        while True:
##            for event in events['items']:
##                print event['summary'], event['start'].get('dateTime')
##                pass
##            page_token = events.get('nextPageToken')
##            if page_token:
##                events = service.events().list(calendarId=CALENDAR, pageToken=page_token, maxResults=5).execute()
##            else:
##                break


        ###########################
        #Create event in a calendar
        event_id = create_cal_event(service, summary='Test event', location='My home',
                         start='2012-06-15T11:00:00.000-07:00', end='2012-06-15T12:30:00.000-07:00')

        ###########################
        #Delete event in a calendar
        delete_cal_event(service, eventID=event_id, calendarID=CALENDAR)
        

    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")



def nt_book_info():
    '''Return info about each book in the new testament in the following format:
    [ (book, number_chapters, number_verses, number_words), ...]'''
    nt_data = '''Book_name  num_cha 1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23  24  25  26  27  28  num_ver num_wor
    Matt    28  25  23  17  25  48  34  29  34  38  42  30  50  58  36  39  28  27  35  30  34  46  46  39  51  46  75  66  20  1071    18345
    Mark    16  45  28  35  41  43  56  37  38  50  52  33  44  37  72  47  20* .   .   .   .   .   .   .   .   .   .   .   .   678 11304
    Luke    24  80  52  38  44  39  49  50  56  62  42  54  59  35  35  32  31  37  43  48  47  38  71  56  53  .   .   .   .   1151    19482
    John    21  51  25  36  54  47  71  53* 59* 41  42  57  50  38  31  27  33  26  40  42  31  25  .   .   .   .   .   .   .   879 15635
    Acts    28  26  47  26  37  42  15  60  40  43  48  30  25  52  28  41  40  34  28  40* 38  40  30  35  27  27  32  44  31  1006    18451
    Rom 16  32  29  31  25  21  23  25  39  33  21  36  21  14  23  33  27  .   .   .   .   .   .   .   .   .   .   .   .   433 7111
    1Cor    16  31  16  23  21  13  20  40  13  27  33  34  31  13  40  58  24  .   .   .   .   .   .   .   .   .   .   .   .   437 6829
    2Cor    13  24  17  18  18  21  18  16  24  15  18  33  21  13  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   256 4477
    Gal 6   24  21  29  31  26  18  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   149 2230
    Eph 6   23  22  21  32  33  24  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   155 2422
    Phil    4   30  30  21  23  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   104 1629
    Col 4   29  23  25  18  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   95  1582
    1Thess  5   10  20  13  18  28  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   89  1481
    2Thess  3   12  17  18  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   47  823
    1Tim    6   20  15  16  16  25  21  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   113 1591
    2Tim    4   18  26  17  22  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   83  1238
    Titus   3   16  15  15  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   46  659
    Phlm    1   25  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   25  335
    Heb 13  14  18  19  16  14  20  28  13  28  39  40  29  25  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   303 4953
    James   5   27  26  18  17  20  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   108 1742
    1Peter  5   25  25  22  19  14  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   105 1684
    2Peter  3   21  22  18  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   61  1099
    1John   5   10  29  24  21  21  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   105 2141
    2John   1   13  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   13  245
    3John   1   15  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   15  219
    Jude    1   25  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   25  461
    Rev 22  20  29  22  11  14  17  17  13  21  11  19  17  18  20  8   21  18  24  21  15  27  21  .   .   .   .   .   .   404 9852'''

    book_info = [(book, int(num_cha), int(num_ver), int(num_word))
                 for (book, num_cha,_,_,_,_,_
                        ,_,_,_,_,ten,_,_,_,_,
                        _,_,_,_,_,twenty,_,_,_
                        ,_,_,_,_,_,num_ver, num_word) in [book_line.split()
                                                          for book_line in nt_data.split('\n')[1:] ]
                 ]
    return book_info

def nt_chapters():
    chapters = [book + ' ' + str(chap)
                for (book, num_chaps, _, _) in nt_book_info()
                for chap in range(1, num_chaps+1)
                ]
    return chapters

def query_starting_chapter(all_chapters=None):
    '''Prompt the user for which chapter they are starting on and return a "chapters" list starting at that chapter
    which is suitable for use in generate_reminder_schedule()'''
    books = set([chapter.split()[0] for chapter in all_chapters])
    max_chaps = {}
    for book in books:
        max_chaps[book] = max([int(chapter.split()[1]) for chapter in all_chapters if chapter.split()[0]==book ])
    for num, book in enumerate(books):
        print book+', ',
    print ''
    in_book = raw_input('Enter the name of the book: [%s] ' % all_chapters[0].split()[0])
    if not in_book or in_book == '':
        in_book = all_chapters[0].split()[0]
    if in_book in books:
        chap = raw_input('Enter the chapter [1 - %d]' % max_chaps[in_book])
        starting_chap = in_book + ' ' + str(chap) 
        if starting_chap in all_chapters:
            return all_chapters[all_chapters.index(starting_chap):]
    return all_chapters # default return in case user's input is invalid

def generate_reminder_schedule(startdate=datetime.date.today(), enddate=datetime.date.today() + datetime.timedelta(days=90),
                               chapters=None):
    '''Return a list of tuples: [ (date, reminder_text), ...]'''
    if not chapters: chapters = nt_chapters()
    print chapters
    print 'total chapters: ', len(chapters)
    num_days = enddate - startdate
    num_days = num_days.days
    chaps_perday = len(chapters) // num_days
    tenth_fraction = int(str(((len(chapters) / float(num_days)) - chaps_perday)*10)[0])
    add_chap_freq = 10 // tenth_fraction # every add_chap_freq days, add an extra chapter
    print 'chaps_perday: ', chaps_perday, '   tenth: ', tenth_fraction, '   add_chap_freq: ', add_chap_freq
    #readto_chapters = chapters[::-1*chaps_perday][::-1] #skip by chaps_perday from back so end is always finished, then reverse
    readto_chapters = []
    n = incremental = 0
    for i in range(1, num_days+1):
        n += 1
        if n >= add_chap_freq:
            n = 0
            incremental += 1
        if (i*chaps_perday)+incremental >= len(chapters)-1:
            readto_chapters.append(chapters[-1])
            break
        readto_chapters.append(chapters[(i*chaps_perday)+incremental])
            
    oneday = datetime.timedelta(days=1)
    days = []
    for i in range(num_days):
        days.append(startdate + (oneday*i))

    print 'days: ', len(days), ' readto_chaps: ', len(readto_chapters)
    reminders = zip(days[:len(readto_chapters)], readto_chapters)

    return reminders


def main():
    try:
        service = initialize_service()
        chaps = query_starting_chapter(nt_chapters())

        reminders = generate_reminder_schedule(startdate=datetime.date.today(),
                                               enddate=datetime.date(2012, 8, 13),
                                               chapters=chaps)
        print reminders

        add_entries = True
        answer = raw_input('Confirm to add all the dates above? YES <numlimit> or [no]')
        try:
            numlimit = int(answer)
        except ValueError:
            if answer == 'YES':
                numlimit = None
            else:
                add_entries = False
        if add_entries:
            for i, (day, chapter) in enumerate(reminders):
                if numlimit and i+1 >= numlimit:
                    break
                startstring = day.isoformat()+'T22:00:00.000-07:00'
                endstring = day.isoformat()+'T22:30:00.000-07:00'
                event_id = create_cal_event(service, summary='Read thru %s'%chapter, location='',
                             start=startstring, end=endstring)

        delete_matching_cal_events(service, calendarID=CALENDAR,  q='Read thru', batchsize=20)


    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")

if __name__ == '__main__':
    main()
    #raw_input("Press Enter to close:")

