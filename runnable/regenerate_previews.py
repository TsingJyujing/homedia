import os
import traceback
import utility.video_processor_ffmpeg as video
from config import auto_fix_path

video_path = auto_fix_path("/mnt/e/File/www/video/file/")
preview_path = auto_fix_path("/mnt/e/File/www/video/preview/")


def main():
    list_of_file = [x for x in os.listdir(video_path) if x.endswith("mp4")]
    for file in list_of_file:
        try:
            print("Processing: %s" % file)
            video_cap = video.get_video_cap(os.path.join(video_path, file))
            video.get_video_preview(video_cap, os.path.join(preview_path, file[:-3] + "gif"))
            print("Process done: %s" % file)
        except Exception as _:
            print("Error while procrssing: %s" % file)
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
