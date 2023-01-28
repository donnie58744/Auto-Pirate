import os
import socket
import subprocess
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))

subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", dir_path+'/req.txt'])

import qbittorrentapi
import rarbgapi
import json
import re
import requests
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime,timedelta
from time import sleep
import ftplib

class FtpUploadTracker:
    sizeWritten = 0
    totalSize = 0
    lastShownPercent = 0
    fileTypes = ['.mkv','.flv','.avi','.mp4','.m4v']
    
    def __init__(self, totalSize=None, mediaId=None, mediaType=None,seasonNum = None, searchFile=None, fileExtension=None):
        self.totalSize = totalSize
        self.searchFile = searchFile
        self.mediaId = mediaId
        self.mediaType = mediaType
        self.seasonNum = seasonNum
        self.fileExtension = fileExtension
    
    def handle(self, block):
        main.plexRequestSendTimer+=1
        self.sizeWritten += main.ftpBlockSize
        percentComplete = round((self.sizeWritten / self.totalSize) *100)
        
        if (self.lastShownPercent != percentComplete):
            self.lastShownPercent = percentComplete
            if (self.fileExtension not in self.fileTypes):
                main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', self.mediaId, 'Uploading '+self.seasonNum+' Subs...')
            else:
                main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', self.mediaId, 'Uploading ' + self.seasonNum)
            
            print(f"Uploading: {percentComplete}%")
            main.uploading = True
            # If the percent is over 100 then just 100 as the percent complete
            if (percentComplete >= 100):
                print(f"Uploaded {self.searchFile}")
                if (self.mediaType == 'Movies'):
                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', self.mediaId, 100)
                else:
                    main.updateSeasonInfo(mediaId=self.mediaId, seasonNum=self.seasonNum, data=100)
            else:
                if (main.plexRequestSendTimer >= 3000):
                    if (self.mediaType == 'Movies'):
                        main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', self.mediaId, percentComplete)
                    else:
                        main.updateSeasonInfo(mediaId=self.mediaId, seasonNum=self.seasonNum, data=percentComplete)
                    main.plexRequestSendTimer = 0

class CheckShowDB():
    client = rarbgapi.RarbgAPI()
    queued = []
    failed = []
    maxTimeouts = 6
    timeoutCounter = 0

    def checkIt(mediaId, imdb_ID, mediaName, releaseDate, seasons, timedOut=None):
        seasonNum = str(seasons).strip('[').strip(']').replace('"', '').split(',')
        for index, i in enumerate(seasonNum, start=1):
            # Torrent List For Highest Seeders
            torrents = [[],[],[]]
            if (mediaName+str(i)+mediaId not in main.downloadedMedia and mediaName+str(i)+mediaId not in CheckShowDB.failed):
                print(f'Searching Show DB: {mediaName} {releaseDate} {i}')
                if (CheckShowDB.timeoutCounter >= CheckShowDB.maxTimeouts and mediaName+str(i)+mediaId not in CheckShowDB.failed):
                    print('Show DB Error Skipping...')
                    CheckShowDB.timeoutCounter = 0
                    CheckShowDB.failed.append(mediaName+str(i)+mediaId)
                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', mediaId, 'Error: Couldnt Find Season And/Or Show!')
                    #FIX
                    #!!!main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', mediaId, 0)
                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeSpeed.php', mediaId, '')
                    # Add 25 Days to release date
                    #date_time_str = str(releaseDate)
                    #date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d')
                    #newDate = date_time_obj.date() + timedelta(days=25)
                    #main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeReleaseDate.php', mediaId, 'Queued', 'Not Released', newDate)
                    break
                else:
                    try:
                        year = str(releaseDate).split('-')[0]
                        
                        if (CheckShowDB.timeoutCounter >= CheckShowDB.maxTimeouts/2):
                            print('Changing Search Format...')
                            searchQuery=f'{mediaName} {i}'
                            searchRes = CheckShowDB.client.search(search_string=searchQuery, categories=[rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES, rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES_HD, rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES_UHD], extended_response=True)

                        else:
                            searchQuery=f'{imdb_ID}'
                            searchRes = CheckShowDB.client.search(search_imdb=searchQuery, categories=[rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES, rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES_HD, rarbgapi.RarbgAPI.CATEGORY_TV_EPISODES_UHD], extended_response=True)

                        print(f'Searching.... {searchQuery}')
                        for torrent in searchRes:
                            print(str(torrent))
                            
                            if (re.search(r'\b'+i+r'\b', str(torrent))):
                                torrents[0].append(mediaName)
                                torrents[1].append(torrent.seeders)
                                torrents[2].append(torrent.download)
                                print(str(torrent) + str(torrent.seeders))
                        print(torrents[1])
                        highestSeeder = torrents[1].index(max(torrents[1]))
                        highestSeederName = torrents[0][highestSeeder]
                        highestSeederURL = torrents[2][highestSeeder]
                        CheckShowDB.queued.append(str(highestSeederURL))
                        print(highestSeederURL)
                        main.torrentClient('add', highestSeederURL, 'Shows', mediaName, i,mediaId)
                        timedOut = False
                        CheckShowDB.timeoutCounter=0

                    except ValueError as e:
                        print(e)
                        CheckShowDB.timeoutCounter += 1
                        sleep(35)
                        CheckShowDB.checkIt(mediaId, imdb_ID, mediaName, releaseDate, i, True)
                    except KeyboardInterrupt:
                        exit()
                    except:
                        print('REAL: ' + str(sys.exc_info()[0]))
            else:
                print(f'Skipped {mediaName} {i} {releaseDate}')
                

