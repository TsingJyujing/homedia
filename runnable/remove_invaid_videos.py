# Remove invalid videos
import os
import json
import pymongo
import shutil
from config import auto_fix_path, video_saving_path, trash_video_file
from utility.connections import MongoDBCollection

videos_path = auto_fix_path("/mnt/e/File/www/video/file")


def clean_invalid_log():
    video_id_list = [int(filename[5:-4]) for filename in os.listdir(videos_path) if filename.endswith("mp4")]
    conn = pymongo.MongoClient()
    coll = conn.get_database("website_pron").get_collection("video_info")
    condition = {"_id": {"$nin": video_id_list}}
    data = [x for x in coll.find(condition)]
    with open("backup.json", "w") as fp:
        json.dump(data, fp)
    coll.delete_many(condition)
    print("Done")


def clean_invalid_files():
    with MongoDBCollection("website_pron", "video_info") as coll:
        id_list = {x["_id"] for x in coll.find({}, {"_id": 1})}
        video_id_list = [int(filename[5:-4]) for filename in os.listdir(videos_path) if filename.endswith("mp4")]
        for id in video_id_list:
            if id not in id_list:
                shutil.move(video_saving_path % id, trash_video_file % id)


def main():
    clean_invalid_log()
    clean_invalid_files()


if __name__ == "__main__":
    main()
