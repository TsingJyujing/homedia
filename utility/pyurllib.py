#!/bin/python3
# -*- coding: utf-8 -*-
"""
Created on 2017-2-3
@author: Yuan Yi fan
处理超链接以及超链接获取的BeautifulSoup类
"""
import json
import os
import string
import re
import logging
import math
import base64
import requests
from http.cookiejar import CookieJar
from config import agency_address
from bs4 import BeautifulSoup
import threading
import traceback
from utility.connections import ExtSSHConnection

try:  # Python 2.x
    import urllib2
    from  urllib import urlretrieve
except:  # Python 3.x
    from urllib import request as urllib2
    from urllib.request import urlretrieve

from utility import BackgroundTask
from config import user_agent, XML_decoder, request_timeout

urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(CookieJar())))

pac_list = ("google", "xhamster.com", "t66y.com")


def PAC_list(url: str) -> bool:
    return any((
        any((
            host.find(keyword) >= 0 for keyword in pac_list
        )) for host in re.findall("^(https://.*?/|http://.*?/)",url)
    ))


class URLReadThread(threading.Thread):
    def __init__(self, URL=""):
        super(URLReadThread, self).__init__()
        self.URL = URL
        self.data = None

    def run(self):
        self.data = urlread2(self.URL)


def get_request_head(url):
    req_header = {
        'User-Agent': user_agent,
        'Accept': '"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Host': re.findall('://.*?/', url, re.DOTALL)[0][3:-1].split(":")[0],
        "Connection": "keep-alive"
    }
    return req_header


def get_request(url):
    return urllib2.Request(
        url=url,
        data=None,
        headers=get_request_head(url)
    )


def GET(url, retry_times=1):
    exception = None
    for i in range(retry_times):
        try:
            response = requests.get(url, timeout=120)
            if response.status_code == 200:  # Successful request
                return response.content
            else:
                raise Exception("Http error:" + response.status_code)
        except:
            try:
                return urlread2_agency(url)
            except Exception as ex:
                exception = ex
    else:
        raise exception

def urlread2_agency(url:str):
    agency_url = agency_address + "/agency/get?url=%s" % base64.b64encode(url.encode("UTF-8")).decode()
    obj = json.loads(
        urllib2.urlopen(
            url=get_request(agency_url),
            timeout=request_timeout
        ).read().decode()
    )
    return base64.b64decode(obj["data"])

def urlread2(url:str):
    try:
        if PAC_list(url):
            return urlread2_agency(url)
        else:
            return urllib2.urlopen(
                get_request(url), timeout=request_timeout).read()
    except Exception as ex:
        print("Error while reading {} caused by {}".format(url, ex))
        raise ex


def get_soup(url, retry_tms=10):
    for i in range(retry_tms):
        try:
            return BeautifulSoup(urlread2(url), XML_decoder)  # html.parser
        except Exception as _:
            return BeautifulSoup("", XML_decoder)


class CreateDownloadTask(threading.Thread):
    """
    File download module
    """

    def __init__(self, src_url, dst_path):
        # type: (string, string) -> CreateDownloadTask
        threading.Thread.__init__(self)
        self.url = src_url
        self.dst = dst_path
        self.info = []

    def set_current_info(self, info):
        self.info = info

    def get_current_info(self):
        return self.info

    def run(self):
        urlretrieve(
            url=self.url,
            filename=self.dst,
            reporthook=lambda block_download_count, block_size, file_size: self.set_current_info({
                "current_percent": block_download_count * block_size * 100.0 / file_size,
                "block_download_count": block_download_count,
                "block_size": block_size,
                "file_size": file_size
            }))


class LiteFileDownloader(threading.Thread):
    """
    小文件下载线程
    """

    def __init__(self, image_url, filename):
        threading.Thread.__init__(self)
        self.image_url = image_url
        self.filename = filename
        self.done = 0

    def run(self):
        if not os.path.exists(self.filename):  # 已经下载过了
            data = urlread2(url=self.image_url)
            if data is not None:
                with open(self.filename, 'wb') as fid:
                    fid.write(data)


