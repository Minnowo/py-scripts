
import os
import subprocess
import tempfile
import argparse
import datetime

from subprocess import PIPE


FFMPEG = os.path.join(os.path.dirname(__file__), "..\\.ffmpeg\\ffmpeg.exe")
FFPROBE = os.path.join(os.path.dirname(__file__), "..\\.ffmpeg\\ffprobe.exe")


def get_parser():

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]... URL...",
        add_help=False,
    )

    general = parser.add_argument_group("General Options")
    general.add_argument(
        "-h", "--help",
        action="help",
        help="Print this help message and exit",
    )

    rename = parser.add_argument_group("Options")
    rename.add_argument(
        "-i", "--input",
        dest="inputs", metavar="FILE", action="append",
        help="Specify input file. multiple -i can specified"
    )
    rename.add_argument(
        "-t", "--target",
        dest="target", metavar="xMB",
        help="Target file size in MB"
    )
    rename.add_argument(
        "--overwrite",
        dest="overwrite", action="store_true",
        help="Overwrite existing files"
    )
    rename.add_argument(
        "-na", "--no-audio",
        dest="noaudio", action="store_true",
        help="Put all the bitrate into the video stream"
    )
    rename.add_argument(
        "-ao", "--audio-only",
        dest="audioonly", action="store_true",
        help="Removes video and only compresses the audio as mp3"
    )
    rename.add_argument(
        "-fp", "--ffmpeg",
        dest="ffmpeg_path", metavar="PATH",
        help="Specify the path to ffmpeg"
    )
    rename.add_argument(
        "-fb", "--ffprobe",
        dest="ffprobe_path", metavar="PATH",
        help="Specify the path to ffprobe"
    )

    return parser


def parse_float(value, default=0):
    if not value:
        return default

    try:
        return float(value)

    except (ValueError, TypeError):
        return default


def set_date_modified(file_path, date_time):
    dt_epoch = date_time.timestamp()
    os.utime(file_path, (dt_epoch, dt_epoch))


def compress_video_file(file_path, output_file_path,
                        target_file_size_mb, *, FFMPEG_PATH=FFMPEG,
                        FFPROBE_PATH=FFPROBE, PRINT=False,
                        NO_AUDIO=False, AUDIO_ONLY=False):




    # https://trac.ffmpeg.org/wiki/Encode/H.264#twopass


    if not os.path.isfile(file_path):
        return (False, f"Path: {file_path} does not exist")

    duration = subprocess.run([FFPROBE_PATH, '-v', 'quiet', '-show_entries', 'format=duration', '-of','csv=p=0', file_path],
        shell=False, stdout=PIPE)

    duration = parse_float(duration.stdout.decode(), -1)

    if duration <= 0:
        if PRINT:
            print("\033[93mFile has no duration. Skipping.\033[0m")
        return (False, "Could not read a duration from given file")

    total_bitrate = (target_file_size_mb * 8192) / duration
    video_bitrate = total_bitrate * (3/4)
    audio_bitrate = total_bitrate * (1/4)

    if NO_AUDIO:
        audio_bitrate = 0
        video_bitrate = total_bitrate

    # instead of using a temp file, you can pass NUL or /dev/null depending on windows/linux
    if (os.name == "nt"):
        no_temp = "NUL"
    else:
        no_temp = "/dev/null"

    # the .log file ffmpeg will create, just use a temp file
    two_pass_log = os.path.join(tempfile.gettempdir(), "ffmpeg2pass-0.log")

    if AUDIO_ONLY:
        audio_bitrate = total_bitrate
        video_bitrate = 0 

        p1 = subprocess.run([FFMPEG_PATH, '-v', 'error', '-y',
                            '-i', file_path, '-b:a', str(audio_bitrate) + 'k',
                            '-pass', '1', "-vn", '-f', 'mp3',
                            '-passlogfile', two_pass_log, no_temp], stdout=PIPE, stderr=PIPE)

        p2 = subprocess.run([FFMPEG_PATH, '-v', 'error', '-y', 
                    '-i', file_path, '-b:a', str(audio_bitrate) + 'k',
                    '-pass', '2', "-vn", '-f', 'mp3', 
                    '-passlogfile', two_pass_log, str(output_file_path)], stdout=PIPE, stderr=PIPE) 

    else:
        p1 = subprocess.run([FFMPEG_PATH, '-v', 'error', '-y', 
                        '-i', file_path, '-c:v', 'libx264', '-b:v', str(video_bitrate) + 'k',
                        '-pass', '1', '-an', '-f', 'mp4', '-passlogfile', two_pass_log, no_temp], stdout=PIPE, stderr=PIPE)

        # keep audio 
        if not NO_AUDIO:
            p2 = subprocess.run([FFMPEG_PATH, '-v', 'error', '-y', 
                        '-i', file_path, '-c:v', 'libx264', '-b:v', str(video_bitrate) + 'k',
                        '-pass', '2', '-c:a', 'aac', '-b:a', str(audio_bitrate) + 'k',  
                        '-passlogfile', two_pass_log, str(output_file_path)], stdout=PIPE, stderr=PIPE)
        
        # remove audio from the video 
        else:
            p2 = subprocess.run([FFMPEG_PATH, '-v', 'error', '-y', 
                        '-i', file_path, '-c:v', 'libx264', '-b:v', str(video_bitrate) + 'k',
                        '-pass', '2', '-an',
                        '-passlogfile', two_pass_log, str(output_file_path)], stdout=PIPE, stderr=PIPE)

    p1err = p1.stderr.decode()
    p2err = p2.stderr.decode()

    if p1err != "":
        return (False, p1err)

    if p2err != "":
        return (False, p2err)

    # set the date modified of the new file to the same as the old file
    set_date_modified(output_file_path, datetime.datetime.fromtimestamp(os.path.getmtime(file_path)))

    if PRINT:
        print("video bitrate: " + str(video_bitrate))
        print("audio bitrate: " + str(audio_bitrate))
        print("input path   : " + str(file_path))
        print("output path  : " + str(output_file_path))

    return (True , "")

