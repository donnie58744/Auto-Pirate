from TorrentClient import TorrentClient
from json import loads as jsonLoads
from MyJson import MyJson
from OtherLibs import Formatter, DateLib
from Jackett import Jackett
from PlexRequests import PlexRequest
import re, os

class CheckAndSearch:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.PlexReq=PlexRequest()
        self.searchedRequests=[]
        self.lastRequest=[]
        self.plexSearchTimeout = 60
        self.plexSearchTimer = 0
        pass

    def Search_Add(self, request, season, quality=None, endingAtrr=None, year=None, qbClient=TorrentClient):
        print(f"Searching {Formatter().formatForFolder(string=request['mediaName'])} {season} {quality}")
        searcher=Jackett(imdbID=request['imdbID'], mediaType=request['mediaType'], mediaName=Formatter().formatForFolder(string=request["mediaName"], andSet="remove"), season=season, year=year, quality=quality, endingAttr=endingAtrr)
        rssInfo=searcher.getRSSInfo(mediaType=request['mediaType'])
        print(rssInfo.link)
        # Make rss title readable and not with .
        rssTitle = ' '.join(str(rssInfo.title).split('.'))
        rssTitle=Formatter().formatForFolder(string=str(rssTitle).lower())
        
        # Create Custom Path Using Media Name And Season
        mediaNameFormatted=Formatter().formatForFolder(string=request['mediaName'])
        mediaNameFormattedNoAnd=Formatter().formatForFolder(string=request['mediaName'], andSet="replace")
        # If media type if show then dont add season to folder path
        if (request['mediaType'] == 'Show'):
            customPath=f"{self.UserData['TorrentSaveLocation']}/{request['mediaType']}/{mediaNameFormatted} {season}/"
        else:
            customPath=f"{self.UserData['TorrentSaveLocation']}/{request['mediaType']}/{mediaNameFormatted}"
        print(customPath)
        # Make Sure torrent has media name in it
        print("-----VERIFYING-----")
        print(mediaNameFormattedNoAnd.lower())
        print(mediaNameFormatted.lower())
        print(rssTitle)
        print('--------------------')

        if (re.search(rf'\b{mediaNameFormatted.lower()}\b', rssTitle) or re.search(rf'\b{mediaNameFormattedNoAnd.lower()}\b', rssTitle)):
            # Make sure torrent isnt a whole show pack but rather a season pack only for shows!
            if (request["mediaType"]=="Show"):
                if (re.search(rf'\b{season}-\b', rssTitle) or re.search(rf'\bs01-\b', rssTitle)):
                    print("FULL SHOW!")
                    raise Exception

            qbClient.addTorrent(magnetURL=rssInfo.link, savePath=customPath, torrentName=f"{mediaNameFormatted}*{season}*{request['id']}*{request['mediaType']}")
        else:
            print("Couldnt VERIFY!")
            raise Exception

    def Check_Add(self, request, season, year, searchRequest, qbClient=TorrentClient):
        if (searchRequest not in qbClient.getTorrentList()):
            try:
                self.Search_Add(qbClient=qbClient, request=request, season=season, year=year, quality="1080P")
            except Exception:
                try:
                    self.Search_Add(qbClient=qbClient, request=request, season=season, year=year, quality="720P")
                except Exception:
                    try:
                        self.Search_Add(qbClient=qbClient, request=request, season=season, quality="1080P")
                    except Exception:
                        try:
                            self.Search_Add(qbClient=qbClient, request=request, season=season, quality="720P")
                        except Exception:
                            try:
                                self.Search_Add(qbClient=qbClient, request=request, season=season)
                            except Exception as e:
                                # Check to make sure mediaReleaseDate is within range of user selected days, if its a show let it change the date, only becuase we dont know what date of each season is
                                # Make some sort of counter so if it reaches over the limit it will set the request to couldnt find
                                if (DateLib().getDateDifference(startDate=request['mediaReleaseDate'], endDate='today') <= self.UserData['ReleaseRangeDays'] or request['mediaType'] == 'Show'):
                                    # Change Request Date and Status
                                    newDate=DateLib().addDays(date='today', daysToAdd=self.UserData['DelayedReleaseDays'])
                                    self.PlexReq.changePlexRequestReleaseDate(mediaId=request['id'], release='Not Released', date=newDate, status='Queued')
                                    print('Title May Come Out In The Future!')
                                else:
                                    # Change Request status
                                    self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', request['id'], 'Couldnt Find')
                                    print(f"!!!Search Couldnt Find {request['mediaName']} {season}!!! {e}")
        else:
            print(f"Skipping {request['mediaName']} {season}")

    def formatLastRequest(self, request):
        mediaNameFormated=Formatter().formatForFolder(string=request['mediaName'])

        return f"{mediaNameFormated}*{request['seasons']}*{request['id']}*{request['mediaType']}"

    # Check for new requests and add them to torrent client
    def searchPlexRequests(self, getRequests, qbClient=TorrentClient):
        self.plexSearchTimer +=1 
        print(self.plexSearchTimer)
        lastRequest=self.formatLastRequest(getRequests[0])
        if (self.lastRequest != lastRequest or self.plexSearchTimer >= self.plexSearchTimeout):
            self.plexSearchTimer = 0
            try:
                print("Checking Plex Requests...")
                for request in getRequests:
                    # Format media name for search
                    mediaNameFormated=Formatter().formatForFolder(string=request['mediaName'])
                    year = str(request["mediaReleaseDate"]).split('-')[0]
                    seasonArray=jsonLoads(request['seasons'])
                    mediaType=request['mediaType']
                    mediaRelease=request["mediaRelease"]
                    mediaStatus=request['status']
                    # Check if the media is not released or couldnt find it
                    if (mediaRelease != "Not Released" and mediaStatus != "Couldnt Find"):
                        if (mediaType == 'Show'):
                            # Loop through all seasons of show and search
                            for season in seasonArray:
                                searchRequest=f"{mediaNameFormated}*{season}*{request['id']}*{mediaType}"
                                # Make sure request isnt already in saved request if not check and add torrent
                                if (searchRequest not in self.searchedRequests):
                                    self.searchedRequests.append(searchRequest)
                                
                                self.Check_Add(searchRequest=searchRequest, qbClient=qbClient, request=request, season=season, year=year)
                                continue
                            
                        else:
                            searchRequest=f"{mediaNameFormated}**{request['id']}*{mediaType}"
                            # Make sure request isnt already in saved request
                            if (searchRequest not in self.searchedRequests):
                                self.searchedRequests.append(searchRequest)

                            self.Check_Add(searchRequest=searchRequest, qbClient=qbClient, request=request, season="", year=year)
                            continue
                    else:
                        print(f"Skipping {mediaNameFormated} || {mediaRelease} {mediaStatus}")
                # Set saved request
                self.lastRequest=lastRequest
                print(f'Last Request: {self.lastRequest}')
            except Exception as e:
                print(f"Request Error {e}")
        else:
            print("Requests Checked!")
