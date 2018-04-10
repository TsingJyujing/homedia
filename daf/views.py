# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import shutil

from django.views.decorators.csrf import csrf_exempt
from agency.xhamster import *
from config import *
from utility.connections import MongoDBDatabase, MongoDBCollection
from utility.files import filter_images
from utility.http_response import response_json, get_host, get_request_with_default
from utility.list_file_io import read_raw


# Region: get information from database/filesystem for frontend daf

@response_json
def get_images_info(request):
    """
    Query image urls by indicated index
    :param request: HTTP request
    :return: images' urls by given index
    """
    image_page_index = int(request.GET["id"])
    with MongoDBDatabase("website_pron") as mgdb:
        doc = mgdb.get_collection("images_info_ahash_weed").find_one({"_id": image_page_index})
        return doc


@response_json
def get_nearby_images(request):
    """
    Query next/last images block info by given id and keywords
    :param request:
    :return:
    """
    current_id = int(request.GET["id"])
    keywords = get_request_with_default(request, "key_words", "")
    direction = request.GET["dir"].upper() == "NEXT"
    if direction:
        query_dir_condition = {"$gt": current_id}
        sort_flip = 1
    else:
        query_dir_condition = {"$lt": current_id}
        sort_flip = -1
    with MongoDBDatabase("website_pron") as mgdb:
        query_res = mgdb.get_collection("images_info_ahash_weed").find({
            "title": {
                "$regex": "(%s)" % "|".join(keywords.split(" "))
            },
            "_id": query_dir_condition
        }).sort(
            "_id", sort_flip
        ).next()
        return query_res


@response_json
def get_novel(request):
    """
    Query image urls by indicated index
    :param request: HTTP request
    :return: images' urls by given index
    """
    novel_index = int(request.GET["id"])
    with MongoDBDatabase("website_pron") as mgdb:
        res = mgdb.get_collection("novels").find_one({"_id": {"$eq": novel_index}})
        assert res is not None
        res["novel_text"] = read_raw(local_novel_path_gen % novel_index)
        return res


@response_json
def query_novel_by_title(request):
    """
    Query novel list by title <-- generated regex
    :param request:
    :return:
    """
    query_keyword = request.GET["query"]
    block_settings = json.loads(get_request_with_default(request, "block", "[]"))
    page_size = int(get_request_with_default(request, "n", "30"))
    page_index = int(get_request_with_default(request, "p", "1"))
    assert page_size >= 1
    assert page_index >= 1
    with MongoDBDatabase("website_pron") as mgdb:
        query_res = mgdb.get_collection("novels").find({
            "title": {
                "$regex": "(%s)" % "|".join(query_keyword.split(" "))
            },
            "novel_type": {
                "$nin": block_settings
            }
        }).sort("words_count", -1).skip((page_index - 1) * page_size).limit(page_size)
        return [x for x in query_res]


@response_json
def query_novel_by_condition(request):
    """
    Query novel list by title <-- json condition
    :param request:
    :return:
    """
    query_condition = json.loads(request.GET["condition"])
    page_size = int(get_request_with_default(request, "n", "30"))
    page_index = int(get_request_with_default(request, "p", "1"))
    assert page_size >= 1
    assert page_index >= 1
    with MongoDBDatabase("website_pron") as mgdb:
        query_res = mgdb.get_collection(
            "novels"
        ).find(
            query_condition
        ).sort(
            "words_count", -1
        ).skip(
            (page_index - 1) * page_size
        ).limit(
            page_size
        )
        return [x for x in query_res]


@response_json
def query_video(requset):
    """
    Query video info by id
    :param requset:
    :return:
    """
    video_id = int(requset.GET["id"])
    with MongoDBDatabase("website_pron") as mgdb:
        return mgdb.get_collection("video_info").find({"_id": {"$eq": video_id}}).next()


@response_json
def query_images_list(request):
    """
    Query images list via title<--generated regex
    :param request:
    :return:
    """
    query_keyword = request.GET["key_words"]
    page_size = int(get_request_with_default(request, "n", "30"))
    page_index = int(get_request_with_default(request, "p", "1"))
    assert page_size >= 1
    assert page_index >= 1
    with MongoDBDatabase("website_pron") as mgdb:
        query_res = mgdb.get_collection("images_info_ahash_weed").find({
            "title": {
                "$regex": "(%s)" % "|".join(query_keyword.split(" "))
            }
        }).sort(
            "_id", -1
        ).skip(
            (page_index - 1) * page_size
        ).limit(
            page_size
        )
        return [x for x in query_res]


@response_json
def query_video_list(request):
    """
    Query video list by title <-- generated regex
    :param request:
    :return:
    """
    query_keyword = request.GET["name"]
    page_size = int(get_request_with_default(request, "n", "30"))
    page_index = int(get_request_with_default(request, "p", "1"))
    like_video = get_request_with_default(request, "like", "no")=="yes"
    if like_video:
        like_condition = {
            "$eq":True
        }
    else:
        like_condition = {
            "$ne":None
        }

    assert page_size >= 1
    assert page_index >= 1
    with MongoDBDatabase("website_pron") as mgdb:
        query_res = mgdb.get_collection("video_info").find({
            "name": {
                "$regex": "(%s)" % "|".join(query_keyword.split(" "))
            },
            "like": like_condition
        }).sort(
            "_id", -1
        ).skip(
            (page_index - 1) * page_size
        ).limit(
            page_size
        )
        return [x for x in query_res]


