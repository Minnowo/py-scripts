

import os 
import subprocess
from subprocess import PIPE

FFMPEG = os.path.join(os.path.dirname(__file__), "..\\.ffmpeg\\ffmpeg.exe")

def main():
    from ffmeta import generate_blobber, RED, ENDC, GREEN, YELLOW

    import argparse

    parser = argparse.ArgumentParser(add_help=False)

    general = parser.add_argument_group("General Options")
    general.add_argument("-h", "--help",  action="help", help="Print this help message and exit")
    general.add_argument("-a", "--audio", dest="audio", metavar="FILE", help="Specify the audio file.")
    general.add_argument("-j", "--jpg",   dest="image", metavar="FILE", help="Specify the jpg file.")
    general.add_argument("-o", "--output",dest="output", metavar="FILE", help="Specify the output audio filename.")

    args = parser.parse_args()

    if not args.audio:
        parser.error("must specify an audio file. see -h for more info.")

    if not args.image:
        parser.error("must specify a jpg file. see -h for more info.")

    if not args.output:
        args.output = "output.opus"

    blob = args.image + ".base64"


    try:
        print(f"generating blob {YELLOW}{args.image}{ENDC}", end="", flush=True)
        generate_blobber(args.image, blob)
        print(f" -> {GREEN}" + os.path.basename(blob) + ENDC)
    except Exception as e:
        print(" -> {0}{1}: {2}{3}".format(RED, type(e).__name__, e , ENDC))
        return 
    
    ffargs = [FFMPEG, '-v', 'error', '-y', "-i", args.audio, "-i", blob, "-map_metadata", "1", "-codec", "copy", args.output]
    
    print(f"{YELLOW}" + " ".join(ffargs) + f"{ENDC}")

    p = subprocess.run(ffargs, stderr=PIPE, shell=True)

    _err = p.stderr.decode()

    if _err:
        print(f"{RED}{_err}{ENDC}")
    else:
        print(args.output)

if __name__ == "__main__":

    main()
