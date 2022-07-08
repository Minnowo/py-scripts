import os
import random 
from re import compile, match
from datetime import datetime

WINDOWS = (os.name == "nt")

# super long ugly multi-line message, so just putting it here as bytes to be decoded on run
DATE_FORMAT_HELP_MESSAGE = b"\nCode  Example     Description\n%a    Sun         Weekday as locale's abbreviated name.\n%A    Sunday      Weekday as locale's full name.\n%w    0           Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.\n%d    08          Day of the month as a zero-padded decimal number.\n%-d   8           Day of the month as a decimal number. (Platform specific)\n%b    Sep         Month as locale's abbreviated name.\n%B    September   Month as locale's full name.\n%m    09          Month as a zero-padded decimal number.\n%-m   9           Month as a decimal number. (Platform specific)\n%y    13          Year without century as a zero-padded decimal number.\n%Y    2013        Year with century as a decimal number.\n%H    07          Hour (24-hour clock) as a zero-padded decimal number.\n%-H   7           Hour (24-hour clock) as a decimal number. (Platform specific)\n%I    07          Hour (12-hour clock) as a zero-padded decimal number.\n%-I   7           Hour (12-hour clock) as a decimal number. (Platform specific)\n%p    AM          Locale's equivalent of either AM or PM.\n%M    06          Minute as a zero-padded decimal number.\n%-M   6           Minute as a decimal number. (Platform specific)\n%S    05          Second as a zero-padded decimal number.\n%-S   5           Second as a decimal number. (Platform specific)\n%f    000000      Microsecond as a decimal number, zero-padded on the left.\n%z    +0000       UTC offset in the form \xc2\xb1HHMM[SS[.ffffff]] (empty string if the object is naive).\n%Z    UTC         Time zone name (empty string if the object is naive).\n%j    251         Day of the year as a zero-padded decimal number.\n%-j   251         Day of the year as a decimal number. (Platform specific)\n%x    09/08/13    Locale's appropriate date representation.\n%X    07:06:05    Locale's appropriate time representation.\n%%    %           A literal '%' character.\n\n%U    36          Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.\n                  All days in a new year preceding the first Sunday are considered to be in week 0.\n\n%W    35          Week number of the year (Monday as the first day of the week) as a decimal number.\n                  All days in a new year preceding the first Monday are considered to be in week 0.\n\n%c    Sun Sep 8 07:06:05 2013       Locale's appropriate date and time representation.".decode()

# supported formats
FORMAT_HELP_MESSAGE = """
-- Formats --
$[EXT]          : the files extension
$[0:10]         : a digit that starts at 0 and increments by 1 until 10
$[0:2:10]       : a digit that starts at 0 and increments by 2 until 10
$[RND:0:999]    : a random number anywhere from 0-999
$[FDM]          : the file date modified
$[FDC]          : the file date created
$[CD]           : the current date
$[CD:%Y-%m-%d]  : specify a custom date format -> run --date-formats to see all of them
"""

DEFAULT_SEP = "|"

DEFAULT_RN_FILE = ".rn"

RESTRICT_MAP = {
        "auto" : "\\\\|/<>:\"?*" if WINDOWS else "/",
        "unix" : "/",
        "windows" : "\\\\|/<>:\"?*",
    }

# removes invalid path characters
RM_INVALID      = compile(f"[{RESTRICT_MAP['auto']}]").sub
# what invalid path characters will become
REPLACE_INVALID = "_"

# console colors 
HEADER    ="\033[95m"
OKBLUE    ="\033[94m"
OKCYAN    ="\033[96m"
OKGREEN   ="\033[92m"
WARNING   ="\033[93m"
FAIL      ="\033[91m"
ENDC      ="\033[0m"
BOLD      ="\033[1m"
UNDERLINE ="\033[4m"



def natural_sort_key(s, _nsre=compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]



def get_sep(string, *, throw_error = False, error = ""):
    """Get the separator character from a string -> sep=|"""
    _ = string.find("=")
    
    if _ == -1:
        if throw_error: raise Exception(error)
        return DEFAULT_SEP

    _ = string[_ + 1:] # take everything after the =
    _ = _[:-1]         # remove the last character of the string (assumes \n)
    return _



def handle_undo(file : list):
    """Reads a list of [.rn] files and renames all existing files back to before being renamed for each file"""
    cwd = os.getcwd()

    for f in file:

        if not os.path.exists(f):
            continue

        if os.path.isdir(f):
            try:
                dir  = os.path.abspath(f) 
                os.chdir(dir)
                paths = filter(lambda x : x.endswith(".rn"), os.listdir()) # grab any .rn files 

            finally:
                os.chdir(cwd)

        if os.path.isfile(f):
            dir  = os.path.dirname(f) 
            paths = [os.path.basename(f)]

        for rn in paths:

            renamer = Renamer(DEFAULT_RN_FILE, no_log = True)

            full_path = os.path.join(dir, rn)

            print("{0}{1}:{2}".format(WARNING, full_path, ENDC))

            try:
                os.chdir(dir)

                with open(full_path, "rb") as rn_file:
                    _ = rn_file.readline().decode()
                    sep = get_sep(_, throw_error=True, error="Invalid .rn file cannot get separator")
                    
                    for line in rn_file:
                        
                        lined = line.decode()

                        if lined.startswith("ERROR" + sep):
                            if lined.count(sep) != 2: # if there is an error there will be 3 occurance of sep
                                continue
                        
                        old_n, _, new_n = lined.partition(sep)

                        new_path =  new_n[:-1]

                        if os.path.exists(new_path):
                            renamer.rename(new_path, old_n)

            except Exception as e:
                print(FAIL, getattr(e, 'message', repr(e)), ENDC)
            
            finally:
                os.chdir(cwd)
    
    os.chdir(cwd)



