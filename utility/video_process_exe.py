import sys
import json
import math
import traceback
from moviepy.editor import VideoFileClip, VideoClip

img_count = 15
duration = 0.5


def video_to_shortcuts(infile: str, outfile: str):
    video_cap = VideoFileClip(infile)
    frame_size = video_cap.size
    video_basic_info = {
        "frame_rate": video_cap.fps,
        "size": {
            "width": frame_size[0],
            "height": frame_size[1],
        },
        "time": video_cap.duration
    }
    with open(outfile + ".json", "w") as fp:
        json.dump(video_basic_info, fp)
    vc = VideoClip(
        make_frame=lambda t: video_cap.get_frame((video_cap.duration-3) * t / (img_count * duration)),
        duration=img_count * duration
    )
    vc = vc.set_fps(
        math.ceil(1 / duration)
    )
    vc.write_gif(outfile + ".gif")


if __name__ == "__main__":
    try:
        infile = sys.argv[1]
        outfile = sys.argv[2]
        print("{}-->{}".format(infile, outfile))
        video_to_shortcuts(infile, outfile)
        print("done.")
    except Exception as ex:
        print("error.")
        print(traceback.format_exc(), file=sys.stderr)
