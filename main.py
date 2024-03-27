#Install Libs First
from OtherLibs import LibInstaller
LibInstaller().run()

import os
from TorrentClient import TorrentClient
from time import sleep
from Jackett import Jackett
from MyJson import MyJson
from CheckAndSearch import CheckAndSearch
from PlexRequests import PlexRequest

class main:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.CheckAndSearch = CheckAndSearch()
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.PlexReq=PlexRequest()
        self.plexSearchTimer = 60
        pass

    def retryClientProcess(self, qbClient=TorrentClient):
        try:
            print('Trying to re open client...')
            qbClient.openClient()
            sleep(10)
            qbClient.connectClient()
            pass
        except Exception:
            self.retryClientProcess(qbClient=qbClient)

    # Set all requests status to Queued
    def resetPlexRequestsStatus(self):
        requestList=PlexRequest().createPlexRequestList()
        for request in requestList:
            if (request['status'] != 'Queued' and request['status'] != 'Couldnt Find'):
                self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', request['id'], 'Queued')

    def start(self):
        qbClient=TorrentClient()
        Jackett(imdbID="",mediaType="",mediaName="").open()
        qbClient.openClient()

        sleep(10)

        try:
            qbClient.connectClient()
        except Exception:
            print("Connect Client Error")
            self.retryClientProcess(qbClient=qbClient)
        
        # Reset all plex requests to Queued
        self.resetPlexRequestsStatus()

        # Main Loop
        while True:
            try:
                # Get Requests List
                requestList=PlexRequest().createPlexRequestList()
            except Exception as e:
                print(f'Get Request ERROR: {e}')
            try:
                # Do Qbittorent stuff
                qbClient.searchClient(getRequests=requestList)
                # Search For the Plex Requests
                self.CheckAndSearch.searchPlexRequests(getRequests=requestList,qbClient=qbClient)
            except Exception as e:
                print(f"Search Client Error: {e}")
                self.retryClientProcess(qbClient=qbClient)

            sleep(1)

if __name__ == "__main__":
    main().start()