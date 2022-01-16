# qb_control.py
# Implements commands of Qbittorrent WebAPI that are necessary for the bot
# https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)

import json
import os.path
import requests


class LoginError(requests.exceptions.RequestException):
    """Exception raised upon unsuccessful Qbittorrent login"""


class QBWebAPI:
    """Class that implements main Qbittorrent WebAPI commands"""

    def __init__(self, config_path: str) -> None:
        if os.path.exists(config_path):
            with open(config_path) as f:
                conf = json.loads(f.read())

            self.server = conf['Server']
            self._login(conf['Username'], conf['Password'])
            self._get_hashdict()

        else:
            raise OSError('Configuration file not found')

    def __del__(self) -> None:
        """Performs logout before deleting QBWebAPI instance"""
        self._logout()
        del self

    def _login(self, username: str, password: str) -> None:
        """Performs login to the server"""
        api_method = self.server + '/api/v2/auth/login'
        header_dict = {'Referer': self.server}
        auth_dict = {'username': username, 'password': password}

        r = requests.post(api_method, headers=header_dict, data=auth_dict)
        if not r.ok:
            raise requests.exceptions.HTTPError(
                'Your IP is banned for too many failed login attempts'
            )
        elif r.ok and r.text == 'Fails.':
            raise LoginError('Incorrect username or password')
        elif r.ok and r.text == 'Ok.':
            # Login successful, getting auth cookie
            sid = r.headers['set-cookie'].split(';')[0]
            self._auth_cookie = {sid[:3]: sid[4:]}

    def _logout(self) -> None:
        api_method = self.server + '/api/v2/auth/logout'
        requests.get(api_method, cookies=self._auth_cookie)

    def _get_default_save_path(self) -> str:
        """Get default path for saving downloads"""
        api_method = self.server + '/api/v2/app/defaultSavePath'
        r = requests.get(api_method, cookies=self._auth_cookie)
        return r.text

    def _get_hashdict(self) -> None:
        """
        Get dictionary mapping torrent names to their hashes
        for search purposes

        """
        api_method = self.server + '/api/v2/torrents/info'
        # Getting info about all torrents on the server
        r = requests.get(api_method, cookies=self._auth_cookie)
        torrents = r.json()
        # Adding torrents names and hashes to a dictionary
        self.hashdict = {
            torrent['name']: torrent['hash'] for torrent in torrents
        }

    def _search_hash(self, torrent_name: str):
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
