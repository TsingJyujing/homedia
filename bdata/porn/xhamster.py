#!/bin/python
# -*- coding: utf-8 -*-
"""
Created on 2017-3-2
@author: Yuan Yi fan
"""
from typing import Iterable

from bs4 import BeautifulSoup
from utility.pyurllib import urlread2
from config import XML_decoder


def getSoup(url):
    """
    Get XML decode result and raw data from web agency
    :param url:
    :return:
    """
    page_data = urlread2(url)
    return page_data, BeautifulSoup(page_data, XML_decoder)


def getTitleFromSoup(sp):
    """
    Get title
    :param sp:
    :return:
    """
    return sp.find('title').text


def getRelatedVideosLink(sp):
    return [x for x in [elem.get("href") for elem in sp.find_all("a") if elem.has_attr("href")] if
            x.startswith("https://m.xhamster.com/videos") and x.endswith("?from=video_related")]


def getCategories(sp):
    res = sp.find('ul', attrs={'class', 'categories_of_video'}).find_all('a')
    categories_of_video = []
    for r in res:
        categories_of_video.append(r.text)
    return categories_of_video


def getRating(sp):
    res = sp.find('div', attrs={'class', 'rating'})
    return float(res.text[:-1])


def getTime(sp):
    try:
        res = sp.find('div', attrs={'class', 'time'})
        time_range = res.text.split(':')
        secs = int(time_range[0]) * 60 + int(time_range[1])
        return secs
    except:
        return 0


def getPreviewImageList(sp):
    res = sp.find('div', attrs={"class": "screenshots_block clearfix", "id": "screenshots_block"})
    res = res.find_all('img')
    return [r.get('src') for r in res]


def getAllPreviewImageList(sp):
    first_image_url = sp.find(
        'div',
        attrs={
            "class": "screenshots_block clearfix",
            "id": "screenshots_block"
        }
    ).find('img').get("src")

    first_image_url_split = first_image_url.split("/")
    first_image_url_prefix = "/".join(first_image_url_split[:-1])
    first_image_url_tail = "_".join(first_image_url_split[-1].split("_")[1:])
    url_template = first_image_url_prefix + "/%d_" + first_image_url_tail
    return [url_template % (i + 1) for i in range(10)]


def getDownloadLink(sp: BeautifulSoup) -> str:
    res = sp.find('a', attrs={"class": "download", "id": "video_download"})
    url_download = res.get('href')
    if not url_download[:5] == "https":
        url_download = "https" + url_download[4:]
    return url_download


def getTopURLs(page_id: int) -> Iterable[str]:
    _, sp = getSoup("https://m.xhamster.com/%d" % page_id)
    return __get_urls_from_soup(sp)


def queryKeywords(key_word: str) -> Iterable[str]:
    _, sp = getSoup("https://m.xhamster.com/search?q=%s" % key_word.replace(" ", "+"))
    return __get_urls_from_soup(sp)


def __get_urls_from_soup(sp: BeautifulSoup) -> Iterable[str]:
    return [elem.find("a").get("href") for elem in sp.find_all("div", attrs={"class": "item-container"})]
