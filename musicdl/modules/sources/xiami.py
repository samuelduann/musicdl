'''
Function:
    虾米音乐下载: https://www.xiami.com/
Author:
    Charles
微信公众号:
    Charles的皮卡丘
'''
import re
import time
import json
import requests
from .base import Base
from hashlib import md5
from ..utils.misc import *


'''虾米音乐下载类'''
class xiami(Base):
    def __init__(self, config, logger_handle, **kwargs):
        super(xiami, self).__init__(config, logger_handle, **kwargs)
        self.source = 'xiami'
        self.__initialize()

    def _get_album_songs(self, albumId):
        cfg = self.config.copy()
        songinfos = []

        token = self.__getToken()
        search_url = self.base_url.format(action=self.actions['getalbumdetail'])
        params = {'albumId': albumId}
        response = self.session.get(search_url, headers=self.headers, params=self.__xiamiSign(params, token))
        r = response.json()['data']['data']
        artistName, albumName, albumLogo = r['albumDetail']['artistName'], r['albumDetail']['albumName'], r['albumDetail']['albumLogo']
        for s in r['albumDetail']['songs']:
            songId = int(s['songId'])
            track = int(s['track'])
            songName = s['songName']
            item = {
                'source': self.source,
                'songid': songId,
                'track': track,
                'total': int(s['albumSongCount']),
                'singers': filterBadCharacter(artistName),
                'cover_url': albumLogo,
                'album': filterBadCharacter(albumName),
                'songname': filterBadCharacter(songName),
                'savedir': cfg['savedir'],
                'savedir': os.path.join(cfg['savedir'], filterBadCharacter(artistName) + ' - ' + filterBadCharacter(albumName)),
                'savename': '%02d-%s - %s' % (track, filterBadCharacter(artistName), filterBadCharacter(songName)),
                'download_url': '',
                'filesize': 0,
                'ext': 'mp3',
                'duration': 0 #seconds2hms(duration)
            }
            for fileInfo in s['listenFiles']:
                if fileInfo['format'] != 'mp3':
                    continue
                if item['filesize'] == 0 or int(fileInfo['fileSize']) > item['filesize']:
                    item['songid'] = songId
                    item['download_url'] = fileInfo['listenFile']
                    item['filesize'] = int(fileInfo['fileSize'])
                    item['duration'] = seconds2hms(int(fileInfo['length'])/1000)
            songinfos.append(item)
        return songinfos


    '''歌曲搜索'''
    def search(self, keyword):
        self.logger_handle.info('正在%s中搜索 ——> %s' % (self.source, keyword))
        cfg = self.config.copy()

        token = self.__getToken()
        search_url = self.base_url.format(action=self.actions['getalbumdetail'])
        params = {'albumId': 1}
        response = self.session.get(search_url, headers=self.headers, params=self.__xiamiSign(params, token))

        token = self.__getToken()
        search_url = self.base_url.format(action=self.actions['searchsongs'])
        params = {
                    'key': keyword,
                    'pagingVO': {'page': '1', 'pageSize': str(cfg['search_size_per_source'])}
                }
        response = self.session.get(search_url, headers=self.headers, params=self.__xiamiSign(params, token))
        all_items = response.json()['data']['data']['songs']
        songinfos = []
        # item['albumLogo']
        for item in all_items:
            download_url = ''
            filesize = 0
            for file in item['listenFiles']:
                if not file['downloadFileSize']: continue
                if file['format'] != 'mp3': continue
                _filesize = int(file['downloadFileSize'])
                if _filesize > filesize:
                    filesize = _filesize
                    download_url = file['listenFile']
                    ext = file['format']
                    duration = int(file.get('length', 0)) / 1000
            if not download_url: continue
            songinfo = {
                        'source': self.source,
                        'songid': str(item['songId']),
                        'track': 1,
                        'total': 1,
                        'singers': filterBadCharacter(item.get('artistName', '-')),
                        'album': filterBadCharacter(item.get('albumName', '-')),
                        'cover_url': item['albumLogo'],
                        'songname': filterBadCharacter(item.get('songName', '-')).split('–')[0].strip(),
                        'savedir': cfg['savedir'],
                        'savename': '%s - %s' % (filterBadCharacter(item.get('artistName', '-')), filterBadCharacter(item.get('songName', '-'))),
                        'download_url': download_url,
                        'filesize': str(filesize),
                        'ext': ext,
                        'duration': seconds2hms(duration)
                    }
            songinfos.append(songinfo)
        return songinfos
    '''虾米签名'''
    def __xiamiSign(self, params, token=''):
        appkey = '23649156'
        t = str(int(time.time() * 1000))
        request_str = {
                        'header': {'appId': '200', 'platformId': 'h5'},
                        'model': params
                    }
        data = json.dumps({'requestStr': json.dumps(request_str)})
        sign = '%s&%s&%s&%s' % (token, t, appkey, data)
        sign = md5(sign.encode('utf-8')).hexdigest()
        params = {
                    't': t,
                    'appKey': appkey,
                    'sign': sign,
                    'data': data
                }
        return params
    '''获得请求所需的token'''
    def __getToken(self):
        action = self.actions['getsongdetail']
        url = self.base_url.format(action=action)
        params = {'songId': '1'}
        response = self.session.get(url, params=self.__xiamiSign(params))
        cookies = response.cookies.get_dict()
        return cookies['_m_h5_tk'].split('_')[0]
    '''初始化'''
    def __initialize(self):
        self.headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
                        'Referer': 'http://h.xiami.com',
                        'Connection': 'keep-alive',
                        'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
                        'Accept-Encoding': 'gzip,deflate,sdch',
                        'Accept': '*/*'
                    }
        self.base_url = 'https://acs.m.xiami.com/h5/{action}/1.0/'
        self.actions = {
                        'searchsongs': 'mtop.alimusic.search.searchservice.searchsongs',
                        'getsongdetail': 'mtop.alimusic.music.songservice.getsongdetail',
                        'getalbumdetail': 'mtop.alimusic.music.albumservice.getalbumdetail',
                        'getsongs': 'mtop.alimusic.music.songservice.getsongs',
                        'getsonglyrics': 'mtop.alimusic.music.lyricservice.getsonglyrics'
                    }