# Region: Operation to delete/modify database and filesystem

@csrf_exempt
@response_json
def remove_video(request):
    """
    Remove video from mongoDB and hard-drive
    :param request:
    :return:
    """
    remove_id = int(request.POST['id'])
    with MongoDBDatabase("website_pron") as mongo_conn:
        collection = mongo_conn.get_collection("video_info")
        condition = {"_id": {"$eq": remove_id}}
        cursor = collection.find(condition)
        if cursor.count() <= 0:
            raise Exception("Given id not found")
        doc = cursor.next()
        with open(trash_video_info % remove_id, "w") as fp:
            json.dump(doc, fp)
        collection.delete_one(condition)
        shutil.move(video_saving_path % remove_id, trash_video_file % remove_id)
        os.remove(shortcuts_saving_path % remove_id)
        return {"status": "success"}


@csrf_exempt
@response_json
def set_video_like(request):
    """
    Set video like or discard it
    :param request:
    :return:
    """
    video_id = int(request.POST['id'])
    is_like = request.POST["like"] == "true"
    with MongoDBDatabase("website_pron") as mongo_conn:
        collection = mongo_conn.get_collection("video_info")
        condition = {"_id": video_id}
        collection.update_one(condition, {"$set": {"like": is_like}})
        return {"status": "success"}


@csrf_exempt
@response_json
def set_images_like(request):
    """
    Set images like or discard
    :param request:
    :return:
    """
    imagelist_id = int(request.POST['id'])
    is_like = request.POST["like"] == "true"
    with MongoDBDatabase("website_pron") as mongo_conn:
        collection = mongo_conn.get_collection("images_info_ahash_weed")
        condition = {"_id": imagelist_id}
        collection.update_one(condition, {"$set": {"like": is_like}})
        return {"status": "success"}


@csrf_exempt
@response_json
def set_novel_like(request):
    """
    Set images like or discard
    :param request:
    :return:
    """
    novel_id = int(request.POST['id'])
    is_like = request.POST["like"] == "true"
    with MongoDBDatabase("website_pron") as mongo_conn:
        collection = mongo_conn.get_collection("novels")
        condition = {"_id": novel_id}
        collection.update_one(condition, {"$set": {"like": is_like}})
        return {"status": "success"}


@csrf_exempt
@response_json
def remove_novel(request):
    """
    Remove novel by given index
    :param request: HTTP request
    :return: images' urls by given index
    """
    novel_index = int(request.POST["id"])
    with MongoDBDatabase("website_pron") as mgdb:
        collection = mgdb.get_collection("novels")
        condition = {"_id": {"$eq": novel_index}}
        doc = collection.find_one(condition)
        assert doc is not None, "query failed"
        res = collection.delete_one(condition).deleted_count
        fn = local_novel_path_gen % novel_index
        shutil.move(fn, trash_novel_path_gen % doc["title"])
        if res > 0:
            return {"status": "success"}
        else:
            return {"status": "error"}


@csrf_exempt
@response_json
def remove_images(request):
    """
    Remove novel by given index
    :param request: HTTP request
    :return: images' urls by given index
    """
    images_index = int(request.POST["id"])
    with MongoDBDatabase("website_pron") as mgdb:
        collection = mgdb.get_collection("images_info_ahash_weed")
        condition = {"_id": {"$eq": images_index}}
        doc = collection.find_one(condition)
        assert doc is not None, "query failed"
        res = collection.delete_one(condition).deleted_count
        fn = local_image_list_path % {"page_index": images_index}
        target_dir = trash_image_path_gen % {"page_index": images_index}
        shutil.move(fn, target_dir)
        with open(os.path.join(target_dir, "_info.json"), "w") as fp:
            json.dump(doc, fp)
        if res > 0:
            return {"status": "success"}
        else:
            return {"status": "error"}


@csrf_exempt
@response_json
def set_xhamster_rate(req):
    url = req.POST["url"]
    if not str(url).startswith("http"):
        url = "https://m.xhamster.com/videos/" + url
    rate = int(req.POST["rate"])
    with MongoDBCollection("spider", "xhamster_storage") as coll:
        assert coll.update_one({"_id": url}, {
            "$set": {"myrate": rate}}).modified_count > 0, "modify failed, no log's 'myrate' modified."


@response_json
def get_xhamster_detail(request):
    url = request.GET["url"]
    if not str(url).startswith("http"):
        url = "https://m.xhamster.com/videos/" + url
    with MongoDBCollection("spider", "xhamster_storage") as coll:
        doc = coll.find_one({"_id": url})
        if doc is None:
            data = query_url(url)
            data.pop("related")
            coll.insert_one(data)
            return data
        else:
            return doc


@response_json
def query_xhamster_bylabel(request):
    tags = json.loads(request.GET["tags"])
    page_size = int(get_request_with_default(request, "n", "30"))
    page_index = int(get_request_with_default(request, "p", "1"))
    with MongoDBCollection("spider", "xhamster_storage") as coll:
        return [x for x in coll.find({
            "$or": [{"label": {"$regex": keyword, "$options": "i"}} for keyword in tags]
        }).skip(
            (page_index - 1) * page_size
        ).limit(
            page_size
        )]


@response_json
def query_xhamster_top_urls(request):
    return get_top_urls(int(request.GET["p"]))

@response_json
def query_xhamster_query_urls(request):
    return get_query_urls(request.GET["q"],int(request.GET["p"]))