class LiteDataDownloader(threading.Thread):
    """
    小文件下载线程(数据缓存)
    """

    def __init__(self, image_url, tag, retry_times=1):
        threading.Thread.__init__(self)
        self.image_url = image_url
        self.data = None
        self.tag = tag
        self.retry_times = retry_times

    def run(self):
        for i in range(self.retry_times):
            try:
                self.data = urlread2(url=self.image_url)
                return
            except:
                try:
                    self.data =urlread2_agency(url=self.image_url)
                    return
                except:
                    pass

    def write_file(self, filename):
        if self.data is not None:
            with open(filename, 'wb') as fid:
                fid.write(self.data)


class BrowserDownloadTask(BackgroundTask):
    def __init__(self, url, filename, progress_callback=lambda value: None, block_size=1024 * 1024):
        BackgroundTask.__init__(self, name="download:" + filename)
        self.set_parent_progress = progress_callback
        self.target_url = url
        self.save_file = filename
        self.block_size = block_size

    def run(self):
        self.progress_info = "获取请求中..."
        logging.debug("Requiring request...")
        response = urllib2.urlopen(get_request(self.target_url), None, request_timeout)
        try:
            file_size = int(response.headers.get('content-length'))
            logging.debug("Getting file size successfully: %d bytes", file_size)
        except Exception as _:
            file_size = None
            logging.warning("Getting file size failed")
        with open(self.save_file, "wb") as fp:
            if file_size is None:
                self.progress_info = "正在下载小文件..."
                logging.debug("Downloading response file")
                self.progress = 0
                fp.write(response.read())
                self.progress = 100
            else:
                self.progress_info = "大文件下载中..."
                logging.debug("Downloading large file")
                self.progress = 0
                block_count = int(math.ceil(file_size * 1.0 / self.block_size))
                for i in range(block_count):
                    logging.debug("Downloading:%d of %d" % (i + 1, block_count))
                    fp.write(response.read(self.block_size))
                    # fp.flush() # 手动刷新
                    self.progress = (i + 1) * 100.0 / block_count

        self.terminated = True


class DownloadTask(BackgroundTask):
    def __init__(self, url, filename, progress_callback=lambda value: None):
        BackgroundTask.__init__(self, name="download:" + filename)
        self.set_parent_progress = progress_callback
        self.target_url = url
        self.save_file = filename

    def set_progress(self, value):
        self.progress = value
        self.set_parent_progress(value)

    def run(self):
        try:
            urlretrieve(
                url=self.target_url,
                filename=self.save_file,
                reporthook=lambda a, b, c: self.set_progress(a * b * 100.0 / c)
            )
        except Exception as ex:
            print(traceback.format_exc())
            print("Error in {} --> {}, use remote downloader.".format(self.target_url, self.save_file))
            RemoteDownloadTask(self.target_url, self.save_file).run()


class RemoteDownloadTask(BackgroundTask):
    def __init__(self, url, filename, progress_callback=lambda value: None):
        self.filename = filename
        self.save_file = url.split("/")[-1].split("?")[0]
        BackgroundTask.__init__(self, name="download:" + self.save_file)
        self.set_parent_progress = progress_callback
        self.target_url = url

    def set_progress(self, value):
        self.progress = value
        self.set_parent_progress(value)

    def run(self):
        with ExtSSHConnection(host="173.199.71.121", user="root", passwd="979323846") as ext_ssh:
            self.progress = 10
            command = 'wget "%s" -O "/root/download/%s"' % (self.target_url, self.save_file)
            ext_ssh.run_command(command)
            self.progress = 35
            ext_ssh.sftp_conn.get(
                "/root/download/%s" % self.save_file,
                self.filename,
                callback=lambda x, y: 60.0 * x / y + 35.0)
            self.progress = 95
            ext_ssh.sftp_conn.remove("/root/download/%s" % self.save_file)
            self.progress = 100