def main(_args):
    
    from time import sleep
    from random import random

    parser = get_parser()
    args = parser.parse_args(_args)

    if not args.inputs:
        parser.error("no input file specified")

    target = args.target

    if not args.target:
        target = 8

    if args.ffmpeg_path:
        peg = args.ffmpeg_path

    else:
        peg = FFMPEG

    if args.ffprobe_path:
        probe = args.ffprobe_path

    else:
        probe = FFPROBE

    if args.audioonly and args.noaudio:
        parser.error("Audio Only cannot be used with No Audio")

    os.system("") # enable color in windows

    total = len(args.inputs)
    c = 1
    for i in args.inputs:
        print(f"working... ({c}/{total})")

        if args.audioonly:
            ext = ".mp3"

        else:
            ext = ".mp4"

        tmp_name = i + "RE9ORQ0K.tmp" + ext

        if args.overwrite:
            if compress_video_file(i, tmp_name, float(target), FFMPEG_PATH=peg, FFPROBE_PATH=probe, PRINT=True, NO_AUDIO=args.noaudio, AUDIO_ONLY=args.audioonly):
                
                sleep(1)

                tmp = os.path.join(".TMP", os.path.basename(i) + str(random()) + ".BAK")

                try:
                    os.makedirs(os.path.dirname(tmp), exist_ok=True)
                    os.rename(i, tmp)

                    if i.lower().strip().endswith(ext):
                        os.rename(tmp_name, i)
                    else:
                        os.rename(tmp_name, i + ext)

                    os.unlink(tmp)
                    os.removedirs(os.path.dirname(tmp))
                except:
                    os.rename(tmp, i)
                    print("\033[91mUnable to delete/overwrite the old file.\nTemp path: " + tmp + "\nOriginal path: " + i + "\033[0m")

        else:
            compress_video_file(i, tmp_name, float(target), FFMPEG_PATH=peg, FFPROBE_PATH=probe, PRINT=True, NO_AUDIO=args.noaudio, AUDIO_ONLY=args.audioonly)

        c += 1

        if c <= total:
            print("=" * 20)

    print("\033[92mDone.\033[0m")

if __name__ == "__main__":
    import sys 
    main(sys.argv[1:])





