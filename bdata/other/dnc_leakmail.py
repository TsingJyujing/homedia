# -*- coding: utf-8 -*-
"""
Created on 2017-2-4
@author: Yuan Yi fan
"""

from utility.list_file_io import write_raw
from utility.pyurllib import urlread2


def get_mail_data(id):
    """
    :param id: Index of mail (up to 22456)
    :return: email text
    """
    return urlread2("https://wikileaks.org/dnc-emails//get/%d" % id)


def save_mail(id, filename):
    """
    :param id: Index of mail (up to 22456)
    :param filename: saving filename(and path before)
    :return: None
    """
    write_raw(filename, get_mail_data(id))
