# !/bin/python
# -*- coding: utf-8 -*-
"""
Created on 2017-3-2
@author: Yuan Yi fan
"""
import os
import shutil
from io import BytesIO
import datetime
from concurrent.futures import ThreadPoolExecutor
import re
from typing import List
import numpy
import face_recognition
import threadpool
import traceback
from PIL import Image
from threading import Lock
# 如果直接执行的时候需要注意引用的库
import sys
sys.path.append("..")
from imagehash import average_hash
from pyseaweed import WeedFS
from utility.images_pool import hash_algorithm
from utility.files import get_extension
# from utility.str_util import *
from bdata.porn.caoliu import *
from utility.list_operation import list_unique
from utility.pyurllib import LiteDataDownloader, GET
from utility.connections import MongoDBCollection

insert_lock = Lock()

conn_pool_size = 32
thread_count = 16
page_to_read = 15
# 一个文件夹最少需要多少文件
files_count_limit_delete_dir = 2
# 图片文件保存的位置
# 定时运行参数
sleep_seconds = 23 * 3600  # 23Hours
# 初始化模型

download_pool = ThreadPoolExecutor(conn_pool_size)


def count_face(image_name, min_window: float = 1.2, max_window: float = 5):
    """
    Count faces in file by given parameters
    :param image_name:
    :param min_window:
    :param max_window:
    :return:
    """
    try:
        img = cv2.imread(image_name)
        return len(face_cascade.detectMultiScale(img, min_window, max_window))
    except:
        return 0


def count_face_on_weed(weed_fid, min_window: float = 1.2, max_window: float = 5):
    """
    Count faces in file by given parameters
    :param image_name:
    :param min_window:
    :param max_window:
    :return:
    """
    try:
        with BytesIO(GET("http://127.0.0.1:9301/" + weed_fid,3)) as fp:
            face_count = len(
                face_recognition.face_locations(
                    numpy.array(Image.open(fp))
                )
            )
            print("There're {} faces in image {}".format(face_count,weed_fid))
            return face_count
    except:
        print(traceback.format_exc(), file=sys.stderr)
        return 0

def count_face_in_weed(weed_fid_list: list, min_window: float = 1.2, max_window: float = 5):
    return sum((count_face_on_weed(weed_fid, min_window, max_window) for weed_fid in weed_fid_list))

def count_face_in_dir(dir_name: str , min_window: float = 1.2, max_window: float = 5):
    """
    Count faces in dir
    :param dir_name:
    :param min_window:
    :param max_window:
    :return:
    """
    return sum(
        [count_face(os.path.join(dir_name, filename), min_window, max_window) for filename in os.listdir(dir_name)])


def count_face_in_weed(weed_fids: List[str], min_window: float = 1.2, max_window: float = 5):
    """
    Count faces in dir
    :param dir_name:
    :param min_window:
    :param max_window:
    :return:
    """
    return sum(
        [count_face_on_weed(weed_fid, min_window, max_window) for weed_fid in weed_fids])


def write_face_count(coll, index, face_count):
    coll.update_one({"_id": index}, {"$set": {"face_count": face_count}})
    return true


def read_face_count(coll, index):
    return coll.find({"_id": index}).next()["face_count"]


def get_face_uncounted_index(coll):
    return [x["_id"] for x in coll.find({"face_count": None}, {"_id": 1}).sort("_id", -1)]


def count_faces():
    def weed_url_to_fid(weed_url: str) -> str:
        parts = weed_url.split("/")
        return parts[0] + "," + parts[1]

    try:
        with MongoDBCollection("website_pron", "images_info_ahash_weed") as coll:
            indexes = get_face_uncounted_index(coll)
            print("{} image lists uncounted.".format(len(indexes)))
            for i in indexes:
                try:
                    info = coll.find_one({"_id": i})
                    face = count_face_in_weed([
                        weed_url_to_fid(image_url)
                        for image_url in info["image_list"]
                    ], 1.1, 5)
                    write_face_count(coll, i, face)
                    print("There're %d faces in index=%d" % (face, i))
                except Exception as ex:
                    print("Error while counting faces in %d" % i)
                    print(traceback.format_exc(), file=sys.stderr)
    except Exception as err:
        print("Error while counting faces:\n" + traceback.format_exc(), file=sys.stderr)


