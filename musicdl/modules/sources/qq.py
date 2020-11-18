'''
Function:
    qq音乐下载: https://y.qq.com/
Author:
    Charles
微信公众号:
    Charles的皮卡丘
'''
import random
import requests
from .base import Base
from ..utils.misc import *
import os


'''QQ音乐下载类'''
class qq(Base):
    def __init__(self, config, logger_handle, **kwargs):
        super(qq, self).__init__(config, logger_handle, **kwargs)
        self.source = 'qq'
        self.__initialize()

    def get_albuminfo(self, albummid):
        params = {
            'albummid': albummid,
            'platform': 'mac',
            'format': 'json',
            'newsong': 1
        }
        response = self.session.get(self.album_url, headers=self.ios_headers, params=params)
        data = response.json()
        return data['data']

    def _get_album_songs(self, albummid):
        cfg = self.config.copy()
        data = self.get_albuminfo(albummid)
        album = data['getAlbumInfo']['Falbum_name']
        total = len(data['getSongInfo'])
        songinfos = []
        for item in data['getSongInfo']:
            artists = ','.join([s['name'] for s in item['singer']])
            songname = item.get('name')
            songmid = item.get('mid')
            track = item.get('index_album', 1)
            ext = ''
            download_url = ''
            filesize = 0
            duration = int(item.get('interval', 0))

            info = self.get_songinfo(songmid)
            if not info:
                self.logger_handle.info('%s 无可用下载链接： %s - %s' % (self.source, artists, songname))
                continue

            songinfo = {
                'source': self.source,
                'songid': songmid,
                'track': track,
                'total': total,
                'singers': filterBadCharacter(artists),
                'album': filterBadCharacter(album),
                'cover_url': 'https://y.gtimg.cn/music/photo_new/T002R300x300M000%s.jpg?max_age=2592000' % albummid,
                'songname': filterBadCharacter(songname),
                'savedir': os.path.join(cfg['savedir'], filterBadCharacter(artists) + ' - ' + filterBadCharacter(album)),
                'savename': '%02d-%s - %s' % (track, filterBadCharacter(artists), filterBadCharacter(songname)),
                'duration': seconds2hms(duration)
            }
            songinfo.update(info)
            songinfos.append(songinfo)
        return songinfos

        #getSongInfo
    def get_songinfo(self, songmid):
        url = 'https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg'
        params = {'songmid': songmid, 'platform': 'yqq', 'format': 'json'}
        r = self.session.get(url, headers=self.headers, params=params)
        data = r.json()
        brs = [
            ('size_320mp3', 320, 'M800', 'mp3'),
            ('size_192aac', 192, 'C600', 'm4a'),
            ('size_128mp3', 128, 'M500', 'mp3')
        ]
        p = {'req_0': {
            'module': 'vkey.GetVkeyServer',
            'method': 'CgiGetVkey',
            'param': {
                'guid': str(random.randrange(1000000000, 10000000000)),
                'songmid': [],
                'filename': [],
                'songtype': [],
                'uin': '0',
                'loginflag': 1,
                'platform': '20',
             }}}
        for vo in brs:
            p['req_0']['param']['songmid'].append(data['data'][0]['mid'])
            p['req_0']['param']['filename'].append(vo[2] + data['data'][0]['file']['media_mid'] + '.' + vo[3])
            p['req_0']['param']['songtype'].append(data['data'][0]['type'])
        r = self.session.get('https://u.y.qq.com/cgi-bin/musicu.fcg', headers=self.headers,
                params={ 'format': 'json', 'platform': 'yqq.json', 'needNewCode': 0, 'data': json.dumps(p)})
        r = r.json()

        for idx, songinfo in enumerate(r['req_0']['data']['midurlinfo']):
            if songinfo['purl']:
                download_url = r['req_0']['data']['sip'][0] + songinfo['purl']
                filesize = data['data'][0]['file'][brs[idx][0]]
                ext = brs[idx][0][-3:]

                songinfo = {
                    'download_url': download_url,
                    'filesize': str(filesize),
                    'ext': ext
                }
                return songinfo
        return None


    '''歌曲搜索'''
    def search(self, keyword):
        self.logger_handle.info('正在%s中搜索 ——> %s' % (self.source, keyword))
        cfg = self.config.copy()
        params = {
            'w': keyword,
            'format': 'json',
            'p': '1',
            'n': cfg['search_size_per_source']
        }
        response = self.session.get(self.search_url, headers=self.headers, params=params)
        all_items = response.json()['data']['song']['list']
        songinfos = []
        for item in all_items:
            artists = ','.join([s.get('name', '') for s in item.get('singer', [])])
            albumName = item.get('albumname', '-')
            songName = item.get('songname', '-')
            albummid = item.get('albummid')
            songmid = item.get('songmid')
            duration = int(item.get('interval', 0))
            ext = ''
            download_url = ''
            filesize = 0

            info = self.get_songinfo(songmid)
            if not info:
                continue

            songinfo = {
                'source': self.source,
                'songid': songmid,
                'track': item.get('cdIdx', 1),
                'total': item.get('cdIdx', 1),
                'singers': artists,
                'album': albumName,
                'cover_url': 'https://y.gtimg.cn/music/photo_new/T002R300x300M000%s.jpg?max_age=2592000' % albummid,
                'songname': songName,
                'savedir': cfg['savedir'],
                'savename': ' - '.join([filterBadCharacter(artists), filterBadCharacter(songName)]),
                'duration': seconds2hms(duration)
            }
            songinfo.update(info)
            songinfos.append(songinfo)
        return songinfos

    '''初始化'''
    def __initialize(self):
        self.ios_headers = {
                            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
                            'Referer': 'http://y.qq.com'
                        }
        self.headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
                        'Referer': 'http://y.qq.com'
                    }
        self.search_url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp'
        self.mobile_fcg_url = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg'
        self.album_url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_detail_cp.fcg'
        self.fcg_url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
