import subprocess, sys, os
from sys import platform
import datetime

class LibInstaller:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        pass

    def run(self):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", self.dir_path+'/req.txt'])

class OS_Checker:
    def __init__(self):
        pass
    
    def WinOrMac(self):
        # True = Mac, False = Win
        if (platform == "linux" or platform == "linux2"):
            return "NOT_SUPPORTED"
        elif (platform == "darwin"):
            return True
        elif (platform == "win32"):
            return False
        
class Formatter:
    def __init__(self):
        pass

    def formatForFolder(self, string, andSet=None):
        out=str(string).replace(':', '').replace('?', '').replace('"','').replace('*', '').replace("'", '').replace(',','').replace('.', '').replace('!', '').replace('/','')
        if (andSet == "remove"):
            out=out.replace('&', '')
        elif (andSet == "replace"):
            out=out.replace('&', 'and')

        return out.replace('  ', ' ')

class DateLib:
    def __init__(self):
        pass

    def getDateDifference(self, startDate, endDate):
        # Format startDate Data
        startDate=str(startDate).split('-')
        startYear=int(startDate[0])
        startMonth=int(startDate[1])
        startDay=int(startDate[2])
        
        # Convert the dates to datetime objects.
        startDate = datetime.datetime(startYear, startMonth, startDay)

        if (endDate == 'today'):
            date_time = datetime.datetime.now()
            endDate=datetime.datetime(date_time.year, date_time.month, date_time.day)
        else:
            # Format endDate Data
            endDate=str(endDate).split('-')
            endYear=int(endDate[0])
            endMonth=int(endDate[1])
            endDay=int(endDate[2])
            endDate = datetime.datetime(endYear, endMonth, endDay)
            

        # Subtract the two datetime objects.
        difference = endDate - startDate

        # Get the number of days between the two dates.
        days_difference = difference.days

        return days_difference
    
    def addDays(self, date, daysToAdd):
        if (date == 'today'):
            date_time = datetime.datetime.now()
            date=datetime.datetime(date_time.year, date_time.month, date_time.day)
        else:
            date = datetime.datetime.strptime(date, "%Y-%m-%d")
        output = datetime.date.fromordinal(date.toordinal() + daysToAdd)
        return output