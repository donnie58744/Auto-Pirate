from MyJson import *
import requests,os
from requests.adapters import HTTPAdapter, Retry
from json import loads as jsonLoads
from OtherLibs import Formatter

class PlexRequest:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.plexTimer = 0
        self.plexTimeout = 15
        pass

    def getPlexRequests(self):
        try:
            if (self.plexTimer >= self.plexTimeout or self.plexTimer == 0):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
                    'Content-Type': 'application/json',
                }
                r = requests.get('https://www.quackyos.com/QuackyForum/scripts/getPlexRequestsAuto.php', headers=headers, timeout=10)
                jsonResponse = r.json()
                self.plexTimer = 0
                return jsonResponse
            self.plexTimer+=1
                
        except (requests.ReadTimeout, requests.ConnectionError):
            self.plexTimer=0
            print("Plex Request Timeout")
        except Exception as e:
            print(e)
            pass

    def createPlexRequestList(self):
        getRequests=self.getPlexRequests()
        requestsList=[]
        for request in getRequests:
            requestsList.append({'id':request['id'], 'imdbID':request['imdbID'], 'mediaName':request["mediaName"], 'mediaType':request['mediaType'], 'mediaRelease':request['mediaRelease'], 'mediaReleaseDate':request['mediaReleaseDate'], 'seasons':request['seasons'], 'status':request['status']})

        return requestsList

    def formatPlexRequests(self, data):
        formattedRequests=[]
        for request in data:
            mediaName=Formatter().formatForFolder(string=request['mediaName'])
            seasonArray=jsonLoads(request['seasons'])
            # Check if the media is not released or couldnt find it
            if (request['mediaType'] == 'Show'):
                # Loop through all seasons of show and search
                for season in seasonArray:
                    formattedRequests.append(f"{mediaName}*{season}*{request['id']}*{request['mediaType']}")
            else:
                formattedRequests.append(f"{mediaName}**{request['id']}*{request['mediaType']}")
        return formattedRequests

    def changePlexRequestStatus(self, url, mediaId, status, season=None ,release=None, date=None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':self.UserData["quackyosUsername"], 'password':self.UserData["quackyosPassword"], 'id':mediaId, 'release':release, 'status':status, 'date':date}
            s = requests.Session()
            retries = Retry(total=2,
                            backoff_factor=0.1,
                            status_forcelist=[ 500, 502, 503, 504 ])
            s.mount('https://', HTTPAdapter(max_retries=retries))
            s.post(url, data=pload, headers=headers, timeout=30)
            
        except Exception as e:
            print(e)
            pass

    def changePlexRequestReleaseDate(self, mediaId, release, date, status):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':self.UserData["quackyosUsername"], 'password':self.UserData["quackyosPassword"], 'pyUser':self.UserData["quackyosUsername"], 'pyPass':self.UserData["quackyosPassword"],'id':mediaId, 'release':release, 'date':date, 'status':status}
            r = requests.post('https://www.quackyos.com/QuackyForum/scripts/changeReleaseDate.php', data=pload, headers=headers, timeout=30)
            print(r.text)
        except Exception as e:
            print(e)
            pass

    def deleteAndNotifyPlexRequest(self, mediaId, season=None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':self.UserData["quackyosUsername"], 'password':self.UserData["quackyosPassword"], 'pyUser':self.UserData["quackyosUsername"], 'pyPass':self.UserData["quackyosPassword"],'deleteId':mediaId, 'season':season}
            r = requests.post('https://www.quackyos.com/QuackyForum/scripts/deleteAndNotify.php', data=pload, headers=headers, timeout=30)
            print(r.text)
        except Exception as e:
            print(e)
            pass
    
    def updateSeasonInfo(self, mediaId, seasonNum, data):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':self.UserData["quackyosUsername"], 'password':self.UserData["quackyosPassword"],'pyUser':self.UserData["quackyosUsername"], 'pyPass':self.UserData["quackyosPassword"], 'mediaId':mediaId, 'seasonNum':seasonNum, 'data':data}
            r = requests.post('https://www.quackyos.com/QuackyForum/scripts/updateSeasonInfo.php', data=pload, headers=headers, timeout=30)
            print(r.text)
        except Exception as e:
            print(e)
            pass
