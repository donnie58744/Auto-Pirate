# Auto Pirate

*Grabs the list of Movie and Show PLEX Requests from the [Quacky Forums](https://quackyos.com?openWindow=QuackyForum) at [QuackyOS](https://quackyos.com). Auto Pirate uses [Jackett](https://github.com/Jackett/Jackett) to find the torrents which are then sent to [qBittorrent](https://www.qbittorrent.org/) and downloaded while using [Windscribe VPN](https://windscribe.com/); it then uploads the files to a specific location to a FTP server with no VPN.*

-----

## Table of Contents

- [Features](#features)
- [Compatibility](#compatibility)
- [Setup](#setup)
- [Run](#run)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](https://github.com/donnie58744/Auto-Pirate/blob/main/LICENSE)

### Features

- Download with a peace of mind :)
  - Auto Pirate always checks that you're using a VPN! So you don't have to worry about your ISP.

- Upload with speed!
  - Auto Pirate disables the VPN when uploading to ensure maximum upload speed!


### Compatibility

- Windows 10/11

### Setup

- #### Configure Auto Pirate Settings

  - Go ahead and fill in the `UserData.json` file with relevant information
    - **For file paths use `/` not `\`**
    - **Jackett IP must include port as well ex. 127.0.0.1:9117**

- #### Downloads

  - Download [qBittorent 4.2.2](https://sourceforge.net/projects/qbittorrent/files/qbittorrent-win32/qbittorrent-4.2.2/) *Must be this version otherwise API won't work :'(*
  - Download [Windscribe VPN](https://windscribe.com/download)
  - Download [Jackett](https://github.com/Jackett/Jackett/releases)

- #### Configure qBittorent Settings

  - ##### Tools -> Options -> Downloads

    - Turn On `Display torrent content and some options`
    - Under Saving Managment set `Default Torrent Managment Mode` to `Manual`
    - Change the `Default Save Path` to whatever you would like

  - ##### Tools -> Options -> Web UI

    - Enable `Web User Interface`
    - Set Port to `8080`
    - Enable `Bypass authentication for clients on localhost`

- #### Configure Jackett Settings

  - Click the **Green Plus** around the **Top Right** area
    - Add **YTS** and **TheRarBg** as indexers


### Run

- Make sure the **Windscribe** VPN GUI is **open**

- ```python3 main.py```

### Usage

- Add a Movie or Show via the [Quacky Forums](https://quackyos.com?openWindow=QuackyForum) **New PLEX Request**
- Watch as Auto Pirate automatically finds and starts downloading and uploading the requested media!

### Contributing

- Donovan Whysong ([Afghan Coder](https://github.com/donnie58744)) - Head Of Programming
- Thank you to these people for supporting the Quacky Server whether it be $ or parts <3
  - Erik Whysong
  - Nana

### License

- View [Here](https://github.com/donnie58744/Auto-Pirate/blob/main/LICENSE)

