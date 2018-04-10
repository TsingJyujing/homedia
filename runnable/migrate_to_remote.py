#!/bin/python
# -*- coding: utf-8 -*-
"""
将本机的数据迁移到某一台远程的服务器上
"""

import json
from utility.connections import MongoDBCollection, ExtSSHConnection
from config import *

remote_video_path = "/media/yuanyifan/ext_data/video_pool/porv_%d.mp4"
remote_video_preview_path = "/media/yuanyifan/ext_data/gif_preview/prev_%d.gif"
remote_images_path = "/media/yuanyifan/ext_data/img_pool/%08d"


def migrate_videos_to_remote():
    with MongoDBCollection("website_pron", "video_info", host="192.168.1.103") as remote_coll:
        with MongoDBCollection("website_pron", "video_info") as local_coll:
            with ExtSSHConnection("192.168.1.103", "yuanyifan", "979323") as ext_ssh:
                for doc in local_coll.find({}):
                    video_id = int(doc["_id"])
                    if remote_coll.find_one({"_id": video_id}) is None:
                        print("Found a log to migrate:\n%s" % json.dumps(doc, indent=2))
                        ext_ssh.sftp_conn.put(video_saving_path % video_id, remote_video_path % video_id)
                        ext_ssh.sftp_conn.put(shortcuts_saving_path % video_id, remote_video_preview_path % video_id)
                        remote_coll.insert_one(doc)
                        print("Migrated a log.")


def remove_remote_DAGUERRE():
    assert input("Delete all DAGUERRE?(True/False)"), "Paused"
    with MongoDBCollection("website_pron", "images_info", host="192.168.1.103") as remote_coll:
        with ExtSSHConnection("192.168.1.103", "yuanyifan", "979323") as ext_ssh:
            daguerre_ids = [int(doc["_id"]) for doc in remote_coll.find({"block": "DAGUERRE"})]
            for daguerre_id in daguerre_ids:  # 找到所有的达盖尔的旗帜
                print("Removing...%08d" % daguerre_id)
                ext_ssh.run_command('rm -rf "%s"' % (remote_images_path % daguerre_id))
                remote_coll.delete_one({"_id": daguerre_id})


def migrate_images_to_remote():
    with MongoDBCollection("website_pron", "images_info", host="192.168.1.103") as remote_coll:
        with MongoDBCollection("website_pron", "images_info") as local_coll:
            with ExtSSHConnection("192.168.1.103", "yuanyifan", "979323") as ext_ssh:
                for doc in local_coll.find({"block": "DAGUERRE"}):  # 找到所有的达盖尔的旗帜
                    image_page_index = int(doc["_id"])
                    print("Uploading...%08d" % image_page_index)
                    local_path = local_image_list_path % {
                        "page_index": image_page_index
                    }
                    remote_path = remote_images_path % image_page_index
                    ext_ssh.upload_dir(local_path, remote_path)
                    remote_coll.insert_one(doc)


if __name__ == '__main__':
    pass
