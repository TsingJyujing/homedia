import json
import base64
from config import request_timeout, agency_address
from utility.pyurllib import URLReadThread




def auto_retry_url_read_json(url, retry_times=5):
    ex = None
    for i in range(retry_times):
        try:
            return url_read_json(url)
        except Exception as cex:
            ex = cex
    raise ex


def url_read_json(url):
    th = URLReadThread(url)
    th.start()
    th.join(request_timeout)
    if th.data is None:
        raise Exception("Error while reading API:" + url)
    obj = json.loads(th.data.decode())
    if "status" in obj:
        if obj["status"] == "error":
            error_info = "\n\n".join(("%s\n%s" % (key, obj[key]) for key in obj))
            raise Exception("Error in remote API:\n" + error_info)
    return obj


def get_top_urls(page_index:int):
    return [base64.b64decode(x).decode("UTF-8") for x in
            auto_retry_url_read_json(agency_address + "/agency/xhamster/query/top/?index=%d" % page_index)["data"]]


def get_query_urls(key_word:str,page_index:int):
    return [base64.b64decode(x).decode("UTF-8") for x in
            auto_retry_url_read_json(agency_address + "/agency/xhamster/query/search/?query=%s&index=%d" % (key_word,page_index))["data"]]

def query_url(url):
    return auto_retry_url_read_json(
        agency_address + "/agency/xhamster/query/info?url=" + base64.b64encode(url.encode("UTF-8")).decode("UTF-8"))
