# -*- coding: utf-8 -*-
"""my_porn_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from daf.views import *
from task_manager.views import *
from page_render.views import *

urlpatterns = [

    url(r'^admin/', admin.site.urls),

    # 获取某一个ID下所有的图片和基础信息
    url(r'^homedia/get/images', get_images_info),

    # 获取某一个ID的小说内容和基础信息
    url(r'^homedia/get/novel', get_novel),

    # 依据标题搜索小说
    url(r'^homedia/query/novel/bytitle', query_novel_by_title),

    # 依据标题搜索视频（板块信息不完善）
    url(r'^homedia/query/video/bytitle', query_video_list),

    # 依据标题搜索图帖信息
    url(r'^homedia/query/images/bytitle', query_images_list),

    # 依据标题搜索图帖信息
    url(r'^homedia/query/images/nearby', get_nearby_images),

    # 根据ID查询视频的基础信息
    url(r'^homedia/query/video/byid', query_video),

    # 根据ID删除视频
    url(r'^homedia/remove/video', remove_video),

    # 根据ID删除视频
    url(r'^homedia/remove/novel', remove_novel),

    # 根据ID删除视频
    url(r'^homedia/remove/images', remove_images),

    # 设置是否喜欢视频
    url(r'^homedia/set/video/like', set_video_like),

    # 设置是否喜欢图片集
    url(r'^homedia/set/images/like', set_images_like),

    # 设置是否喜欢小说
    url(r'^homedia/set/novel/like', set_novel_like),

    # 获取所有正在进行的任务
    url(r'^homedia/query/task/all', query_tasks),

    # 查询小说的页面渲染
    url(r'^homedia/view/query/novel', render_query_novel),

    # 查询视频的页面渲染
    url(r'^homedia/view/query/video', render_query_video),

    # 查询视频的页面渲染
    url(r'^homedia/view/query/images', render_query_images),

    # 查询视频的页面渲染
    url(r'^homedia/view/images', render_view_images),

    # 浏览小说的页面
    url(r'^homedia/view/novel', render_novel_reader),

    # 添加任务
    url(r'^homedia/append/task', append_task),

    # 移除任务
    url(r'^homedia/remove/task', remove_task),

    # 任务管理界面
    url(r'^homedia/manage/tasks', render_task_manage_page),

    # XHAMSTER预览界面
    url(r'^homedia/view/xhamster/detail', render_xhamster_viewer),

    # XHAMSTER预览界面
    url(r'^homedia/view/xhamster/top', render_xhamster_top_viewer),

    # XHAMSTER预览界面
    url(r'^homedia/get/xhamster/info', get_xhamster_detail),

    url(r'^homedia/set/xhamster/rate', set_xhamster_rate),

    # 根据标签查找相应的
    url(r'^homedia/query/xhamster/bylabel', query_xhamster_bylabel),

    # XHAMSTER首页数据
    url(r'^homedia/get/xhamster/top', query_xhamster_top_urls),
    # XHAMSTER首页数据
    url(r'^homedia/get/xhamster/query', query_xhamster_query_urls),

    url(r'^homedia$', render_homedia_index_page),

    url(r'^$', render_index_page),

]