def get_parser():
    import argparse

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

    rename = parser.add_argument_group("Rename Options")
    rename.add_argument(
        "-i", "--input",
        dest="inputs", metavar="FOLDER", action="append",
        help="Specify input directories"
    )
    rename.add_argument(
        "-f", "--format",
        dest="format", metavar="FORMAT",
        help="Specify the format to rename"
    )
    rename.add_argument(
        "-r", "--replace",
        dest="replace", metavar="REPLACE:WITH", action="append",
        help="Replace any occurance of anything before the last : with anything after the last :"
    )
    rename.add_argument(
        "-u", "--undo",
        dest="undo_file", metavar="FILE", action="append",
        help="Undo any renaming done using the provided .rn file"
    )


    filter_ops = parser.add_argument_group("Filter Options")
    filter_ops.add_argument(
        "-sw", "--start-with",
        dest="start_with", metavar="STR", action="append", default=[],
        help="Only rename files that start with the given string (multiple --start-with can be specified)"
    )
    filter_ops.add_argument(
        "-ew", "--ends-with",
        dest="ends_with", metavar="STR", action="append",  default=[],
        help="Only rename files that end with the given string (multiple --ends-with can be specified)"
    )
    filter_ops.add_argument(
        "-m", "--match",
        dest="matches", metavar="REGEX", action="append",  default=[],
        help="Only rename if the filename matches any of the given regex"
    )
    

    after_rename = parser.add_argument_group("Undo File Options")
    after_rename.add_argument(
        "--no-file",
        dest="no_rn_file", action="store_true",
        help="Do not create .rn file"
    )
    after_rename.add_argument(
        "-a", "--append-rn",
        dest="append_rn_data", action="store_true",
        help="Should file rename history be appended to existing .rn file"
    )
    after_rename.add_argument(
        "-s", "--sep",
        dest="sep", metavar="SEP", default=DEFAULT_SEP,
        help="The separator character used in the .rn file"
    )

    help_options = parser.add_argument_group("Format Help")
    help_options.add_argument(
        "--date-formats",
        dest="custom_date_formats", action="store_true",
        help="Show all custom date formats"
    )
    help_options.add_argument(
        "--format-help",
        dest="display_formats", action="store_true",
        help="Show format string variables"
    )
    

    return parser



