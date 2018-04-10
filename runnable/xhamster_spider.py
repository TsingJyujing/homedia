import time
import threading
from utility.connections import MongoDBDatabase, MongoDBCollection, MongoDBConnection

from bdata.porn.xhamster import *

enter_url = 'https://m.xhamster.com/videos/sex-mit-dem-geilen-ex-8273841?from=video_related'

concurrency_num = 32
failed_time_limit = 5 * 60


class SpiderThread(threading.Thread):
    def __init__(self, db_name="spider", coll_prefix="xhamster"):
        threading.Thread.__init__(self)
        self.db_name = db_name
        self.coll_prefix = coll_prefix

    def run(self):
        with MongoDBDatabase(self.db_name) as mongoDB:
            failed_times = 0
            waitingColl = mongoDB.get_collection(self.coll_prefix + "_queue")
            runningColl = mongoDB.get_collection(self.coll_prefix + "_running")
            storageColl = mongoDB.get_collection(self.coll_prefix + "_storage")
            coll_list = (waitingColl, runningColl, storageColl)
            while True:
                if failed_times >= failed_time_limit:
                    break
                task = waitingColl.find_one_and_delete({})
                if task is None:
                    failed_times += 1
                    time.sleep(2)
                else:
                    url = task["_id"]
                    try:
                        runningColl.insert_one({"_id": url})
                        _, sp = getSoup(url)
                        relatedURLs = getRelatedVideosLink(sp)
                        if storageColl.find_one({"_id": url}, {"_id": 1}) is None:
                            doc_storage = {
                                "_id": url,
                                "title": getTitleFromSoup(sp),
                                "label": getCategories(sp),
                                "rate": getRating(sp),
                                "duration": getTime(sp),
                                "preview": getPreviewImageList(sp),
                                "preview_all": getAllPreviewImageList(sp)
                            }
                            storageColl.insert_one(doc_storage)
                            runningColl.delete_one({"_id": url})
                            print("%s done." % url)
                            for task in relatedURLs:
                                condition_doc = {"_id": task.split("?")[0]}
                                if all((coll.find_one(condition_doc, {"_id": 1}) is None for coll in coll_list)):
                                    waitingColl.insert_one(condition_doc)
                        else:
                            print("%s dumped" % url)
                        failed_times = 0
                    except:
                        print("%s download error, excepted." % url)
                        waitingColl.insert_one({"_id": url})
                        failed_times += 1


if __name__ == '__main__':
    dbName = "spider"
    collPrefix = "xhamster"

    with MongoDBConnection() as mongo:
        mongo.drop_database(dbName)

    with MongoDBCollection(dbName, collPrefix + "_queue") as coll:
        if coll.count() <= 0:
            for i in range(3):
                for url in getTopURLs(i + 1):
                    try:
                        coll.insert({"_id": url})
                    except:
                        print("Error while inserting " + url)

    thread_list = [SpiderThread(db_name=dbName, coll_prefix=collPrefix) for _ in range(concurrency_num)]
    [t.start() for t in thread_list]
    [t.join() for t in thread_list]
