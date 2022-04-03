"""
Module qb_control\n
Implements commands of Qbittorrent WebAPI that are necessary for the bot.\n
Full API specification is available at:
https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)
"""

from typing import Generator, Union
import json
import os.path
import requests as req
from human_readable_size import human_readable_size as hsize
from datetime import datetime as dt


class QBWebAPI:
    """Class that implements main Qbittorrent WebAPI commands"""

    def __init__(self, config_path: str) -> None:
        if not os.path.exists(config_path):
            raise OSError("Configuration file not found")

        with open(config_path) as f:
            conf = json.load(f)
        self.server: str = conf["Server"]
        self.base_url = self.server + "/api/v2/{}/{}"
        self._login(conf["Username"], conf["Password"])
        self._get_hashdict()

    def __del__(self) -> None:
        """Performs logout before deleting QBWebAPI instance"""
        self._logout()
        del self

    def _login(self, username: str, password: str) -> None:
        """Performs login to the server"""
        cmd = self.base_url.format("auth", "login")
        header_dict = {"Referer": self.server}
        auth_dict = {"username": username, "password": password}

        r = req.post(cmd, headers=header_dict, data=auth_dict)
        if not r.ok:
            raise req.exceptions.ConnectionError(
                "Your IP is banned for too many failed login attempts"
            )
        elif r.ok and r.text == "Fails.":
            raise req.exceptions.ConnectionError(
                "Incorrect username or password"
            )
        elif r.ok and r.text == "Ok.":
            # Login successful, getting auth cookie
            sid = r.headers["set-cookie"].split(";")[0]
            self.__token = {sid[:3]: sid[4:]}

    def _logout(self) -> None:
        cmd = self.base_url.format("auth", "logout")
        req.get(cmd, cookies=self.__token)

    def _get_default_save_path(self) -> str:
        """Get default path for saving downloads"""
        cmd = self.base_url.format("app", "defaultSavePath")
        return req.get(cmd, cookies=self.__token).text

    def _get_hashdict(self) -> None:
        """
        Get dictionary mapping torrent names to their hashes
        for search purposes

        """
        cmd = self.base_url.format("torrents", "info")
        # Getting info about all torrents on the server
        torrents = req.get(cmd, cookies=self.__token).json()
        # Adding torrents names and hashes to a dictionary
        self.hashdict = {
            torrent["name"]: torrent["hash"] for torrent in torrents
        }

    def _search_hash(self, torrent_name: str) -> Union[str, None]:
        """Searches a torrent by its name and returns its hash"""
        i = 0
        torrent_names = list(self.hashdict.keys())
        torrent_hashes = list(self.hashdict.values())
        while True:
            try:
                if torrent_name in torrent_names[i]:
                    return torrent_hashes[i]
            except IndexError:
                return None
            i += 1

    def torrent_info(self, torrent_name: str) -> Union[list, str]:
        """
        Returns detailed info about a particular torrent
        """
        hash = self._search_hash(torrent_name)
        if hash is None:
            return "Torrent not found"
        cmd = self.base_url.format("torrents", "info")
        r = req.get(cmd, cookies=self.__token, params={'hashes': hash})
        torrent = r.json()[0]

        # Compiling data for our bot into a list
        size = hsize(torrent['size'])
        downl = hsize(torrent['downloaded'])
        progress = format(torrent['progress'] * 100, '.2f') + "%"
        dlspeed = hsize(torrent['dlspeed']) + "/s"
        compl = str(dt.fromtimestamp(torrent['completion_on']))
        seeds_leechs = f"{torrent['num_seeds']}/{torrent['num_leechs']}"
        upl = hsize(torrent['uploaded'])
        ulspeed = hsize(torrent['upspeed']) + '/s'
        tdata = [
            torrent['name'], torrent['state'], size, downl, progress,
            dlspeed, compl, seeds_leechs, upl, ulspeed
        ]
        return tdata

    def list_group(self, group: str) -> Generator[str, None, None]:
        """
        Yields torrent names filtered by their state
        (all, downloaded, seeding, etc)
        """
        groups = [
            'all', 'downloaded', 'seeding', 'completed', 'paused',
            'active', 'inactive', 'errored'
        ]
        if group not in groups:
            msg = "{}: unknown group. Available groups: {}"
            raise ValueError(msg.format(group, ', '.join(groups)))
        cmd = self.base_url.format("torrents", "info")
        r = req.get(cmd, cookies=self.__token, params={'filter': group})
        torrents = r.json()
        for torrent in torrents:
            yield torrent['name']

    def torrent_contents(self, torrent_name: str) -> Union[list, str]:
        """Show contents of a torrent"""
        if self._search_hash(torrent_name) is None:
            return "Torrent not found"
        hash = self._search_hash(torrent_name)
        cmd = self.base_url.format("torrents", "files")
        files = req.get(cmd, cookies=self.__token, params={'hash': hash})
        for file in files.json():
            progress = format(file['progress'] * 100, '.2f') + "%"
            yield [file['name'], hsize(file['size']), progress]

    def traffic_stats(self) -> list:
        """Get global transfer info (usually seen in qB status bar)"""
        cmd = self.base_url.format("transfer", "info")
        stats = req.get(cmd, cookies=self.__token).json()
        dlspeed = hsize(stats['dl_info_speed']) + "/s"
        dldata = hsize(stats['dl_info_data'])
        ulspeed = hsize(stats['up_info_speed']) + "/s"
        uldata = hsize(stats['up_info_data'])
        dht = str(stats["dht_nodes"])
        return [
            stats['connection_status'], dlspeed, dldata, ulspeed, uldata, dht
        ]

    def pause_resume(self, torrent_name=0, action="pause") -> str:
        """
        Pause/resume a torrent. If torrent_name = 0, pause/resume all torrents
        """
        if torrent_name != 0 and self._search_hash(torrent_name) is not None:
            hash = self._search_hash(torrent_name)
            cmd = self.base_url.format("torrents", action)
            req.get(cmd, cookies=self.__token, params={'hashes': hash})
            return f"Torrent {action}d"
        if torrent_name == 0:
            cmd = self.base_url.format("torrents", action)
            req.get(cmd, cookies=self.__token, params={'hashes': 'all'})
            return f"All torrents {action}d"

        return "Torrent not found"

    def delete_torrent(self, torrent_name: str, delete_files=False) -> str:
        """
        Deletes a torrent.
        If delete_files is True, also deletes downloaded files
        """
        if self._search_hash(torrent_name) is not None:
            hash = self._search_hash(torrent_name)
            cmd = self.base_url.format("torrents", "delete")
            p = {"hashes": hash, "deleteFiles": delete_files}
            req.get(cmd, cookies=self.__token, params=p)
            # Updating hashdict after torrent removal
            self._get_hashdict()
            return "Torrent deleted"

        return "Torrent not found"

    def add_torrent(self, url: str, save_path='', seq_dl=False) -> str:
        """
        Adds new torrent from url attribute
        (supported links: HTTP, HTTPS, magnet and bc://bt/).
        If save_path is empty, uses default saving path
        specified in qB settings.
        If seq_dl is True, enables sequential download of files.
        """
        # Forming data package to be uploaded in POST request
        d = {'urls': url, 'sequentialDownload': seq_dl}
        if save_path != '':
            d['savepath'] = save_path
        # Sending POST request
        cmd = self.base_url.format("torrents", "add")
        r = req.post(cmd, cookies=self.__token, data=d)
        # Analyzing response
        if r.status_code == 415:
            return "Torrent file is not valid"
        # If status_code is not 415, update hashdict
        self._get_hashdict()
        return "Torrent added successfully"
