import re
import os


def get_extension(filename):
    last_seg = filename.replace("\\", "/").split("/")[-1].split(".")
    if len(last_seg) > 1:
        return "." + last_seg[-1]
    else:
        return ""


def filter_extension(filename, extensions):
    return re.search("\\.(%s)$" % "|".join(extensions), filename) is not None


regexp_image_file = re.compile("\\.(%s)$" % "|".join([
    "jpg",
    "jpeg",
    "bmp",
    "png",
    "gif"
]))


def filter_images(image_filename):
    return regexp_image_file.search(image_filename) is not None


def walk_files(local_dir):
    all_files = list()
    if os.path.exists(local_dir):
        files = os.listdir(local_dir)
        for x in files:
            filename = os.path.join(local_dir, x)
            if os.path.isdir(filename):
                all_files.extend(walk_files(filename))
            else:
                all_files.append(filename)
    else:
        print('{} does not exist'.format(local_dir))
    return [file.replace("\\", "/") for file in all_files]