def is_valid_image(filename):
    try:
        image_size = Image.open(filename).size
        assert len(image_size) >= 2
        assert image_size[0] > 240
        assert image_size[1] > 240
        return True
    except:
        return False


def get_urls(n):
    urls = []
    for i in range(n):
        current_page_url = get_latest_urls(i + 1)
        print("Obtained %d urls in page %d" % (len(current_page_url), i + 1))
        urls += current_page_url
    return list_unique(urls)


def remove_log(coll, index):
    return coll.delete_one({"_id": index}).deleted_count > 0


def is_url_existed(coll, url):
    return coll.count({"page_url": url})


def get_is_like(coll, index):
    return coll.find({"_id": index}).next()["like"]


def insert_log(coll, title, url, comment_text, image_urls, image_list):
    try:
        insert_lock.acquire()
        next_index = coll.find().sort("_id", -1).next()["_id"] + 1
        return coll.insert_one({
            "_id": next_index,
            "page_url": url.replace("http://%s/" % caoliu_host, "/"),
            "title": title,
            "block": "daguerre".upper(),
            "like": False,
            "image_urls": image_urls,
            "image_list": image_list,
            "comment": comment_text
        }).inserted_id
    finally:
        insert_lock.release()


def GET_to_weed_hash(url: str):
    try:
        image_bytes = GET(url, 6)
        with MongoDBCollection("website_pron", "image_hash_pool") as coll:
            with BytesIO(image_bytes) as bio:
                hash_info = hash_algorithm(bio)
            find_hash_in_lib = coll.find_one({"_id": hash_info})
            if find_hash_in_lib is None:
                weed_fs = WeedFS()
                weed_fid = weed_fs.upload_file(stream=image_bytes,name=url)
                find_hash_in_lib = {
                    "_id": hash_info,
                    "weed_fid": weed_fid,
                    "file_type": re.findall("\.(\w+)$", url)[0]
                }
                coll.insert_one(find_hash_in_lib)
            return find_hash_in_lib
    except:
        print("Error while get+insert image from web:\n{}\n".format(url), file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return None


def process_page_url(url):
    try:
        with MongoDBCollection("website_pron", "images_info_ahash_weed") as coll:
            if is_url_existed(coll, url.replace("http://%s/" % caoliu_host, "/")):
                raise Exception("URL is existed in db!")
            page_soup = get_soup(url)
            title = get_page_title(page_soup)
            images = get_page_images(page_soup)
            text = get_page_text(page_soup)
            # 下载小文件

            images_buffer = (
                download_pool.submit(GET_to_weed_hash, img).result()
                for img in images
            )
            page_index = insert_log(coll, title, url, text, images, [
                img_info["weed_fid"].replace(",", "/") + "/" + img_info["_id"] + "." + img_info["file_type"]
                for img_info in images_buffer if img_info is not None
            ])
            print("Downloaded: {}-->{}".format(url, page_index))

    except Exception as ex:
        if str(ex).find("URL is existed") < 0:
            print("Error while downloading..." + traceback.format_exc())


def download_image_lists(n):
    pool = threadpool.ThreadPool(thread_count)
    for i in range(n):
        try:
            urls = get_latest_urls(i + 1)
            print("Obtained %d urls in page %d" % (len(urls), i + 1))
            requests = threadpool.makeRequests(process_page_url, urls)
            [pool.putRequest(req) for req in requests]
            print("Requests appended to thread pool")
        except Exception as _:
            print("Error while appending thread pool\n" + traceback.format_exc())
    pool.wait()


def remove_empty_dir(min_file_tol: int):
    with MongoDBCollection("website_pron", "images_info_ahash_weed") as coll:
        return coll.delete_many({"$where": "this.image_list.length<{}".format(min_file_tol)}).deleted_count


def execute_one_cycle():
    print("Initialized, downloading...")
    download_image_lists(page_to_read)
    print("Downloaded, cleaning...")
    remove_empty_dir(files_count_limit_delete_dir)
    # count_faces()


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        if sys.argv[1] == "count_faces":
            count_faces()
        else:
            print("Unknown parameter: " + sys.argv[1])
    else:
        execute_one_cycle()
