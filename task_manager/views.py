import string
import time

from django.views.decorators.csrf import csrf_exempt
from utility.http_response import response_json
from utility.xhamster import xHamsterDownloadTask
from utility.pyurllib import DownloadTask, RemoteDownloadTask
from utility.xvideos import XVideoDownloadTask

supported_task_type = {"download_file", "download_xvideo", "download_xhamster","download_file_agencily"}
task_list = {}
check_min_interval = 0.5


def clear_invalid_tasks():
    for key in task_list.keys():
        if task_list[key].terminated:
            task_list.pop(key)


@csrf_exempt
@response_json
def append_task(request):
    """
    Append a task to task list and start it
    :param request: 
    :return:
    """
    task_type = request.POST["task_type"]
    assert task_type in supported_task_type, "Unsupported task type"
    parameter = request.POST["param"]
    key = generate_a_key()
    if task_type == "download_xvideo":
        task_append = XVideoDownloadTask(parameter, key)
    elif task_type == "download_xhamster":
        task_append = xHamsterDownloadTask(parameter, key)
    elif task_type == "download_file":
        filename = parameter.split("/")[-1].split("?")[0]
        task_append = DownloadTask(parameter, "buffer/%s" % filename)
    elif task_type == "download_file_agencily":
        task_append = RemoteDownloadTask(parameter)
    else:
        raise Exception("Unsupported task type (Fatal)")
    task_list[key] = task_append
    task_append.start()
    return {"status": "success"}


@csrf_exempt
@response_json
def remove_task(request):
    """
    Remove a task to task list and start it
    :param request: 
    :return: 
    """
    task_key =int(request.POST["task_key"])
    if task_key in task_list:
        task_list.pop(task_key)
        return {"status": "success"}
    else:
        raise Exception("this task has cleared from task list")


@response_json
def query_tasks(request):
    return_data = [{
        "id": key,
        "name": task_list[key].getName(),
        "type": str(type(task_list[key])),
        "progress": task_list[key].progress,
        "info": task_list[key].progress_info
    } for key in task_list.keys()]
    clear_invalid_tasks()
    return return_data


def generate_a_key():
    for i in range(1000):
        key = int(time.time() * 1000)
        if key not in task_list.keys():
            return key
        else:
            time.sleep(1)
    raise Exception("Failed to create a new task key")
