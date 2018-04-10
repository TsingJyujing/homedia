import os
import re
import shutil
import traceback
import requests
from imagehash import average_hash
from PIL import Image
from utility.connections import MongoDBDatabase
import sys
from pyseaweed import WeedFS

from config import image_pool_path, local_image_list_path

re_find_tail = re.compile("\.(\w+)$")


def hash_algorithm(file):
    return str(average_hash(Image.open(file), hash_size=10))


def insert_image_to_pool(file: str, overwrite: bool = True, remove_after_insert: bool = False, silence: bool = True):
    try:
        file_hash = hash_algorithm(file)
        target_file_name = file_hash + "." + re_find_tail.findall(file)[0]
        target_file = os.path.join(image_pool_path, target_file_name)
        if os.path.exists(target_file):
            if overwrite:
                shutil.copy(file, target_file)
                if not silence:
                    print("Warn: Hash {} existed in pool, overwritten.".format(target_file))
            else:
                if not silence:
                    print("Warn: Hash {} existed in pool, jumped.".format(target_file))
        else:
            shutil.copy(file, target_file)
            if not silence:
                print("Info: Hash {} inserted to pool.".format(target_file))
        if remove_after_insert:
            os.remove(file)
        return target_file_name
    except:
        print(traceback.format_exc(), file=sys.stderr)


def insert_image_to_weed(file: str, remove_after_insert: bool = False, silence: bool = True):
    try:
        file_hash = hash_algorithm(file)
        file_type = re_find_tail.findall(file)[0]
        with MongoDBDatabase("website_pron") as mongodb:
            coll = mongodb.get_collection("image_hash_pool")
            return_data = coll.find_one({"_id": file_hash})
            if return_data is None:
                weed_fs = WeedFS("192.168.1.103")
                file_id = weed_fs.upload_file(file)
                insert_info = {
                    "_id": file_hash,
                    "weed_fid": file_id,
                    "file_type": file_type
                }
                coll.insert_one(insert_info)
                return insert_info
            else:
                return return_data
    except:
        print(traceback.format_exc(), file=sys.stderr)
        return None


def migrate():
    with MongoDBDatabase("website_pron") as mgdb:
        source_coll = mgdb.get_collection("images_info")
        target_coll = mgdb.get_collection("images_info_ahash_weed")
        total_size = source_coll.count()
        for index, doc in enumerate(source_coll.find({})):
            print("{}/{} is prcoessing.\r".format(index, total_size))
            image_list_index = doc["_id"]
            image_dir = local_image_list_path % {"page_index": int(image_list_index)}
            hash_list = [
                hash_res["weed_fid"].replace(",", "/") + "/" + hash_res["_id"] + "." + hash_res["file_type"]
                for hash_res in (
                    insert_image_to_weed(os.path.join(image_dir, file))
                    for file in os.listdir(image_dir)
                ) if hash_res is not None
            ]
            insert_doc = doc
            insert_doc["image_list"] = hash_list
            target_coll.insert_one(insert_doc)


if __name__ == "__main__":
    migrate()
