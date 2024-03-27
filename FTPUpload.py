import os
import ftplib
from MyJson import *
from PlexRequests import *
from OtherLibs import Formatter
from time import sleep

class FtpUploadTracker:
    sizeWritten = 0
    totalSize = 0
    lastShownPercent = 0
    fileTypes = ['.mkv','.flv','.avi','.mp4','.m4v']
    
    def __init__(self, totalSize=None, mediaId=None, mediaType=None,seasonNum = None, searchFile=None, fileExtension=None):
        self.PlexReq=PlexRequest()
        self.totalSize = totalSize
        self.searchFile = searchFile
        self.mediaId = mediaId
        self.mediaType = mediaType
        self.seasonNum = seasonNum
        self.fileExtension = fileExtension
        self.ftpBlockSize = FTPUpload().ftpBlockSize
        self.plexRequestSendTimer=0
    
    def handle(self, block):
        self.plexRequestSendTimer+=1
        self.sizeWritten += self.ftpBlockSize
        percentComplete = round((self.sizeWritten / self.totalSize) *100)
        
        if (self.lastShownPercent != percentComplete):
            self.lastShownPercent = percentComplete
            self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', self.mediaId, 'Uploading')
            
            print(f"Uploading: {percentComplete}%")

            # If the percent is over 100 then just 100 as the percent complete
            if (percentComplete >= 100):
                print(f"Uploaded {self.searchFile}")
                if (self.mediaType == 'Movies'):
                    self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', self.mediaId, 100)
                else:
                    self.PlexReq.updateSeasonInfo(mediaId=self.mediaId, seasonNum=self.seasonNum, data=100)
            else:
                if (self.plexRequestSendTimer >= 3000):
                    if (self.mediaType == 'Movies'):
                        self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', self.mediaId, percentComplete)
                    else:
                        self.PlexReq.updateSeasonInfo(mediaId=self.mediaId, seasonNum=self.seasonNum, data=percentComplete)
                    self.plexRequestSendTimer = 0

class FTPUpload:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        self.Formatter = Formatter()
        self.PlexReq=PlexRequest()
        self.ftpBlockSize=102400
        pass

    def uploadMedia(self, ftp, fileLocation, mediaName, torrentSeason,mediaId, status, folderUpload=None, folderPath=None):
            try:
                mediaType = fileLocation
                # FTP dont like alot of symbols so just format the media name
                mediaName = self.Formatter.formatForFolder(mediaName)
                self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeSpeed.php', mediaId, '')
                print('Uploading...')
                if ('Movie' in mediaType):
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
                        self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeDownloadProgress.php', mediaId, 0)
                    else:
                        print('RESET TO 0')
                        self.PlexReq.updateSeasonInfo(mediaId=mediaId, seasonNum=torrentSeason, data=0)
                    self.PlexReq.changePlexRequestStatus('https://www.quackyos.com/QuackyForum/scripts/changeStatus.php', mediaId, status)
                    
                    if os.path.isfile(fileLocation + r'\{}'.format(searchFile)):
                        filename, file_extension = os.path.splitext(f'{fileLocation}/{searchFile}')
                        if (file_extension !='.jpg' and file_extension!='.srt' and file_extension !='.txt'):
                            with open(searchFile, 'rb') as fh:
                                uploadTracker = FtpUploadTracker(totalSize=int(totalSize), mediaId=mediaId, mediaType=mediaType, seasonNum=torrentSeason, searchFile=searchFile, fileExtension=file_extension)
                                print('Server Location: ' + f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/')
                                try:
                                    ftp.cwd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/')
                                    ftp.storbinary('STOR %s' % searchFile, fh, self.ftpBlockSize, uploadTracker.handle)
                                except Exception as e:
                                    if ('[WinError 10053]' in str(e) or '[WinError 10054]' in str(e) or "550 Couldn't open the file or directory" in str(e) or 'cannot read from timed out object' in str(e)):
                                        raise e
                                    else:
                                        print(f"FTP GOT STUCK CONTINUE {e}")
                                        # Relogin to prevent reading timed out object
                                        ftp = ftplib.FTP()
                                        ftp.connect(host=self.UserData["FTPip"], port=self.UserData["FTPport"],timeout=20)
                                        ftp.login(self.UserData["FTPusername"], self.UserData["FTPPassword"])
                                        continue
                                fh.close()
                        else:
                            print('SKIPPED: ' + filename)
                    elif (os.path.isdir(fileLocation + r'\{}'.format(searchFile)) and searchFile.lower() != 'subs'):
                        try:
                            print('|Server Location|: ' + f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/{searchFile}/')
                            try:
                                if (folderPath):
                                    ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/{searchFile}')
                                else:
                                    ftp.mkd(f'/PLEX/{mediaType}/{mediaName}/{torrentSeason}/{folderPath}/{searchFile}')
                            except Exception as e:
                                print(e)
                                pass
                            
                            try:
                                self.uploadMedia(ftp, fileLocation + r'\{}'.format(searchFile), mediaName, torrentSeason, mediaId, status, True, f'{folderPath}/{searchFile}')
                            except Exception as e:
                                raise e

                            os.chdir(fileLocation)
                        except Exception as e:
                            print(f'{e}')
                            raise e
                        
            except Exception as e:
                if ('[WinError 10053]' in str(e) or '[WinError 10054]' in str(e)):
                    raise e
                else:
                    raise e