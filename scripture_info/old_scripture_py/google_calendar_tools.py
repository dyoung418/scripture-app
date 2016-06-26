from __future__ import print_function

from apiclient.discovery import build
#from apiclient.oauth import OAuthCredentials

import httplib2
import oauth2 as oauth

from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
from oauth2client.client import AccessTokenRefreshError

import logging
import pprint
import datetime, calendar
import itertools, operator

FLOW = OAuth2WebServerFlow(
    client_id='222187858874.apps.googleusercontent.com',
    client_secret='5aubG5F0dIe5yoApuVxiSRNO',
    scope='https://www.googleapis.com/auth/calendar',
    user_agent='DAY calendar app/1.0')

CALENDAR = 'danny@youngshome.com'

class GCal(object):
    '''Encapsulates methods for dealing with Google Calendars'''
    def __init__(self):
        try:
            self.service = self.initialize_service(flow=FLOW, cred_filename='calendar.dat',
                                                   service_name='calendar', version='v3')
        except AccessTokenRefreshError:
            print ("The credentials have been revoked or expired, please re-run"
                      "the application to re-authorize")
    

    def _prepare_credentials(self, flow=None, cred_filename='calendar.dat'):
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


    def _retrieve_service(self, http, service_name='calendar', version='v3'):
        """Retrieves API service via the discovery service."""

        # Construct a service object via the discovery service.
        service = build(service_name, version, http=http)
        return service


    def initialize_service(self, flow=None, cred_filename='calendar.dat', service_name='calendar', version='v3'):
        """Builds instance of service from discovery data and does auth."""

        if not flow: flow=FLOW
        # Create an httplib2.Http object to handle our HTTP requests.
        http = httplib2.Http()

        # Prepare credentials, and authorize HTTP object with them.
        credentials = self._prepare_credentials(flow=flow, cred_filename=cred_filename)
        http = credentials.authorize(http)

        # Retrieve service.
        return self._retrieve_service(http, service_name=service_name, version=version)

    def create_cal_event(self, calendarId=CALENDAR, summary='automatic calendar event', location='',
                         start='2012-06-15T10:00:00.000-07:00', end='2012-06-15T10:00:00.000-07:00',
                         attendee_email=CALENDAR,
                         colorID='1'):
        '''Create a calendar event.  Return the created event id'''
        timezone = self.calendar_timezone(calendarId)
        event = {
            'summary': summary,
            'location': location,
            'start': {
                'dateTime': start,
                'timeZone': timezone
            },
            'end': {
                'dateTime': end,
                'timeZone': timezone
            },
            'attendees': [
                {
                    'email': attendee_email
                },
            ],
            'colorId': colorID
        }
        created_event = self.service.events().insert(calendarId=calendarId, body=event).execute()
        logging.info('Created event at id: %s' % created_event['id'])
        return created_event['id']

    def delete_cal_event(self, eventID=None, calendarID=None, prompt=True):
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
                self.service.events().delete(calendarId=calendarID, eventId=eventID).execute()

    def get_matching_cal_events(self, calendarID=CALENDAR, q=None):
        '''Return a list of calendar ids which match the provided query (in 'q')'''
        assert calendarID is not None and q is not None
        results = []
        events = self.service.events().list(calendarId=calendarID, singleEvents=True, orderBy='startTime', q=q).execute()
        while True:
            if events:
                matches = events.get('items')
                if matches:
                    results += matches #events['items'] (aka matches) is a list, so add it rather than using .append()
            page_token = events.get('nextPageToken')
            if page_token:
                events = self.service.events().list(calendarId=calendarID, pageToken=page_token).execute()
            else:
                break
        return results


    def delete_matching_cal_events(self, calendarID,  q=None, batchsize=10):
        '''Delete all calendar events that match query criteria.  Will prompt to confirm'''
        matching_events = self.get_matching_cal_events(calendarID=calendarID, q=q)
        for n, event in enumerate(matching_events):
            print("{0}: {1} - {2}".format(n, event['summary'], str(event['start'])))
            #print "%d: %s - %s" % (n, event['summary'], str(event['start']))
        answer = raw_input("Delete <ALL>, <STOP>, delete <num> or skip these and show [NEXT]: ")
        try:
            del_index = int(answer)
        except ValueError:
            if answer == 'STOP':
                return
            elif answer == 'NEXT':
                pass
            elif answer == 'ALL':
                for num, e in enumerate(matching_events):
                    print("Deleting {0}: {1} - {2}".format(num, e['summary'], str(e['start'])))
                    #print "Deleting %d: %s - %s" % (num, e['summary'], str(e['start']))
                    self.service.events().delete(calendarId=calendarID,
                                        eventId=e['id']).execute()
        else:
            if del_index < len(matching_events):
                e = matching_events[del_index]
                if raw_input("Delete entry %d: %s, %s? [YES]" % (del_index, e['id'], str(e['start']))) in ['YES']:
                    self.service.events().delete(calendarId=calendarID,
                                        eventId=e['id']).execute()

    def list_calendars(self):
        results = []
        calendar_list = self.service.calendarList().list().execute()
        #print ' '.join([entry['summary'] for entry in calendar_list['items']]) #note that this doesn't get additional pages with 'nextPageToken'
        while True:
            if calendar_list:
                results += calendar_list['items']
            page_token = calendar_list.get('nextPageToken')
            if page_token:
                calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            else:
                break
        return results

    def get_calendar_metadata(self, calenderID=CALENDAR):
        calendar_metadata = self.service.calendars().get(calendarId=calenderID).execute()
        return calendar_metadata

    def calendar_timezone(self, calenderID=CALENDAR):
        return self.get_calendar_metadata()['timeZone']

    def get_calendar_colors(self, calendarID=CALENDAR):
        colors = service.colors().get().execute()
##        pprint.pprint(colors)
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
        return colors


def main():
    cal = GCal()
    pprint.pprint(cal.list_calendars())
    print('')
    pprint.pprint(cal.get_calendar_metadata())

if __name__ == '__main__':
    main()
    #raw_input("Press Enter to close:")

