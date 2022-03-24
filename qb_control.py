# qb_control.py
# Implements commands of Qbittorrent WebAPI that are necessary for the bot
# https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)


from typing import Union
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
            self._token = {sid[:3]: sid[4:]}

    def _logout(self) -> None:
        cmd = self.base_url.format("auth", "logout")
        req.get(cmd, cookies=self._token)

    def _get_default_save_path(self) -> str:
        """Get default path for saving downloads"""
        cmd = self.base_url.format("app", "defaultSavePath")
        return req.get(cmd, cookies=self._token).text

    def _get_hashdict(self) -> None:
        """
        Get dictionary mapping torrent names to their hashes
        for search purposes

        """
        cmd = self.base_url.format("torrents", "info")
        # Getting info about all torrents on the server
        torrents = req.get(cmd, cookies=self._token).json()
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

    def torrent_info(self, handle: str) -> Union[list, None]:
        """
        Returns info about a particular torrent or prints a list of torrents
        filtered by their state (all, downloaded, seeding, etc)
        """
        torrent_states = [
            '*all', '*downloaded', '*seeding', '*completed', '*paused',
            '*active', '*inactive', '*errored'
        ]
        # Assuming that the handle represents a torrent state
        if handle in torrent_states:
            handle = handle[1:]
            cmd = self.base_url.format("torrents", "info")
            r = req.get(cmd, cookies=self._token, params={'filter': handle})
            torrents = r.json()
            return [torrent['name'] for torrent in torrents]

        # Assuming that the handle represents a torrent name
        if self._search_hash(handle) is not None:
            hash = self._search_hash(handle)
            cmd = self.base_url.format("torrents", "info")
            r = req.get(cmd, cookies=self._token, params={'hashes': hash})
            torrent = r.json()[0]

            # Finally compiling data for our bot into a list
            size = hsize(torrent['size'])
            downl = hsize(torrent['downloaded'])
            progress = format(torrent['progress'] * 100, '.2f') + "%"
            dlspeed = hsize(torrent['dlspeed']) + "/s"
            compl = str(dt.fromtimestamp(torrent['completion_on']))
            seeds_leechs = f"{torrent['num_seeds']}/{torrent['num_leechs']}"
            upl = hsize(torrent['uploaded']) + "/s"
            ulspeed = hsize(torrent['upspeed'])
            tdata = [
                torrent['name'], torrent['state'], size, downl, progress,
                dlspeed, compl, seeds_leechs, upl, ulspeed
            ]
            return tdata

        return None
