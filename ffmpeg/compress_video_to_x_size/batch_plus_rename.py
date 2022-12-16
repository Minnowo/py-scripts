


import compress 
import argparse
import os 
import random
from re import compile
from datetime import datetime


class DigitTemplateGenerator:
    """A class that returns a template string formatted with digits
    
    formats strings containing any 2 templates:
       $[n:z]   where n is the starting number and z is the ending number (increment is 1 by default)
       $[n:i:z] where n is the starting number, i is the increment and z is the ending number

    example usage:
        
        template = "sample_$[1:100]"

        d_format = DigitFormatter(template)
        d_format.get_formatted_text() # -> sample_1
        d_format.get_formatted_text() # -> sample_2
        d_format.get_formatted_text() # -> sample_3
         
    """
    # split function for the digit formats $[1:1] or $[1:1:1]
    DIGIT_SPLIT  = compile(r"\$\[-?\d+(?:\:-?\d+)?:-?\d+\]").split

    # matches $[1:9] or $[1:1:9]
    DIGIT_MATCH  = compile(r"\$\[(-?\d+)(?:\:(-?\d+))?\:(-?\d+)\]")

    def __init__(self, template : str) -> None:
        
        self.split = [i for i in self.DIGIT_SPLIT(template)]
        self.digits = []
        self.digit_counter = []
        self.end = len(self.split)

        for i in self.DIGIT_MATCH.findall(template):
            increment = 1 

            if i[1]:
                increment = int(i[1])

            # format the digits as ints (start, increment, max)
            self.digits.append((int(i[0]), increment, int(i[2])))  

        self.reset()
            
    def get_next_string(self):
        """Gets the name formatted with the current digits and increments all the digits"""
        # begin building the name
        name = ""
        count = 0                                # loop count 
        index = 0                                # index of the current digit position
        for i in self.split:

            # make sure its not the first or last loop
            if count > 0 and count < self.end:
                
                # tuple (start, zfill) -> the starting digit, and the zfill 
                d = self.digit_counter[index]         

                # append the current digit to the string and apply zfill
                name += f"{d[0]}".zfill(d[1])         

                # (start, zfill)[0] < (start, increment, max)[2] 
                # if less than max increase by the increment amount
                if d[0] < self.digits[index][2]:

                    self.digit_counter[index][0] += self.digits[index][1]

                # move to next index 
                index += 1 
            
            # append the string
            name += i 
            count += 1

        return name 

    def reset(self):
        """Resets all the counters for each digit"""
        # reset / init the digit counter array 
        self.digit_counter = []
        for dig in self.digits: 
            # dig[0] = start number
            # dig[2] = end number
            start = dig[0] 
            pad_zeros = len(str(dig[2]))

            self.digit_counter.append([start, pad_zeros])

class TextFormatter:

    RE_EXT     = compile(r"\$\[EXT\]")                # repalce file extension
    RE_RAND    = compile(r"\$\[RND\:(\d+)\:(\d+)\]")  # random number

    def __init__(self, template) -> None:
        self.template = template
        self.file_ext = ""

    def add_context(self, context):

        ext = context.rsplit(".", 1)

        if len(ext) > 1:
            self.file_ext = ext[-1]

        else:
            self.file_ext = ""

    def format_text(self, text):

        text = self.RE_EXT.sub(self.file_ext, text)  

        # random number
        for i in self.RE_RAND.findall(text):
            text = self.RE_RAND.sub(str(random.randint(int(i[0]), int(i[1]))), text, 1)

        return text 

class DateFormatter(TextFormatter):

    SUB_MAP = {
        "FDM" : compile(r"\$\[FDM\]").sub,
        "FDC" : compile(r"\$\[FDC\]").sub,
        "CD"  : compile(r"\$\[CD\]").sub
    }

    # matches $[FDM]  or $[FDC] pr $[CD]
    MATCH_SIMPLE_DATE = compile(r"\$\[(FDM|FDC|CD)\]")
    
    # matches $[FDM: 'anything that is not [ or ]' ]
    # matches $[FDC: 'anything that is not [ or ]' ]
    MATCH_CUSTOM_DATE = compile(r"\$\[(FDM|FDC|CD):([^\]]+)\]")      

    def __init__(self, template, *, default_date_format = "%Y-%m-%d", require_file_exist = True) -> None:
        
        TextFormatter.__init__(self, template)

        # simple date sub will just sub everything and there is only 2 options so just remove duplicates
        self.simple_date_format = set(self.MATCH_SIMPLE_DATE.findall(template))

        # list of tuple -> (DM / DC, custom date format)
        self.custom_date_format = self.MATCH_CUSTOM_DATE.findall(template)

        self.file_name = ""

        self.date_format = default_date_format
        self.require_file_exist = require_file_exist
        
    def add_context(self, context):
        """Set the filename for formatting file date created / modified"""
        
        self.file_name = context

    def format_text(self, templage):

        name = templage
        file_date_created = 0
        file_date_modified = 0

        if os.path.isfile(self.file_name):
            file_date_created = os.stat(self.file_name).st_ctime
            file_date_modified = os.stat(self.file_name).st_mtime

        elif self.require_file_exist:
            raise Exception("DateFormatter.get_formatted_text -> given file does not exist, requires the file exists")
            
        for i in self.simple_date_format:

            if i == "FDM":
                name = self.SUB_MAP[i](datetime.fromtimestamp(file_date_modified).strftime(self.date_format), name)
            
            elif i == "FDC":
                name = self.SUB_MAP[i](datetime.fromtimestamp(file_date_created).strftime(self.date_format), name)

            elif i == "CD":
                name = self.SUB_MAP[i](datetime.fromtimestamp(datetime.now().timestamp()).strftime(self.date_format), name)


        for i in self.custom_date_format:

            if i[0] == "FDM":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(file_date_modified).strftime(i[1]), name, 1)

            elif i[0] == "FDC":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(file_date_created).strftime(i[1]), name, 1)
                
            elif i[0] == "CD":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(datetime.now().timestamp()).strftime(i[1]), name, 1)
        
        return name

