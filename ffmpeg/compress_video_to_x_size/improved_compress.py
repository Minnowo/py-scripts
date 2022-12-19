import os
import subprocess
import tempfile
import datetime

FFPROBE_PATH = os.path.join(os.path.dirname(__file__), "..\\.ffmpeg\\ffprobe.exe")
FFMPEG_PATH = os.path.join(os.path.dirname(__file__), "..\\.ffmpeg\\ffmpeg.exe")

if (os.name == "nt"):
    NO_TEMP = "NUL"
else:
    NO_TEMP = "/dev/null"


class FFMPEG_Exception(Exception):
    """raised when ffmpeg has an error"""


def check_file_exists(path: str):

    if not os.path.isfile(path):
        raise OSError(f"file '{path}' does not exist")


def round_to_8x(value: float):

    if value <= 0:
        return 0

    value = int(value)
    low = (value // 8) * 8
    high = low + 8

    if abs(high - value) > abs(value - low):
        return low

    return high


def get_temp_filename(dir: str, starting_with: str, extension: str):

    fail_after = 100
    fail = 0

    while True:

        name = os.path.join(dir, f"{starting_with}{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.{extension}")

        if not os.path.isfile(name):
            return name

        fail += 1

        if fail > fail_after:
            raise OSError(f"could not make temppath starting with {starting_with} and ending with {extension} after trying {fail} times")


def parse_float(value: str, default=0):

    if not value:
        return default

    try:
        return float(value)
    except ValueError:
        return default



def subprocess_communicate(process: subprocess.Popen, timeout: int = 10) -> tuple:

    while True:

        try:

            return process.communicate(timeout=timeout)

        except subprocess.TimeoutExpired:

            pass


def run_program(args: list):

    return subprocess_communicate(
        subprocess.Popen(args, bufsize=10**5,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE))


def get_audio_video_stream(path: str):

    if not os.path.isfile(FFPROBE_PATH):
        raise OSError(f"could not find ffprobe with path '{FFPROBE_PATH}'")

    check_file_exists(path)

    (stdout, stderr) = run_program([FFPROBE_PATH, "-v", "quiet", "-show_entries",
                                    "stream=codec_type", "-of", "default=nw=1:nk=1", path])
    return (b"audio" in stdout,
            b"video" in stdout)




def get_file_duration(path: str):

    if not os.path.isfile(FFPROBE_PATH):
        raise OSError(f"could not find ffprobe with path '{FFPROBE_PATH}'")

    check_file_exists(path)

    (stdout, sdterr) = run_program([FFPROBE_PATH, '-v', 'quiet',
                               '-show_entries', 'format=duration',
                               '-of', 'csv=p=0', path])

    duration = parse_float(stdout.decode(), -1)

    if duration <= 0:
        return -1

    return duration



def compress_file(path: str, target_size_mb: int, video_bitrate_percent: float, new_size: tuple = None):

    if target_size_mb <= 0:
        raise ValueError(f"you cannot specify a target size <= 0 mb: {target_size_mb}")


    if video_bitrate_percent < 0 or video_bitrate_percent > 1:
        raise ValueError(f"video bitrate percent must be a value between 0 and 1, given: {video_bitrate_percent}")

    (has_audio, has_video) = get_audio_video_stream(path)

    print(f"detected audio stream: {has_audio}")
    print(f"detected video stream: {has_video}")

    if not has_audio and not has_video:
        raise OSError(f"file '{path}' does not contain any video or audio streams")

    duration = get_file_duration(path)

    if duration == -1:
        raise OSError(f"file '{path} does not contain any duration")

    total_bitrate = (target_size_mb * 8192) / duration

    if has_video:
        video_bitrate = round_to_8x(total_bitrate * video_bitrate_percent)

        if has_audio:
            audio_bitrate = round_to_8x(total_bitrate * (1 - video_bitrate_percent))
        else:
            video_bitrate = round_to_8x(total_bitrate)
            audio_bitrate = 0

    elif has_audio:
        audio_bitrate = round_to_8x(total_bitrate * (1 - video_bitrate_percent))

        if has_video:
            video_bitrate = round_to_8x(total_bitrate * video_bitrate_percent)
        else:
            video_bitrate = 0
            audio_bitrate = round_to_8x(total_bitrate)

    file_dir = os.path.dirname(path)

    temp_dir = os.path.join(file_dir, ".compress_temp_dir")

    os.makedirs(temp_dir, exist_ok=True)

    print(f"detected duration: {duration}")
    print(f"target total bitrate : {total_bitrate}")
    print(f"target video bitrate : {video_bitrate}")
    print(f"target audio bitrate : {audio_bitrate}")

    audio_path  = get_temp_filename(temp_dir, "audio", "mp3")
    video_path  = get_temp_filename(temp_dir, "video", "mp4")
    video_path2 = get_temp_filename(temp_dir, "video", "mp4")


    if has_audio and audio_bitrate > 0:

        print("compressing audio...")

        compress_audio(path, audio_path, audio_bitrate)

    if has_video and video_bitrate > 0:

        print("compressing video...")

        # if new_size is not None:

        #     reduce_resolution(path, video_path2, new_size) 

        #     compress_video(video_path2, video_path, video_bitrate)

        # else:
        
        compress_video(path, video_path, video_bitrate, new_size)

    output = get_temp_filename(file_dir, os.path.basename(path) + "-", "mp4")
    combine_to_mp4(audio_path, video_path, output)

    print(output)


def combine_to_mp4(audio_path: str, video_path: str, output_path: str):

    audio_exists = os.path.isfile(audio_path)
    video_exists = os.path.isfile(video_path)

    if not audio_exists and not video_exists:
        raise OSError(f"both video and audio path do not exist: '{audio_path}', '{video_path}'")

    args = [FFMPEG_PATH, '-v', 'error', "-y"]

    if audio_exists:

        args.extend(["-i", audio_path])

    if video_exists:

        args.extend(["-i", video_path])

    args.extend([
        "-c", "copy", output_path
    ])

    (stdout, stderr) = run_program(args)

    if stderr != b"":
        raise FFMPEG_Exception(stderr.decode())



def reduce_resolution(path: str, output_path: str, new_size: tuple):

    check_file_exists(path)

    (width, height) = new_size

    (stdout, stderr1) = run_program([FFMPEG_PATH, '-v', 'error', '-y',
                            '-i', path, '-filter:v', f"scale={width}:{height}",
                            output_path])

    if stderr1 != b"":
        raise FFMPEG_Exception(stderr1.decode())

def compress_audio(path: str, output_path: str, audio_bitrate: int):

    check_file_exists(path)

    two_pass_log = os.path.join(tempfile.gettempdir(), "ffmpeg2pass-0.log")

    (stdout, stderr1) = run_program([FFMPEG_PATH, '-v', 'error', '-y',
                            '-i', path, '-b:a', str(audio_bitrate) + 'k',
                            '-pass', '1', "-vn", '-f', 'mp3',
                            '-passlogfile', two_pass_log, NO_TEMP])


    (stdout, stderr2) = run_program([FFMPEG_PATH, '-v', 'error', '-y',
                    '-i', path, '-b:a', str(audio_bitrate) + 'k',
                    '-pass', '2', "-vn", '-f', 'mp3',
                    '-passlogfile', two_pass_log, str(output_path)])


    if stderr1 != b"":
        raise FFMPEG_Exception(stderr1.decode())

    if stderr2 != b"":
        raise FFMPEG_Exception(stderr2.decode())




def compress_video(path: str, output_path: str, video_bitrate: int, resize: tuple = None):

    check_file_exists(path)

    two_pass_log = os.path.join(tempfile.gettempdir(), "ffmpeg2pass-0.log")

    (stdout, stderr1) = run_program([FFMPEG_PATH, '-v', 'error', '-y',
                        '-i', path, '-c:v', 'libx264', '-b:v', str(video_bitrate) + 'k',
                        '-pass', '1', '-an', '-f', 'mp4',
                        '-passlogfile', two_pass_log, NO_TEMP])


    cmd = [FFMPEG_PATH, '-v', 'error', '-y',
                        '-i', path, '-c:v', 'libx264', '-b:v', str(video_bitrate) + 'k',
                        '-pass', '2', '-an',
                        ]

    if resize is not None:
        
        (width, height) = resize

        cmd.extend(['-filter:v', f"scale={width}:{height}"])

    cmd.extend(['-passlogfile', two_pass_log, str(output_path)])

    (stdout, stderr2) = run_program(cmd)

    if stderr1 != b"":
        raise FFMPEG_Exception(stderr1.decode())

    if stderr2 != b"":
        raise FFMPEG_Exception(stderr2.decode())


def run_guided():

    from tkinter.filedialog import askopenfilename
    from tkinter import Tk
    import traceback

    ROOT = Tk()
    ROOT.withdraw()

    while True:

        target_file_path = askopenfilename()

        if not os.path.isfile(target_file_path):
            continue

        print(f"Compressing: {target_file_path}\n")
        break


    while True:

        target_file_size = parse_float(input("Enter the target file size in Megabytes (MB): "), -1)

        if target_file_size < 0:
            continue

        print(f"Targeting: {target_file_size}MB\n")
        break


    while True:

        target_video_percent = parse_float(input("Enter the video compression percentage,\nThis value should be between 0 and 1 (inclusive),\nThis value determines how much the video and audio is compressed,\nEx. 0=No video only want audio, 1=Video only and no audio, 0.5=Compress audio and video about equally\nRecommend 0.8: "), -1)

        if target_video_percent < 0 or target_video_percent > 1:
            continue

        print(f"Video Percent: {target_video_percent}\n")
        break

    try:

        compress_file(target_file_path, target_file_size, target_video_percent)

    except OSError as e:
        print(f"\nAn OS error has occurred: {e}")
        print(traceback.format_exc())

        with open('error.txt', 'a') as f:
            f.write(str(e))
            f.write(traceback.format_exc())

    except FFMPEG_Exception as e:
        print(f"\nAn FFMPEG error has occurred: {e}")
        print(traceback.format_exc())

        with open('error.txt', 'a') as f:
            f.write(str(e))
            f.write(traceback.format_exc())


    input("--- Done ---")


def main():

    global FFPROBE_PATH, FFMPEG_PATH

    import argparse

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]... URL...",
        add_help=False,
    )

    general = parser.add_argument_group("General Options")
    general.add_argument(
        "--help",
        action="help",
        help="Print this help message and exit",
    )
    general.add_argument(
        "-i", "--input",
        dest="inputs", metavar="FILE", action="append",
        help="Specify input file. multiple -i can specified"
    )
    general.add_argument(
        "-t", "--target", default=8,
        dest="target", metavar="xMB",
        help="Target file size in MB"
    )
    general.add_argument(
        "-p", "--percent", default=0.8,
        dest="percent", metavar="xMB",
        help="Video/Audio compression, 0=No video All audio, 1=All video no audio, 0.5=Half should be video half should be audio"
    )
    general.add_argument(
        "-w", "--width",
        dest="width", metavar="X",
        help="Resize the video to have this width before compressing (cannot be used with -h)"
    )
    general.add_argument(
        "-h", "--height",
        dest="height", metavar="X",
        help="Resize the video to have this height before compressing (cannot be used with -w)"
    )
    general.add_argument(
        "--guided",
        dest="guided", action="store_true",
        help="Run a simple guided wizard"
    )
    general.add_argument(
        "-fp", "--ffmpeg",
        dest="ffmpeg_path", metavar="PATH",
        help="Specify the path to ffmpeg"
    )
    general.add_argument(
        "-fb", "--ffprobe",
        dest="ffprobe_path", metavar="PATH",
        help="Specify the path to ffprobe"
    )

    args = parser.parse_args()

    if args.guided:
        run_guided()
        return

    if not args.inputs:
        parser.error("Input file(s) are required, use -i <path> to specify")

    if args.ffprobe_path:
        FFPROBE_PATH = args.ffprobe_path

    if args.ffmpeg_path:
        FFMPEG_PATH = args.ffmpeg_path

    new_size = None 

    if args.width:

        _ = parse_float(args.width, None)

        if _ is not None:
        
            new_size = (int(_), "trunc(ow/a/2)*2")

    if args.height:

        _ = parse_float(args.height, None)

        if _ is not None:
        
            new_size = ("trunc(oh*a/2)*2", int(_))

    target = parse_float(args.target, 8)
    percent = parse_float(args.percent, 0.8)

    for i in args.inputs:

        if not os.path.isfile(i):
            print(f'File "{i} does not exist, skipping..."')
            continue


        try:
            print(f"Compressing: {i}:")
            compress_file(i, target, percent, new_size)

        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
