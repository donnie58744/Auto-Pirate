import feedparser, os, subprocess
from MyJson import *
from OtherLibs import OS_Checker, Formatter

class Jackett():
    def __init__(self, imdbID, mediaType, mediaName, year=None, season=None, ep=None, quality=None, endingAttr=None):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.osChecker=OS_Checker()
        self.jackettIP=self.UserData["JackettIP"]
        self.jackettAPIKEY=self.UserData["JackettAPIKEY"]
        self.imdbID=imdbID
        self.mediaType = mediaType
        self.mediaName = Formatter().formatForFolder(string=mediaName)
        self.year = year
        self.season = season
        self.ep = ep
        self.quality = quality
        self.endingAttr = endingAttr

    def createUrl(self):
        indexer=""
        cat=""
        formattedMediaName=str(self.mediaName).replace(" ","+")
        imdbIdFormatted=""
        seasonFormatted=""
        epFormatted=""
        qualityFormatted=""
        yearFormatted=""
        endingAttr=""

        # Format year for url

        if (self.quality):
            qualityFormatted=f"+{self.quality}"

        if (self.imdbID):
            imdbIdFormatted=f"&imdbid={self.imdbID}"

        if (self.year):
            yearFormatted=f"+{self.year}"

        if (self.endingAttr):
            endingAttr=f"+{self.endingAttr}"

        if (self.mediaType == 'Movie'):
            indexer="yts"
            cat="&cat=100044,100045"
            searchType='movie'
            qualityFormatted=""
            formattedMediaName=""
            yearFormatted=""
            endingAttr=""
        else:
            indexer="therarbg"
            searchType='tvsearch'
            imdbIdFormatted=""
            # Format Season and Episode For Url
            if (self.season):
                seasonFormatted=f"+{self.season}"

            if (self.ep):
                epFormatted=f"{self.ep}"

        url=f"http://{self.jackettIP}/api/v2.0/indexers/{indexer}/results/torznab/api?apikey={self.jackettAPIKEY}&t={searchType}{cat}&q={formattedMediaName}{yearFormatted}{seasonFormatted}{epFormatted}{qualityFormatted}{imdbIdFormatted}{endingAttr}"
        print(url)
        return url
    
    def getRSSInfo(self, mediaType):
        try:
            # The Feed Returns a tuple ascess like entry.ID
            NewsFeed = feedparser.parse(self.createUrl())
            if (mediaType == "Movie"):
                entry = NewsFeed.entries[1]
            else:
                entry = NewsFeed.entries[0]

            return entry
        except Exception as e:
            return ""
        
    def open(self):
        uOS=self.osChecker.WinOrMac()
        if (uOS):
            try:
                subprocess.call(('open', f'{self.UserData["JackettPath"]}'))
                return True
            except Exception:
                return False
        elif (uOS == "NOT_SUPPORTED"):
            return False
        else:
            try:
                subprocess.Popen([self.UserData['JackettPath']])
                return True
            except Exception:
                return False


"""
USAGE
test=Jackett(imdbID="", mediaType='Show', mediaName="Barry", season="S02", quality="1080p")
rssInfo=test.getRSSInfo()
print(rssInfo.link)
"""
