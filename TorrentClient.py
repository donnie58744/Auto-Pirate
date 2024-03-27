import qbittorrentapi, subprocess, ftplib
from time import sleep
from MyJson import *
from FTPUpload import *
from PlexRequests import *
from VPN import *
from OtherLibs import OS_Checker, Formatter

class TorrentClient:
    def __init__(self, host=None, port=None, username=None, password=None):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.FTP_Uploader=FTPUpload()
        self.PlexReq=PlexRequest()
        self.VPN_Con=VPN()
        self.osChecker=OS_Checker()
        self.qbt_client=None
        self.host= host
        self.port = port
        self.username = username
        self.password = password
        self.torrentTimeoutCounter = 0
        self.stalledTorrents = []
        self.stalledTimeout = self.UserData["StalledTorrentTimeout"]
        self.lastDownloadProgress = 0
        self.plexRequestSendTimer = 0

    def openClient(self):
        if (self.VPN_Con.checkVPN(uploading=False)):
            uOS=self.osChecker.WinOrMac()
            if (uOS):
                try:
                    subprocess.call(('open', f'{self.UserData["QbittorrentPath"]}'))
                    return True
                except Exception:
                    return False
            elif (uOS == "NOT_SUPPORTED"):
                return False
            else:
                try:
                    subprocess.Popen(self.UserData['QbittorrentPath'])
                    return True
                except Exception:
                    return False
    
    def closeClient(self):
        if (self.qbt_client.app_shutdown()):
            return True
        else:
            return False
        
    def formatTorrentName(self, torrentName):
        try:
            torrentData = str(torrentName).split('*')
            torrentId = torrentData[2]
            torrentName = torrentData[0]
            torrentSeason = torrentData[1]
            torrentType = torrentData[3]
            
            return [torrentName,torrentSeason,torrentId,torrentType]
            
        except IndexError:
            pass

    def getTorrentList(self):
        torrentList=[]
        for torrent in self.qbt_client.torrents_info():
            formated=self.formatTorrentName(torrentName=torrent.name)
            if (formated != None):
                torrentList.append('*'.join(formated))
        return torrentList

    def connectClient(self):
        self.qbt_client = qbittorrentapi.Client(
            host=self.UserData["QbittorrentHostIP"],
            port=self.UserData["QbittorrentPort"],
            username=self.UserData["QbittorrentUsername"],
            password=self.UserData["QbittorrentPassword"],
        )

        try:
            self.qbt_client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(e)
            raise qbittorrentapi.LoginFailed

    def searchClient(self, getRequests):
        if (self.VPN_Con.checkVPN(uploading=False)):
            try:
                for torrent in self.qbt_client.torrents_info():
                    try:
                        torrentData = self.formatTorrentName(torrentName=torrent.name)
                        torrentId = torrentData[2]
                        torrentName = torrentData[0]
                        torrentSeason = torrentData[1]
                        torrentType = torrentData[3]
                        speed = round((torrent.dlspeed/1024)/1024,1)
                    except:
                        print(f"Error Wrong Formatting! {torrent.name}")
                        continue

                    """
                    Get Relative torrent data from plex requests data
                    for request in getRequests:
                        if (request['id'] == torrentId):
                            status=request['status']
                            break
                    """

                    if (torrent.state == "pausedDL"):
                        self.resumeTorrents(torrent.hash)
                    elif (torrent.state == 'metaDL' or torrent.state == 'stalledDL'):
                        self.dlStall(torrent=torrent)
                        continue
                    elif (torrent.state == 'stalledUP' or torrent.state=='uploading' or torrent.state=='forcedUP'):
                        try:
                            self.uploadTorrent(torrent=torrent)
                        except Exception as e:
                            print(e)
                        break
                    
                    # Check if torrent isnt stalled
                    if (torrent.state != 'stalledDL'):
                        if (torrent.hash in self.stalledTorrents):
                            # Check if queued or %100 downloaded
                            if (speed > self.UserData["LowSpeedTorrentMBs"] or torrent.state == 'queuedUP' or torrent.state == 'queuedDL' or torrent.state == 'pausedUP'):
                                self.stalledTorrents.remove(torrent.hash)
                                self.torrentTimeoutCounter = 0
                                print(f'Torrent Not Stalled No Mo! {torrent.name}')
                                print(self.stalledTorrents)

                    # Send Download Percent
                    if (torrent.state == 'downloading' or torrent.state == 'forcedDL'):
                        self.updatePlexDownloadPercent(torrent=torrent, torrentSpeed=speed)
                    
                    # Check if speed is low and downloading
                    if (speed < self.UserData["LowSpeedTorrentMBs"] and torrent.state == 'downloading'):
                        self.dlStall(torrent=torrent)
                        continue

                self.plexRequestSendTimer+=1

                if (self.plexRequestSendTimer >= self.UserData["PlexRequestSendTimerSeconds"]):
                    self.plexRequestSendTimer=0
            except Exception as e:
                raise e

    def updatePlexDownloadPercent(self, torrent, torrentSpeed):
        try:
            torrentData = self.formatTorrentName(torrentName=torrent.name)
            torrentId = torrentData[2]
            torrentName = torrentData[0]
            torrentSeason = torrentData[1]
            torrentType = torrentData[3]
            downloadProgress = round(torrent.progress *100)
        except:
            print(f"Error Wrong Formatting! {torrent.name}")
        try:
            # !!!MAKE A LIST WITH THE TORRENT HASH AND PROGRESS TO DETRIMINE DIFFERNT PROGESSES PER TORRENT
            self.lastDownloadProgress = downloadProgress
        except:
            pass
        # Wait about 20 seconds until next info update
        try:
            if (self.plexRequestSendTimer >= self.UserData["PlexRequestSendTimerSeconds"] or self.plexRequestSendTimer == 0):
                self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeSpeed.php', torrentId, str(torrentSpeed))
                if (torrentType == 'Movie'):
                    torrentSeason = ''
                    self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', torrentId, downloadProgress)
                else:
                    self.PlexReq.updateSeasonInfo(mediaId=torrentId, seasonNum=torrentSeason, data=downloadProgress)
                # Change Request status
                self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', torrentId, 'Downloading')
        except UnboundLocalError:
            print("No Torrent ID!")
            pass

    def finishUploadTorrent(self, torrentId, torrentSeason=None):
        # Delete Request
        self.PlexReq.deleteAndNotifyPlexRequest(mediaId=torrentId, season=torrentSeason)
        # Reset Plex Request Status
        self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', torrentId, 'Queued')

    def uploadTorrent(self, torrent):
        try:
            torrentData = self.formatTorrentName(torrentName=torrent.name)
            torrentId = torrentData[2]
            torrentName = Formatter().formatForFolder(string=torrentData[0])
            torrentSeason = torrentData[1]
            torrentType = torrentData[3]
            if (torrentType == 'Show'):
                torrentContentPath=f"{self.UserData['TorrentSaveLocation']}/{torrentType}/{torrentName} {torrentSeason}/"
            else:
                torrentContentPath=f"{self.UserData['TorrentSaveLocation']}/{torrentType}/{torrentName}/"
        except Exception as e:
            self.pauseTorrents(torrentHashes=[torrent.hash])
            raise e

        # Pause Torrent(Stop It Seeding)
        print('Pausing Torrent...')
        self.pauseTorrents(torrent.hash)
        self.closeClient()
        self.VPN_Con.windscribe(['disconnect'])
        sleep(45)

        try:
            ftp = ftplib.FTP()
            ftp.connect(host=self.UserData["FTPip"], port=self.UserData["FTPport"],timeout=60)
            print('Logging In...')
            ftp.login(self.UserData["FTPusername"], self.UserData["FTPPassword"])

            self.FTP_Uploader.uploadMedia(ftp, torrentContentPath, torrentName, torrentSeason, torrentId, 'Uploading')
            try:
                ftp.quit()
            except Exception:
                pass
            self.finishUploadTorrent(torrentId=torrentId, torrentSeason=torrentSeason)
        except Exception as e:
            if ('FTP GOT STUCK CONTINUE timed out' in str(e)):
                # this is a ok error
                self.finishUploadTorrent(torrentId=torrentId, torrentSeason=torrentSeason)
                pass
            else:
                # Upload Failed So Log It
                print(f"ERROR: Upload Failed {torrentName} {torrentSeason} {torrentId}")
                f = open(self.dir_path+'/FailedUploads.txt', 'a')
                f.write(f"\n{torrentName} {torrentSeason} || {e}")
                f.close()
                self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', torrentId, 'Upload Failed!')

    def dlStall(self, torrent):
        if (torrent.hash not in self.stalledTorrents):
            self.stalledTorrents.append(torrent.hash)

        print(f"Dl-Timeout: {self.torrentTimeoutCounter}")
        print(self.stalledTorrents)

        if (self.torrentTimeoutCounter >= self.stalledTimeout):
            self.torrentTimeoutCounter = 0
            print('Restarting Client Due To Low Speed/Stalled Torrent!')
            self.stalledTorrents=[]
            self.pauseTorrents(all=True)
            sleep(2)
            self.closeClient()
            sleep(5)
            self.VPN_Con.windscribe(['disconnect'])
            sleep(5)

        elif (self.torrentTimeoutCounter == self.stalledTimeout/2):
            self.pauseTorrents(torrentHashes=self.stalledTorrents)

        self.torrentTimeoutCounter += 1
        print(f'Low Speed/Stalled Torrent: {torrent.name}')
        sleep(1)

    def addTorrent(self, magnetURL, savePath, torrentName):
        try:
            self.qbt_client.torrents_add(urls=magnetURL, save_path=savePath, rename=torrentName, use_download_path=False)
        except Exception as e:
            print("COULDNT ADD TORRENT")
            raise e

    def pauseTorrents(self, torrentHashes=None, all=None):
        try:
            if (all):
                self.qbt_client.torrents.pause.all()
            else:
                self.qbt_client.torrents.pause(torrentHashes)
        except Exception as e:
            print("COULDNT PAUSE TORRENT")
            raise e

    def resumeTorrents(self, torrentHashes):
        try:
            self.qbt_client.torrents.resume(torrentHashes)
        except Exception as e:
            print("COULDNT RESUME TORRENT")
            raise e