# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 22:44:29 2015

@author: TsingJyujing

基础的文件操作和字符串矩阵、列表的存取
"""
import csv


def write_raw(filename, data):  # 快速存储得到的数据
    with open(filename, 'wb') as fp:
        fp.write(data)


def read_raw(filename):  # 快速存储得到的数据
    with open(filename, 'r') as fp:
        return fp.read()


def write_strlist(filename, str_list):
    with open(filename, 'w') as f:
        for str_elem in str_list:
            f.write(str_elem + '\n')


def read_strlist(filename):
    with open(filename, 'r') as fp:
        raw_list = fp.readlines()
        for index, str_elem in enumerate(raw_list):
            raw_list[index] = str_elem[:-1]
        return raw_list


def read_strmat(filename, division_char):
    with open(filename, "r", encoding="UTF-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=division_char)
        rtn = []
        for x in reader:
            rtn.append(x)
        return rtn


def write_strmat(filename, str_mat, division_char):
    with open(filename, "w", encoding="UTF-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=division_char)
        writer.writerows(str_mat)


if __name__ == "__main__":
    print("Usage: from list_file_io import *")
