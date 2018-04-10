#! python2
# -*- coding: utf-8 -*-

import shutil
import os

from config import local_image_list_path, local_images_path
from utility.connections import MongoDBCollection

try:
    prompt = raw_input
except:
    prompt = input


def remove_replication():
    """
    移除重复项，只保留最早下载的项目
    :return:
    """
    with MongoDBCollection("website_pron", "images_info") as coll:
        res = coll.aggregate([
            {
                # page_url不能为空
                "$match": {
                    "page_url": {
                        "$ne": None
                    }
                }
            },
            {
                # 按照URL计数
                "$group": {
                    "_id": {
                        "url": "$page_url"
                    },
                    "count": {
                        "$sum": 1
                    }
                }
            },
            {
                # 计数大于1的
                "$match": {
                    "count": {
                        "$gte": 2
                    }
                }
            }
        ])
        for x in res:
            url = x["_id"]["url"]
            is_first = True
            _id_list = [x["_id"] for x in coll.find({"page_url": url}, {"_id": 1}).sort("_id")]
            for _id in _id_list:
                if is_first:
                    is_first = False
                else:
                    coll.delete_one({"_id": _id})


def remove_invalid_log():
    """
    删除在数据库中没有文件夹的记录
    :return:
    """
    with MongoDBCollection("website_pron", "images_info") as coll:
        deprecated_id = [x["_id"] for x in coll.find({}, {"_id": 1}) if
                         not os.path.exists(local_image_list_path % {"page_index": x["_id"]})]
        if len(deprecated_id) > 0:
            if prompt("Delete these images:\n" + ",".join(
                    ["%d" % x for x in deprecated_id]) + "\n(y/n):").lower() == "y":
                coll.delete_many({"_id": {"$in": deprecated_id}})


def remove_invalid_dirs():
    with MongoDBCollection("website_pron", "images_info") as coll:
        id_list = {int(x) for x in os.listdir(local_images_path)}
        mg_id_list = {x["_id"] for x in coll.find({}, {"_id": 1})}
        id_dump = id_list.difference(mg_id_list)
        for _id in id_dump:
            shutil.rmtree(local_image_list_path % {"page_index": _id})


def remove_trash_images():
    """
    根据规则移除垃圾图贴{"comment":{"$regex":"at\.umeng\.com"}}
    :return:
    """
    with MongoDBCollection("website_pron", "images_info") as coll:
        return coll.delete_many({"comment": {"$regex": "at\.umeng\.com"}}).deleted_count


def main():
    remove_replication()
    remove_trash_images()
    remove_invalid_log()
    remove_invalid_dirs()


if __name__ == "__main__":
    main()
