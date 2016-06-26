from __future__ import print_function
from __future__ import unicode_literals
import pprint
import datetime, calendar
import json
import google_calendar_tools

#CALENDAR = 'danny@youngshome.com'
CALENDAR = 'Ali and Daddy Scripture Calendar'

CAL_ENTRY_TAG = 'ScriptureCal'


class Scriptures(object):

    def __init__(self, fname='all_scripts_basic_info.json'):
        '''Read in data from 'all_scrips_basic_info.jsaon' 
        '''
        try:
            f = open(fname, 'r')
            self.script_info = json.loads(f.read())
            #pprint.pprint(self.script_info) #debug
            self.scriptures = [s[0]['name'] for s in self.script_info]
            self.words_per_page = int(round(266936.0/531.0)) #43: This is #words/#pages of the Book of Mormon
            self.methods = ['Chapters per day', 'Pages per day']
        except:
            print("Received exception trying to read input file")
            exit
        finally:
            f.close()

    def get_book_names(self, scripture):
        return [b[0]['name'] for s in self.script_info
                            if s[0]['name'] == scripture
                            for b in s[1]]

    def get_chapter_names(self, scripture, book):
        return [c['name'] for s in self.script_info
                            if s[0]['name'] == scripture
                            for b in s[1]
                            if b[0]['name'] == book
                            for c in b[1]]

    def prompt_user(self):
        '''return scripture and starting book/chapter and method'''
        scripture = self._prompt("Which book would you like to read?: ", self.scriptures)
        if not scripture: return
        books = self.get_book_names(scripture)
        start_book = self._prompt("Which book would you like to start in?: ", books, default=1)
        chapters = self.get_chapter_names(scripture, start_book)
        start_chapter = self._prompt("Which chapter would you like to start in?: ", chapters, default=1)
        method = self._prompt("Which method would you like to use?: ", self.methods, default=1)
        date_string = self._prompt("Enter the end date in mm/dd/yyyy format (all numbers): ", [])
        try:
            end_date = datetime.datetime.strptime(date_string, '%m/%d/%Y')
        except ValueError:
            print("Could not parse date given")
            return
        return (scripture, start_book, start_chapter, method, end_date)
        
        
    def _prompt(self, prompt_text, option_list, default=None):
        '''Prompt list and accept either number of option or the typed option itself.
        return the string of the option selected.  If given, default must be and index into option_list'''
        assert default is None or (isinstance(default, int) and default < len(option_list)+1)
        if option_list:
            self._printcolumns(option_list, 3)
        if default:
            answer = raw_input(prompt_text + '[%d] '%default)
        else:
            answer = raw_input(prompt_text)
        if not answer and option_list and default is not None:
            answer = option_list[default-1] #(default is 1-based)
        else:
            if option_list:
                try:
                    n = int(answer)
                    n -= 1 #because my prompt was 1 based, but this index needs to be zero-based
                except (TypeError, ValueError):
                    if option_list and answer not in option_list:
                            print("Invalid input")
                            return
                else:
                    if n < len(option_list):
                        answer = option_list[n]
                    else:
                        print("Invalid input")
                        return
            elif not option_list:
                pass #return answer as is if there is no option list
        return answer

    def _printcolumns(self, iterable, cols):
        printlist = [(n, txt) for n, txt in enumerate(iterable, 1)]
        print(printlist) #debug
        length_per_col = len(printlist)/cols + 1
        colstarts = [ i*length_per_col for i in range(cols) ]
        for i in range(length_per_col): #each printed row
            for j in range(len(colstarts)): #each column
                if colstarts[j]+i < len(printlist):
                    print(u'{0:<3d}: {1:<20s}'.format(printlist[colstarts[j]+i][0], printlist[colstarts[j]+i][1]), end='')
            print('')
                

    def create_cumul_percentage_list(self, scripture, start_book, start_chapter, method,):
        '''Creates a flat list of the chapters between the starting chapter and the end
        of the scripture_book.  Each entry is a tuple of (chapter_name, cumulative_percent)
        where the cumulative percent is the percent of the way from starting point to the
        end of the scripture using the 'method' which is either 'Chapters per day' or
        'Pages per day'
        '''
        all_chapters = [c for s in self.script_info
                            if s[0]['name'] == scripture
                            for b in s[1]
                            for c in b[1]]
        for index, chapter in enumerate(all_chapters):
            if chapter['name'] == start_chapter: # the chapter name includes book, so we don't need to consider book separately
                start_index = index
        relevant_chapters = all_chapters[start_index:]
        if method == 'Chapters per day':
            total_chapters = len(relevant_chapters)
            return [ (c['name'], float(num)/total_chapters) for num, c in enumerate(relevant_chapters)]
        elif method == 'Pages per day':
            cumul_words = 0
            result = []
            total_words = sum( [c['words'] for c in relevant_chapters] )
            for c in relevant_chapters:
                cumul_words += c['words']
                result.append( (c['name'], float(cumul_words)/total_words) )
            return result

    def generate_reminder_schedule(self, scripture, start_book, start_chapter,
                                   method, end_date,
                                   reminder_template='Read thru %s - '+CAL_ENTRY_TAG,
                                   start_hour=22, start_min=0):
        '''Return a list of tuples of the form (date_time, reminder_string)'''
        cumul_list = self.create_cumul_percentage_list(scripture, start_book, start_chapter, method)
        start_date = datetime.datetime.today()
        if end_date < start_date:
            print("Error: end date is prior to today")
            return
        start_date = start_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        end_date = end_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        total_timediff = end_date - start_date
        total_num_days = total_timediff.days
        reminders = []
        oneday = datetime.timedelta(days=1)
        cumul_time = 0.0
        for i in range(total_num_days):
            cumul_time += 1
            for entry in cumul_list:
                if entry[1] >= cumul_time/total_num_days:
                    reminders.append( (start_date + (i*oneday), reminder_template % entry[0]) )
                    break
        return reminders

    def main(self):
        cal = google_calendar_tools.GCal()
        add = self._prompt('Would you like to add entries? ', ['yes','no'], default=1)
        thirty_min = datetime.timedelta(minutes=30)
        if add == 'yes':
            scripture, start_book, start_chapter, method, end_date= self.prompt_user()
            schedule = self.generate_reminder_schedule(scripture, start_book, start_chapter,
                                                       method, end_date)
            
            add_entries = True
            print(schedule)
            print('')
            answer = raw_input('Confirm to add all the dates above? YES <numlimit> or [no]')
            try:
                numlimit = int(answer)
            except ValueError:
                if answer == 'YES':
                    numlimit = None
                else:
                    add_entries = False
            if add_entries:
                for i, (day, notice) in enumerate(schedule):
                    if numlimit and i+1 >= numlimit:
                        break
                    startstring = day.isoformat()
                    ending = day + thirty_min
                    endstring = ending.isoformat()
                    event_id = cal.create_cal_event(calendarId=CALENDAR, summary=notice,
                                 location='',
                                 start=startstring, end=endstring,
                                 attendee_email=CALENDAR)
        delete = self._prompt('Would you like to delete entries? ', ['yes', 'no'], default=2)

        if delete == 'yes':
            search_text = self._prompt('What calendar entry text would you like to search for? [%s]'%CAL_ENTRY_TAG, [])
            if not search_text: search_text = CAL_ENTRY_TAG
            cal.delete_matching_cal_events(calendarID=CALENDAR,  q=search_text, batchsize=20)


if __name__ == '__main__':
    s = Scriptures()
    s.main()
    #raw_input("Press Enter to close:")

