import subprocess, requests, os
from MyJson import *
from time import sleep

class VPN:
    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.UserData=MyJson().jsonParser(file=self.dir_path+'/UserData.json')
        pass

    def windscribe(self, arguments):
        subprocess.check_call([self.UserData["WindscribePath"]] + arguments)
    
    def checkVPN(self, uploading):
        try:
            currentIP = requests.get('https://api.ipify.org').content.decode('utf8')
            yourIP = str(self.UserData['YourIP'])

            if (yourIP == ''):
                print('Please edit the config.json file and enter in your machines IP, Hint: run ipconfig')
                exit()
            if (uploading == False):
                if (currentIP == yourIP):
                    print('VPN OFF, Turning On Now...')
                    self.windscribe(['connect', 'best'])
                    sleep(15)
                    return True
                else:
                    return True
            else:
                return True
        except (OSError,KeyboardInterrupt) as e:
            if e.errno == 51:
                print('Network Unreachable')