class Renamer:
    """
    A simple wrapper around os.rename that handles printing to the console and logging into a file
    
        __init__(directory, log_file, overwrite_existing, no_log)
            - directory : the directory where files are going to be renamed
            - log_file  : the name of the log file
            - overwrite_existing : overwrite existing logfile, otherwise appends
            - no_log : doesn't write anything to the log file
        
        rename(file_name, new_name) : renames the given file
            - file_name : the name of the file relative to the given directory from __init__
            - new_name  : the new name of the file relative to the given directory from __init__
        log(text) : write the given text to the log file
            - text : bytes / encoded text NOT string -> use string.encode()
        close() : closes the log file
    """
    def __init__(self, log_file, *, sep = "|", overwrite_existing = True, no_log = False) -> None:
        
        self.log_file_name = log_file

        self.logger = None
        self.sep = sep
        self.pad = 50

        if no_log:
            return

        # get the path to the rn file
        _ = log_file

        # if file exists, and the user wants to append logs to existing .rn file, 
        # read the file and get the separator character,
        if os.path.exists(_) and not overwrite_existing:
            with open(_, "r") as fff:
                self.sep = get_sep(fff.readline())

            self.logger = open(_, "ab")  

        # else just override the old file
        else:
            # reading / writing as bytes because of foreign characters
            self.logger = open(_, "wb")    
            self.logger.write(f"sep={self.sep}\n".encode())

    def close(self):
        if self.logger:
            self.logger.close()

    def log(self, text):
        if not self.logger:
            return 

        self.logger.write(text)

    def rename(self, file_name, new_name):

        print('   {0:<{1}} '.format(file_name, self.pad), end="")

        try:
            os.rename(file_name, new_name)

            self.log(f"{file_name}{self.sep}{new_name}\n".encode())

            print('{0}-->{2} {1}'.format(OKGREEN, new_name, ENDC))

        except Exception as e:
            self.log(f"ERROR|{file_name}{self.sep}{new_name}\n".encode())
            
            print("{0}-->{2} {1}".format(FAIL, getattr(e, 'message', repr(e)), ENDC)) 
            

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

    def __init__(self) -> None:
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

    def __init__(self, *, default_date_format = "%Y-%m-%d", require_file_exist = True) -> None:
        
        TextFormatter.__init__(self)

        self.file_name = ""

        self.date_format = default_date_format
        self.require_file_exist = require_file_exist
        
    def add_context(self, context):
        """Set the filename for formatting file date created / modified"""
        
        self.file_name = context

    def format_text(self, template):

        name = template
        file_date_created = 0
        file_date_modified = 0

        if os.path.isfile(self.file_name):
            file_date_created = os.stat(self.file_name).st_ctime
            file_date_modified = os.stat(self.file_name).st_mtime

        elif self.require_file_exist:
            raise Exception("DateFormatter.get_formatted_text -> given file does not exist, requires the file exists")
            
        for i in set(self.MATCH_SIMPLE_DATE.findall(template)):

            if i == "FDM":
                name = self.SUB_MAP[i](datetime.fromtimestamp(file_date_modified).strftime(self.date_format), name)
            
            elif i == "FDC":
                name = self.SUB_MAP[i](datetime.fromtimestamp(file_date_created).strftime(self.date_format), name)

            elif i == "CD":
                name = self.SUB_MAP[i](datetime.fromtimestamp(datetime.now().timestamp()).strftime(self.date_format), name)


        for i in self.MATCH_CUSTOM_DATE.findall(template):

            if i[0] == "FDM":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(file_date_modified).strftime(i[1]), name, 1)

            elif i[0] == "FDC":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(file_date_created).strftime(i[1]), name, 1)
                
            elif i[0] == "CD":
                name = self.MATCH_CUSTOM_DATE.sub(datetime.fromtimestamp(datetime.now().timestamp()).strftime(i[1]), name, 1)
        
        return name




def main():

    parser = get_parser()
    args = parser.parse_args()

    if args.display_formats:
        print(FORMAT_HELP_MESSAGE)
        return

    if args.custom_date_formats:
        print(DATE_FORMAT_HELP_MESSAGE)
        return 

    if args.undo_file:
        handle_undo(args.undo_file)
        return

    if not args.inputs:
        parser.error("No inputs specified")
        return 

    if not args.format and not args.replace:
        print("No output format or replace specified use -f \"FORMAT\" to specify a format --format-help for more info\nor -r 'word:replacement' to replace words")
        return

    
    _replace = {} 
    _format  = args.format

    # filters 
    _ends_with   = args.ends_with
    _starts_with = args.start_with
    _regex       = args.matches

    # rename instance args 
    _no_log             = args.no_rn_file
    _sep                = args.sep
    _overwrite_existing = not args.append_rn_data

    # directories to rename
    _directories = set()



    if args.replace:                  # replace specified

        for i in args.replace:        # go through all given strings
            
            _ = i.rsplit(":", 1)      # split at last occurance of :
            
            if len(_) == 2:           # if there is not 2 items skip
                _replace[_[0]] = _[1] # set dict 



    for i in args.inputs:

        if not os.path.exists(i):
            continue

        if os.path.isdir(i):
            _directories.add(os.path.abspath(i))


    
    standard_format = TextFormatter()
    date_format     = DateFormatter()
    digit_format    = DigitTemplateGenerator(_format)
    
    cwd = os.getcwd()

    for dir in _directories:

        renamer = Renamer(os.path.join(dir, DEFAULT_RN_FILE), 
                          sep = _sep,
                          overwrite_existing = _overwrite_existing, 
                          no_log = _no_log)

        digit_format.reset()

        print("{0}{1}:{2}".format(WARNING, dir, ENDC))

        try:
            os.chdir(dir)

            files = sorted(os.listdir(dir), key=natural_sort_key)

            renamer.pad = len(max(files, key=len))

            for file in files:

                if not os.path.isfile(file):
                    continue

                if file == DEFAULT_RN_FILE:
                    continue

                if _regex:
                    if not any(match(regex, file) for regex in _regex):
                        continue
                
                if _starts_with:
                    if not any([file.startswith(i) for i in _starts_with]):
                        continue
                
                if _ends_with:
                    if not any([file.endswith(i) for i in _ends_with]):
                        continue
                
                n_file = file

                if _format:

                    n_file = digit_format.get_next_string()

                    date_format.add_context(file)
                    n_file = date_format.format_text(n_file)

                    standard_format.add_context(file)
                    n_file = standard_format.format_text(n_file)


                if _replace:

                    for key, value in _replace.items():
                    
                        n_file = n_file.replace(key, value)


                n_file = RM_INVALID(REPLACE_INVALID, n_file)

                renamer.rename(file, n_file)


        except OSError as e:
            pass 

        finally:
            os.chdir(cwd)

            # close our log file
            renamer.close()







if __name__ == "__main__":
    os.system("") # console color on windows
    main()