class main():
    torrentDriveLetter='F:'
    plexTimer = 0
    plexTimeout = 15
    downloadedMedia = []
    torrentClientOpen = False
    uploading = False
    torrentTimeoutCounter = 0
    lastDownloadProgress = 0
    lastSpeed = 0
    stalledTorrents = []
    stalledTimeout = 120
    plexRequestSendTimer = 0
    daysToAdd=5
    ftpBlockSize=102400

    FTPip = ""
    FTPusername = ""
    FTPPassword = ""
    quackyosUsername = ""
    quackyosPassword = ""
    windscribePath = r"C:\Program Files\Windscribe"
    qbittorrentExe = r"C:\Program Files (x86)\qBittorrent\qbittorrent.exe"

    def createMagnetURL(torrentList, torrentURL):
        for i in torrentList:
            if (i["quality"] == "1080p" or i["quality"] == "720p"):
                print(f"Found {i['quality']} Torrent")
                hash = str(i["hash"])
        magnetUrl = f'magnet:?xt=urn:btih:{hash}&dn={torrentURL}&tr=http://track.one:1234/announce&tr=udp://track.two:80'
        return magnetUrl

    def getPlexRequests():
        try:
            if (main.plexTimer >= main.plexTimeout or main.plexTimer == 0):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
                }
                r = requests.post('https://www.quackyos.com/QuackyForum/scripts/getPlexRequestsAuto.php', headers=headers, timeout=10)
                jsonResponse = r.json()
                for x in jsonResponse:
                    main.checkPirateDB(x['mediaType']+'s', str(x['id']), str(x['mediaName']), x['seasons'], str(x['mediaReleaseDate']), str(x['mediaRelease']), str(x['status']), str(x['imdbID']))
                print('Downloaded Media' + str(main.downloadedMedia))
                main.plexTimer = 0
            main.plexTimer+=1
                
        except (requests.ReadTimeout, requests.ConnectionError):
            main.plexTimer=0
            print("Plex Request Timeout")
        except Exception as e:
            print(e)
            pass

    def changePlexRequestStatus(url, mediaId, status, season=None ,release=None, date=None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':main.quackyosUsername, 'password':main.quackyosPassword, 'id':mediaId, 'release':release, 'status':status, 'date':date}
            s = requests.Session()
            retries = Retry(total=2,
                            backoff_factor=0.1,
                            status_forcelist=[ 500, 502, 503, 504 ])
            s.mount('https://', HTTPAdapter(max_retries=retries))
            s.post(url, data=pload, headers=headers, timeout=30)
            
        except Exception as e:
            print(e)
            pass

    def deleteAndNotifyPlexRequest(mediaId, season=None):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':main.quackyosUsername, 'password':main.quackyosPassword, 'pyUser':main.quackyosUsername, 'pyPass':main.quackyosPassword,'deleteId':mediaId, 'season':season}
            r = requests.post('https://www.quackyos.com/QuackyForum/scripts/deleteAndNotify.php', data=pload, headers=headers, timeout=30)
            print(r.text)
        except Exception as e:
            print(e)
            pass
    
    def updateSeasonInfo(mediaId, seasonNum, data):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            }
            pload= {'username':main.quackyosUsername, 'password':main.quackyosPassword,'pyUser':main.quackyosUsername, 'pyPass':main.quackyosPassword, 'mediaId':mediaId, 'seasonNum':seasonNum, 'data':data}
            r = requests.post('https://www.quackyos.com/QuackyForum/scripts/updateSeasonInfo.php', data=pload, headers=headers, timeout=30)
            print(r.text)
        except Exception as e:
            print(e)
            pass

    def uploadMedia(ftp, fileLocation, mediaName, torrentSeason,mediaId, status, folderUpload=None, folderPath=None):
        main.uploading = True
        mediaType = fileLocation
        # FTP dont like :
        mediaName = str(mediaName).replace(':', '').replace('?', '').replace('>', '').replace('<', '').replace('/', '')
        main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeSpeed.php', mediaId, '')
        print('Uploading...')
        try:
            if ('Movies' in mediaType):
                mediaType = 'Movies'
                torrentSeason = ''
                try:
                    # Create and Enter Main Movie Folder
                    ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/')
                except Exception as e:
                    print ('Main Folder Already Exists')
                    pass
            else:
                mediaType = 'Shows'
                try:
                    # Create Main Show Folder
                    ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/')
                except Exception as e:
                    print('Main Folder Already Exsist')
                    pass

            os.chdir(fileLocation)

            # Create Main Media Folder only once
            mediaName = str(mediaName).replace(':', '')
            if (not folderUpload):
                if (mediaType == 'Shows'):
                    # Create and Enter Main Season Folder
                    try:
                        ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}')
                    except Exception as e:
                        print('Dont Worry! ' + str(e))
                        pass
                folderPath = ''

            for searchFile in os.listdir(fileLocation):
                print(f"Location: {fileLocation}")
                totalSize = os.path.getsize(f'{fileLocation}/{searchFile}')
                print('Total Size: ' + str(totalSize))
                print(f"Starting Upload: {searchFile}")
                # FTP upload
                # Read file in binary mode
                sleep(5)
                # Change Plex Request
                if (mediaType == 'Movies'):
                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', mediaId, 0)
                else:
                    print('RESET TO 0')
                    main.updateSeasonInfo(mediaId=mediaId, seasonNum=torrentSeason, data=0)
                main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', mediaId, status)
                if os.path.isfile(fileLocation + r'\{}'.format(searchFile)):
                    filename, file_extension = os.path.splitext(f'{fileLocation}/{searchFile}')
                    if (file_extension !='.jpg' and file_extension!='.srt' and file_extension !='.txt'):
                        with open(searchFile, 'rb') as fh:
                            uploadTracker = FtpUploadTracker(totalSize=int(totalSize), mediaId=mediaId, mediaType=mediaType, seasonNum=torrentSeason, searchFile=searchFile, fileExtension=file_extension)
                            print('Server Location: ' + f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/')
                            ftp.cwd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/')
                            try:
                                ftp.storbinary('STOR %s' % searchFile, fh, main.ftpBlockSize, uploadTracker.handle)
                            except Exception as e:
                                if ('[WinError 10053]' in str(e) or '[WinError 10054]' in str(e)):
                                    raise e
                                else:
                                    print(f"FTP GOT STUCK CONTINUE {e}")
                                    # Relogin to prevent reading timed out object
                                    ftp = ftplib.FTP(main.FTPip, timeout=20)
                                    ftp.login(main.FTPusername, main.FTPPassword)
                                    pass
                            fh.close()
                    else:
                        print('SKIPPED: ' + filename)
                elif (os.path.isdir(fileLocation + r'\{}'.format(searchFile)) and searchFile.lower() != 'subs'):
                    try:
                        print('Server Location: ' + f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/{searchFile}/')
                        if (folderPath):
                            ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/{searchFile}')
                        else:
                            ftp.mkd(f'{searchFile}')
                        
                        main.uploadMedia(ftp, fileLocation + r'\{}'.format(searchFile), mediaName, torrentSeason, mediaId, status, True, f'{folderPath}/{searchFile}')
                        os.chdir(fileLocation)
                    except Exception as e:
                        print(f'{e}')
                        raise e

            # Delete Request
            main.deleteAndNotifyPlexRequest(mediaId=mediaId, season=torrentSeason)
        except Exception as e:
            if ('[WinError 10053]' in str(e) or '[WinError 10054]' in str(e)):
                raise e
            else:
                print(f'277: {e}')
                sleep(5)
                print('retrying')
                # Relogin to prevent reading timed out object
                ftp = ftplib.FTP(main.FTPip, timeout=20)
                ftp.login(main.FTPusername, main.FTPPassword)
                pass

    def downloadTorrent(get, mediaId, mediaType, mediaName, seasons):
        url = get['url']
        torrents = get['torrents']

        # Open Magnet URL
        main.torrentClient('add', main.createMagnetURL(torrents,url), mediaType, mediaName, seasons,mediaId)
        print("DOWNLOADING: " + str(get['title']))

    def checkPirateDB(mediaType, mediaId, mediaName, seasons,releaseDate, mediaRelease, status,movieDB_ID):
        # Vars
        relatedMedia = []
        # Prevent random charaters like ' n shit so search works better
        mediaName = str(mediaName).replace("'", '')
        try:
            if (mediaRelease == 'Released' and status != 'Error: Couldnt Find Season And/Or Show!' and movieDB_ID != ''):
                # Check Movie DB
                if (mediaType == 'Movies'):
                    if (mediaName+mediaId not in main.downloadedMedia):
                        print(f"Searching Movie DB: {mediaName} {releaseDate}")
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
                        }
                        r = requests.get('https://yts.mx/api/v2/list_movies.json?query_term=' + movieDB_ID, headers=headers, timeout=30)
                        if (str(r) == '<Response [403]>'):
                            print('Error Searching...' + f' {mediaName} {str(movieDB_ID)}')
                        else:
                            jsonResponse = r.json()
                            jsonResponse = jsonResponse["data"]["movies"]

                            for x in jsonResponse:
                                if (x['imdb_code'] == movieDB_ID):
                                    main.downloadTorrent(x, mediaId, mediaType, mediaName, seasons)
                                    break
                                else:
                                    relatedMedia.append(x['title'])
                            else:
                                print('Couldnt Find Exact Match!, heres a list of related media.')
                                print(relatedMedia)
                    else:
                        print(f'Skipped {mediaName} {releaseDate}')
                            
                elif (mediaType == 'Shows'):
                    CheckShowDB.checkIt(mediaId, movieDB_ID, mediaName, releaseDate, seasons)

        #Cant Find Movie In DB
        except KeyError as e:
            print(f'Couldnt find {mediaName} Changing Media Release Date...')
            # Add X amount of Days to release date
            date_time_str = str(releaseDate)
            date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d')
            newDate = date_time_obj.date() + timedelta(days=main.daysToAdd)
            main.changePlexRequestStatus(url='https://www.quackyos.com/QuackyForum/scripts/changeReleaseDate.php', mediaId=mediaId, status='Queued', release='Not Released', date=newDate)

        except  requests.ReadTimeout as e:
            print('DB Request Timeout')
        except requests.ConnectionError as e:
            
            print('DB Request Timeout')
                    
    def torrentClient(request=None, url=None, mediaType=None, mediaName=None, seasons=None, mediaId=None):
        try:
            main.plexRequestSendTimer+=1
            if request == 'open':
                if (main.torrentClientOpen == False):
                    print('Opening Torrent Client...')
                    subprocess.Popen([main.qbittorrentExe])
                    main.torrentClientOpen = True
                else:
                    print('Torrent Client Already Open')
            # instantiate a Client using the appropriate WebUI configuration
            qbt_client = qbittorrentapi.Client(
                host='localhost',
                port=8080,
                username='admin',
                password='adminadmin',
            )

            # the Client will automatically acquire/maintain a logged-in state
            # in line with any request. therefore, this is not strictly necessary; 
            # however, you may want to test the provided login credentials.
            try:
                qbt_client.auth_log_in()
            except qbittorrentapi.LoginFailed as e:
                print(e)
                pass

            if (request == 'add'):
                qbt_client.torrents_add(urls=url, save_path=f"{main.torrentDriveLetter}/upload/{mediaType}/", rename=f"{mediaName}*{seasons}*{mediaId}*{mediaType}", use_download_path=False)
                if (seasons == '[]'): seasons = ''
                if (mediaName+seasons+mediaId not in main.downloadedMedia):
                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', mediaId, 'Downloading ' + seasons)
                    main.lastDownloadProgress = 0
                    main.downloadedMedia.append(mediaName+seasons+mediaId)
            elif (request == 'pause'):
                qbt_client.torrents.pause(main.stalledTorrents)
            elif (request == 'close'):
                print('Shutting Down Torrent Client')
                main.stalledTorrents = []
                main.torrentClientOpen = False
                qbt_client.app_shutdown()
            elif (request == 'makeDlList'):
                for torrent in qbt_client.torrents_info():
                    try:
                        torrentData = str(torrent.name).split('*')
                        torrentId = torrentData[2]
                        torrentName = torrentData[0]
                        torrentSeason = torrentData[1]
                        torrentType = torrentData[3]
                        
                        if (torrentSeason == '[]'):
                            torrentSeason=''

                        main.downloadedMedia.append(torrentName+torrentSeason+torrentId)
                    except IndexError:
                        print(f"Error Wrong Formatting! {torrent.name}")
                print('DL List Made! ' + str(main.downloadedMedia))

            elif (request == 'search'):
                for torrent in qbt_client.torrents_info():
                    speed = round((torrent.dlspeed/1024)/1024,1)
                    # Resume Torrent If Paused
                    if (torrent.state == 'pausedDL'):
                        if (main.checkVPN(main.uploading)):
                            print(f'Resuming: {torrent.name}')
                            qbt_client.torrents.resume(torrent.hash)
                    
                    # Restart Torrent Client On Stalled For x Seconds
                    elif (torrent.state == 'metaDL' or torrent.state == 'stalledDL'):
                        sleep(1)
                        if (torrent.hash not in main.stalledTorrents):
                            main.stalledTorrents.append(torrent.hash)
                        print(main.stalledTorrents)
                        main.torrentTimeoutCounter += 1
                        print (main.torrentTimeoutCounter)
                        if (main.torrentTimeoutCounter >= main.stalledTimeout):
                            main.torrentTimeoutCounter = 0
                            print('Restarting Client Due To Stalled Torrent')
                            main.torrentClient(request='close')
                            sleep(5)
                            main.windscribe(['disconnect'])
                        elif (main.torrentTimeoutCounter == main.stalledTimeout/2):
                            main.torrentClient(request='pause')

                    # Upload Media
                    elif (torrent.state == 'stalledUP' or torrent.state=='uploading' or torrent.state=='forcedUP'):
                        try:
                            torrentData = str(torrent.name).split('*')
                            torrentId = torrentData[2]
                            torrentName = torrentData[0]
                            torrentSeason = torrentData[1]
                            torrentType = torrentData[3]
                        except:
                            print(f"Error Wrong Formatting! {torrent.name}")
                        main.uploading = True
                        # pause all torrents
                        print('Pausing Torrent...')
                        qbt_client.torrents.pause(torrent.hash)
                        main.torrentClient(request='close')
                        main.windscribe(['disconnect'])
                        sleep(15)
                        try:
                            with ftplib.FTP(main.FTPip, timeout=30) as ftp:
                                print('Logging In...')
                                ftp.login(main.FTPusername, main.FTPPassword)
                                main.uploadMedia(ftp, torrent.content_path, torrentName, torrentSeason, torrentId, 'Uploading')
                                ftp.close()
                        except Exception as e:
                            print(f"ERROR: Upload Failed {torrentName} {torrentSeason}")
                            print(e)
                            print(dir_path+'/FailedUploads.txt')
                            f = open(dir_path+'/FailedUploads.txt', 'a')
                            f.write('\n'+str(torrentData)+':'+str(e))
                            main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', torrentId, 'Upload Failed!')
                        
                        # Torrent Finished Uploading
                        main.torrentClientOpen = False
                        CheckShowDB.failed = []
                        main.uploading = False
                        
                        # Open Back up the VPN and QBittorent
                        main.windscribe(['connect', 'best'])
                        sleep(5)
                        main.torrentClient(request='open')
                    
                    # Check if torrent is downloading and if it was stalled before
                    if (torrent.state == 'downloading' and torrent.hash in main.stalledTorrents and speed > 0.1):
                        main.stalledTorrents.remove(torrent.hash)
                        main.torrentTimeoutCounter = 0
                        print('Torrent Not Stalled No Mo!')

                    # Send Download Percent
                    if (torrent.state == 'downloading' or torrent.state == 'forcedDL'):
                        try:
                            torrentData = str(torrent.name).split('*')
                            torrentId = torrentData[2]
                            torrentName = torrentData[0]
                            torrentSeason = torrentData[1]
                            torrentType = torrentData[3]
                            downloadProgress = round(torrent.progress *100)
                        except:
                            print(f"Error Wrong Formatting! {torrent.name}")
                        try:
                            # !!!MAKE A LIST WITH THE TORRENT HASH AND PROGRESS TO DETRIMINE DIFFERNT PROGESSES PER TORRENT
                            main.lastDownloadProgress = downloadProgress
                        except:
                            pass
                        # Wait about 20 seconds until next info update
                        try:
                            if (main.plexRequestSendTimer >= 20):
                                main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeSpeed.php', torrentId, str(speed))
                                if (torrentType == 'Movies'):
                                    torrentSeason = ''
                                    main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', torrentId, downloadProgress)
                                else:
                                    main.updateSeasonInfo(mediaId=torrentId, seasonNum=torrentSeason, data=downloadProgress)
                                # Change Request status
                                main.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', torrentId, 'Downloading ' + torrentSeason)
                        except UnboundLocalError:
                            print("No Torrent ID!")
                            pass

                    if (speed < 0.1 and torrent.state == 'downloading'):
                        sleep(1)
                        main.torrentTimeoutCounter += 1
                        print(main.stalledTorrents)
                        print ('Low Speed! ' + str(main.torrentTimeoutCounter))
                        
                        if (main.torrentTimeoutCounter >= main.stalledTimeout):
                            main.torrentClient(request='pause')
                            main.torrentClient(request='close')
                            main.torrentTimeoutCounter = 0
                        elif (main.torrentTimeoutCounter == main.stalledTimeout/2):
                            main.torrentClient(request='pause')
                        if (torrent.hash not in main.stalledTorrents):
                            main.stalledTorrents.append(torrent.hash)
                            print(main.stalledTorrents)
                if (main.plexRequestSendTimer >= 20):
                    main.plexRequestSendTimer=0
                main.clearTableLock = True
        except qbittorrentapi.APIConnectionError:
            main.plexTimer=0
            main.torrentClientOpen = False
            main.torrentClient(request='open')

    def readConfig(path, key, item):
        output = []
        # Open JSON file
        f = open(dir_path+path)
        data = json.load(f)
        
        if key == '':
            return data
        elif item == '':
            return data[key]
        else:
            for i in data[key]:
                output.append(i[item])
            return output

    def windscribe(arguments):
        subprocess.check_call([main.windscribePath+r"\windscribe-cli.exe"] + arguments)
    
    def checkVPN(uploading):
        try:
            currentIP = requests.get('https://api.ipify.org').content.decode('utf8')
            getIP = str(main.readConfig('/config.json','default', 'ip')[0])

            if (getIP == 'YOUR_IP'):
                print('Please edit the config.json file and enter in your machines IP, Hint: run ipconfig')
                exit()
            if (uploading == False):
                if (currentIP == getIP):
                    
                    print('VPN OFF, Turning On Now...')
                    main.windscribe(['connect', 'best'])
                    sleep(30)
                else:
                    return True
            else:
                return True
        except (OSError,KeyboardInterrupt) as e:
            if e.errno == 51:
                
                print('Network Unreachable')


# Start

main.windscribe(['connect', 'best'])
sleep(30)
main.torrentClient(request='open')
main.torrentClient(request='makeDlList')

while True:
    sleep(1)
    if (main.checkVPN(main.uploading)):
        main.torrentClient(request='search')
        main.getPlexRequests()