#!/bin/python
# -*- coding: utf-8 -*-
"""
Created on 2017-3-2
@author: Yuan Yi fan
"""
import json
import math
import shutil
import time

import os
import traceback

import sys

from utility import video_processor

from bdata.porn.xhamster import *
from config import shortcuts_temp, video_temp, video_saving_path, shortcuts_saving_path
from utility import BackgroundTask
from utility.pyurllib import DownloadTask
from utility import connections


class xHamsterDownloadTask(BackgroundTask):
    def set_progress(self, value):
        self.progress = value

    def __init__(self, page_url, key=None):
        BackgroundTask.__init__(self, name="download video")
        if key is None:
            self.key = int(math.ceil(time.time() * 1000))
        else:
            self.key = int(key)
        self.page_url = page_url

    def run_raisable(self):
        self.progress = 0
        self.progress_info = "Started, querying page data..."
        page_data, page_soup = getSoup(self.page_url)

        self.progress = 10
        self.progress_info = "Got page data, analysing...."

        # Get video basic info from web
        mp4url = getDownloadLink(page_soup)
        title = getTitleFromSoup(page_soup)
        labels = getCategories(page_soup)
        save_filename = video_temp % self.key

        # Common operations
        self.progress = 15
        self.progress_info = "Downloading video ..." + title
        task = DownloadTask(mp4url, save_filename, lambda value: self.set_progress(value * 0.65 + 15))
        task.start()
        task.join(timeout=3600 * 24)

        self.progress = 80
        self.progress_info = "Processing video ..."

        # waiting for processing video

        video_processor.commit_task(save_filename, save_filename, timeout=3600)

        with open(save_filename + ".json", "r") as fp_read:
            video_basic_info = json.loads(fp_read.read())

        assert os.path.exists(save_filename + '.gif')

        self.progress = 95
        self.progress_info = "Inserting to database ..."

        video_basic_info["name"] = title
        video_basic_info["tags"] = labels
        video_basic_info["source"] = {
            "url": self.page_url,
            "type": "m.xhamster.com"
        }
        video_basic_info["like"] = False

        with connections.MongoDBCollection("website_pron", "video_info") as collection:
            index = collection.find({}, {"_id": 1}).sort("_id", -1).next()["_id"] + 1
            video_basic_info["_id"] = index
            collection.insert_one(video_basic_info)

        shutil.copy(save_filename + ".gif", shortcuts_saving_path % index)
        shutil.copy(video_temp % self.key, video_saving_path % index)
        try:
            os.remove(save_filename + ".gif")
            os.remove(video_temp % self.key)
        except:
            print("Warning: Exception while cleaning.")

        self.progress = 100
        self.terminated = True

    def run(self):
        try:
            self.run_raisable()
        except Exception as ex:
            print(traceback.format_exc(), file=sys.stderr)
            self.progress = 0
            self.terminated = True
