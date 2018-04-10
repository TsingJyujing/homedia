import sys
import time
import threading
import traceback

sys.path.append("..")

from agency.xhamster import *
from utility.connections import MongoDBDatabase, MongoDBCollection
from utility.debug_tool import LastOpMonitor

concurrency_num = 28
failed_time_limit = 100


exception_keys = ("HTTP Error 423", "HTTP Error 410")


def deleted_error(exception):
    for key in exception_keys:
        if str(exception).find(key) >= 0:
            return True
    else:
        return False


class SpiderThread(threading.Thread):
    def __init__(self, db_name="spider", coll_prefix="xhamster"):
        threading.Thread.__init__(self)
        self.db_name = db_name
        self.coll_prefix = coll_prefix
        self.last_op = "Uninited."

    @property
    def last_op(self):
        return self._last_op

    @last_op.setter
    def last_op(self, value):
        self._last_op = value + "%f" % time.time()

    def run(self):
        try:
            self.main()
        except:
            print("Thread exited abnormally:",file=sys.stderr)
            print("Stack Trace:\n" + traceback.format_exc(), file=sys.stderr)

    def main(self):
        self.last_op = "Initialized."
        with MongoDBDatabase(self.db_name) as mongoDB:
            failed_times = 0
            waitingColl = mongoDB.get_collection(self.coll_prefix + "_queue")
            runningColl = mongoDB.get_collection(self.coll_prefix + "_running")
            deletedColl = mongoDB.get_collection(self.coll_prefix + "_deleted")
            storageColl = mongoDB.get_collection(self.coll_prefix + "_storage")
            coll_list = (waitingColl, deletedColl, runningColl, storageColl)
            while True:
                if failed_times >= failed_time_limit:
                    print("Failed too much, ended: " + self.name)
                    break
                task = waitingColl.find_one_and_delete({})
                self.last_op = "Got a task."
                if task is None:
                    failed_times += 1
                    print("Failed: " + self.name)
                    self.last_op = "Fail sleeping."
                    time.sleep(2)
                else:
                    url = task["_id"]
                    try:
                        runningColl.insert_one({"_id": url})
                        if storageColl.find_one({"_id": url}, {"_id": 1}) is None:
                            self.last_op = "Querying."
                            doc_storage = query_url(url)
                            self.last_op = "Queried."
                            relatedURLs = doc_storage.pop("related")
                            runningColl.delete_one({"_id": url})
                            storageColl.insert_one(doc_storage)
                            self.last_op = "Inserted, appending."
                            for task in relatedURLs:
                                condition_doc = {"_id": task.split("?")[0]}
                                if all((coll.find_one(condition_doc, {"_id": 1}) is None for coll in coll_list)):
                                    try:
                                        waitingColl.insert_one(condition_doc)
                                    except:
                                        pass
                        else:
                            print("DUMP  : %s" % url)
                        failed_times = 0
                    except Exception as ex:
                        if deleted_error(ex):
                            print("Found a HTTP Error URL:" + url)
                            try:
                                runningColl.delete_one({"_id": url})
                                deletedColl.insert_one({"_id": url})
                            except:
                                print("Error to process deleted url.")
                        else:
                            print("Error to process: %s" % url)
                            print(traceback.format_exc())
                            waitingColl.insert_one({"_id": url})
                            runningColl.delete_one({"_id": url})
                            failed_times += 1


if __name__ == '__main__':
    dbName = "spider"
    collPrefix = "xhamster"

    with MongoDBDatabase(dbName) as mgdb:
        for res in mgdb.get_collection(collPrefix + "_running").find({}):
            try:
                mgdb.get_collection(collPrefix + "_queue").insert(res)
            except:
                pass
        mgdb.get_collection(collPrefix + "_running").drop()

    with MongoDBCollection(dbName, collPrefix + "_queue") as coll:
        if coll.count() <= 0:
            for i in range(3):
                for url in get_top_urls(i + 1):
                    try:
                        coll.insert({"_id": url})
                    except:
                        print("Error while inserting " + url)

    thread_list = [SpiderThread(db_name=dbName, coll_prefix=collPrefix) for _ in range(concurrency_num)]
    [t.start() for t in thread_list]
    opThread = LastOpMonitor(thread_list, 5)
    # opThread.start()
    [t.join() for t in thread_list]