def natural_sort_key(s, _nsre=compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

def get_temp_filename(directory, similarname = "", x = 5):

    x = 100**x
    name = os.path.join(directory, similarname + str(hex(int(random.random() * x))) + ".tmp")

    while os.path.isfile(name):
        name = os.path.join(directory, similarname + str(hex(int(random.random() * x))) + ".tmp")
 
    return name 

def remove_options(parser, options):
    for option in options:
        for action in parser._actions:
            if vars(action)['option_strings'][0] == option:
                parser._handle_conflict_resolve(None,[(option,action)])
                break

def get_parser():
    parser = compress.get_parser() 

    remove_options(parser, ["-i", "--input"])
    remove_options(parser, ["-o", "--overwrite"])

    general = parser.add_argument_group("Batch + Rename Options")
    general.add_argument(
        "-i", "--input",
        dest="input", metavar="DIRECTORY", action="append",
        help="Specify input directory"
    )
    general.add_argument(
        "-f", "--format",
        dest="format",
        help="The name format",
    )
    general.add_argument(
        "-fh", "--format-help",
        dest="formathelp", action="store_true",
        help="Shows formatting options",
    )

    return parser
    

def main(_args):
    
    parser = get_parser()
    args = parser.parse_args(_args)
    
    format = "$[FDM]-$[1:999].$[EXT]"
    target = 8
    peg    = compress.FFMPEG
    probe  = compress.FFPROBE

    if args.formathelp:
        print("-- Formats --")
        print("$[EXT]          : the files extension (forced to be mp4)") 
        print("$[0:10]         : a digit that starts at 0 and increments by 1 until 10")
        print("$[0:2:10]       : a digit that starts at 0 and increments by 2 until 10")
        print("$[RND:0:999]    : a random number anywhere from 0-999")
        print("$[FDM]          : the date modified")   
        print("$[FDC]          : the date created")   
        return

    if not args.input:
        parser.error("no input directory specified")

    if args.format:
        format = args.format

    if args.target:
        target = float(args.target)

    if args.ffmpeg_path:
        peg = args.ffmpeg_path

    if args.ffprobe_path:
        probe = args.ffprobe_path

    items  = {"directories" : set(), "files" : set()}

    for i in args.input:

        if os.path.exists(i):
            if os.path.isdir(i):
                items["directories"].add(os.path.abspath(i))

            elif os.path.isfile(i):
                items["files"].add(os.path.abspath(i))

    standard_format = TextFormatter(format)
    date_format     = DateFormatter(format)
    digit_format    = DigitTemplateGenerator(format)
    
    for dir in items["directories"]:

        print("Directory: " + dir)

        digit_format.reset()

        for file in sorted(os.listdir(dir),key=natural_sort_key):

            file = os.path.abspath(os.path.join(dir, file))

            if not os.path.isfile(file):
                continue
            
            new_filename = digit_format.get_next_string()

            date_format.add_context(file)
            new_filename = date_format.format_text(new_filename)

            if args.audioonly:
                ext = ".mp3"

            else:
                ext = ".mp4"

            standard_format.add_context(file + ext) # force .mp4 file extension
            new_filename = standard_format.format_text(new_filename)

            new_filepath     = os.path.join(dir, new_filename)
            print("   Compressing " + os.path.basename(file), end="...", flush=True)

            r = compress.compress_video_file(file, new_filepath, target, 
                       FFMPEG_PATH=peg, FFPROBE_PATH=probe, PRINT=False, NO_AUDIO=args.noaudio, AUDIO_ONLY=args.audioonly)

            if not r[0]:
                print(" \033[91m-> ERROR: " + r[1].strip(), end="\033[0m\n")
                continue

            print(" \033[92m-> " + os.path.basename(new_filename), end="\033[0m\n")

if __name__ == "__main__":
    import sys 
    os.system("") # enable color in windows
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("\n\033[91mKeyboardInterrupt\033[0m")