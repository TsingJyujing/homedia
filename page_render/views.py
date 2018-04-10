# -*- coding: utf-8 -*-
from django.shortcuts import render

from utility.http_response import get_request_with_default


def render_query_novel(request):
    return render(request, "query_novel.html")


def render_novel_reader(request):
    return render(request, "read_novel.html", {
        "novel_id": request.GET["id"]
    })


def render_task_manage_page(request):
    return render(request, "task_manage.html")


def render_query_video(request):
    return render(request, "query_video.html")


def render_query_images(request):
    return render(request, "query_images.html")


def render_view_images(request):
    return render(request, "view_images.html", {
        "images_id": request.GET["id"],
        "query_key_words": get_request_with_default(request, "key_words", "")
    })


def render_homedia_index_page(request):
    return render(request, "homedia.html")

def render_index_page(request):
    return render(request, "index.html")


def render_xhamster_viewer(request):
    return render(request, "xhamster_viewer.html", {
        "xhamster_context": request.GET["id"]
    })

def render_xhamster_top_viewer(request):
    return render(request, "xhamster_top.html")