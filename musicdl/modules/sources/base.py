'''
Function:
    各平台音乐下载器基类
Author:
    Charles
微信公众号:
    Charles的皮卡丘
'''
import requests
from ..utils.downloader import Downloader


'''音乐下载器基类'''
class Base():
    def __init__(self, config, logger_handle, **kwargs):
        self.source = None
        self.session = requests.Session()
        self.session.proxies.update(config['proxies'])
        self.config = config
        self.logger_handle = logger_handle

    def download_album(self, albumId):
        songInfoList = self._get_album_songs(albumId)
        self.download(songInfoList)

    '''歌曲搜索'''
    def search(self, keyword):
        raise NotImplementedError('not be implemented')
    '''歌曲下载'''
    def download(self, songinfos):
        total = len(songinfos)
        succ = 0
        for songinfo in songinfos:
            self.logger_handle.info('正在从%s下载 ——> %s - %s' % (self.source, songinfo['singers'], songinfo['songname']))
            task = Downloader(songinfo, self.session)
            if task.start():
                self.logger_handle.info('成功从%s下载到了 ——> %s - %s' % (self.source, songinfo['singers'], songinfo['songname']))
                succ += 1
            else:
                self.logger_handle.info('无法从%s下载 ——> %s - %s' % (self.source, songinfo['singers'], songinfo['songname']))
        self.logger_handle.info('下载完成 %d/%d' % (succ, total))
    '''初始化'''
    def __initialize(self):
        raise NotImplementedError('not be implemented')
    '''返回类信息'''
    def __repr__(self):
        return 'Music Source: %s' % self.source
