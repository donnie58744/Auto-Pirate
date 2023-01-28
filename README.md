# For Windows Only

## Code Setup
- Go into main.py and change 
    - `torrentDriveLetter` : Drive Letter To Save Torrents To 
    - `FTPip` : FTP IP To upload torrents
    - `FTPusername` : FTP username
    - `FTPPassword` : FTP Password
    - `quackyosUsername` : QuackyOs username, this checks the message boards
    - `quackyosPassword` : QuackyOs password
    - `windscribePath` : The path to Windscribe VPN ex `C:\Program Files\Windscribe`
    - `qbittorrentExe` : The exe file of qBittorent ex `C:\Program Files (x86)\qBittorrent\qbittorrent.exe`

- Go into config.json and change
    - `ip` : Change this to your ip

## Downloads:

> Download [qBittorent 4.2.2](https://sourceforge.net/projects/qbittorrent/files/qbittorrent-win32/qbittorrent-4.2.2/) *Must be this version otherwise API wont work :'(*

> Download [Windscribe VPN](https://windscribe.com/download)

## Change `qBittorent` Settings:

> Tools -> Options -> Downloads

- Turn Off `Display torrent content and some options`

- Under Saving Managment set `Default Torrent Managment Mode` to `Automatic`

- Change the `Default Save Path` to whatever you would like

> ### Tools -> Options -> Web UI

- Enable `Web User Interface`

- Set Port to `8080`

- Enable `Bypass authentication for clients on localhost`