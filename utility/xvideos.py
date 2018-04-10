#!/bin/python
# -*- coding: utf-8 -*-
"""
Created on 2017-3-2
@author: Yuan Yi fan
"""

import math
import shutil
import time
import pymongo
from bdata.porn.xvideos import *
from config import shortcuts_saving_path, video_saving_path
from utility import BackgroundTask
from utility.pyurllib import DownloadTask
from utility import video_processor

video_temp = "buffer/video_temp_%X.mp4"
shortcuts_temp = "buffer/shortcuts_temp_%X.gif"


class XVideoDownloadTask(BackgroundTask):
    def set_progress(self, value):
        self.progress = value

    def __init__(self, page_url, key=None):
        BackgroundTask.__init__(self, name="download video")
        if key is None:
            self.key = int(math.ceil(time.time() * 1000))
        else:
            self.key = int(key)
        self.page_url = page_url

    def run(self):
        self.progress = 0
        self.progress_info = "Started, querying page data..."
        page_data = get_data(self.page_url)

        self.progress = 10
        self.progress_info = "Got page data, analysing...."
        page_soup = BeautifulSoup(page_data, XML_DECODER)
        mp4url = get_mp4_url(page_data)
        title = get_title(page_soup)
        labels = get_keyword(page_soup)
        save_filename = video_temp % self.key

        # Common operations
        self.progress = 15
        self.progress_info = "Downloading video ..." + title
        task = DownloadTask(mp4url, save_filename, lambda value: self.set_progress(value * 0.65 + 15))
        task.start()
        task.join(timeout=3600 * 24)

        self.progress = 80
        self.progress_info = "Processing video ..."
        vcap = video_processor.get_video_cap(save_filename)
        video_basic_info = video_processor.get_video_basic_info(vcap)
        video_processor.get_video_preview(vcap, file_name=shortcuts_temp % self.key)
        vcap.release()

        self.progress = 95
        self.progress_info = "Inserting to database ..."

        video_basic_info["name"] = title
        video_basic_info["tags"] = labels
        video_basic_info["source"] = {
            "url": self.page_url,
            "type": "m.xhamster.com"
        }
        video_basic_info["like"] = False
        conn = pymongo.MongoClient()

        collection = conn.get_database("website_pron").get_collection("video_info")

        index = collection.find({}, {"_id": 1}).sort("_id", -1).next()["_id"] + 1
        video_basic_info["_id"] = index
        collection.insert_one(video_basic_info)
        conn.close()

        shutil.move(shortcuts_temp % self.key, shortcuts_saving_path % index)
        shutil.move(video_temp % self.key, video_saving_path % index)

        self.progress = 100
        self.terminated = True
