from pprint import pprint
import requests
import os 
import json 
import hydrus_api
from re import compile

try:
    import image_size_reader as isr 
    ISR_NOT_FOUND = False 
except ImportError:

    ISR_NOT_FOUND = True 

class Service():

    def __init__(self, service_name : str, service_key : str) -> None:
        self.name = service_name
        self.key = service_key

API_KEY = "insert your api key here"

TAG_SERVICE = Service("tag service name", "service key")

DEFAULT_API_URL = "http://127.0.0.1:45869/"

CLIENT = hydrus_api.Client(API_KEY, DEFAULT_API_URL)


def natural_sort_key(s, _nsre=compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]


def list_services():

    s = CLIENT.get_services()
    
    for key, value in s.items():

        print(key)
        for i in value:
            print("   ", i)
        print()


def add_doujin(folder_path : str, **kwargs):

    if not os.path.isdir(folder_path):
        return  

    files = []
    all_file_tags = []
    service_names = [TAG_SERVICE.name]
    service_keys  = [TAG_SERVICE.key ] 

    if "tags" in kwargs:
        all_file_tags.extend(kwargs['tags'])

    # all files 
    _files = sorted([os.path.join(folder_path, i) for i in os.listdir(folder_path)], key=natural_sort_key)

    if ISR_NOT_FOUND:

        _image_files_ext = [".png", ".jpg", ".jpeg", ".jpe", ".jfif", ".tiff", ".tif", ".bmp", ".webp", ".gif"]
        files.extend(filter(lambda x : any(x.endswith(i) for i in _image_files_ext), _files))

    else:
        # image files 
        files.extend(filter(lambda x : isr.get_image_size(x) != (0, 0), _files))

    # metadata 
    meta = list(filter(lambda x : x.endswith('.json'), _files))

    TAGS = [
        ('title_pretty', "title:"),
        ('title_en'    , "title:"),
        ('title_jp'    , "title:"),
        ('title_ja'    , "title:"),
        ('title'       , "title:"),
        ('gallery_id'  , "gallery id:"),
        ('artist'      , "creator:"),
        ('artists'     , "creator:"),
        ('character'   , "character:"),
        ('characters'  , "character:"),
        ('parody'      , "parody:"),
        ('parodies'    , "parody:"),
        ('group'       , "group:"),
        ('groups'      , "group:"),
        ('tag'         , ""),
        ('tags'        , ""),
        ('type'        , "type:"),
        ('language'    , "language:"),
        ('languages'   , "language:"),
    ]

    for i in meta:
        
        with open(i, 'r') as reader:

            data = json.load(reader)
            
            for ii in TAGS:
                
                if ii[0] in data:
    
                    if isinstance(data[ii[0]], int):
                        all_file_tags.append(ii[1] + str(data[ii[0]])) 

                    elif isinstance(data[ii[0]], str):

                        all_file_tags.append(ii[1] + data[ii[0]].strip().lower()) 

                    elif isinstance(data[ii[0]], list):
                        
                        for iii in data[ii[0]]:

                            all_file_tags.append(ii[1] + iii.strip().lower()) 
    
    _ = -1 
    for i in files:
        _ += 1
        tags = ['page:' + str(_ + 1)]
        tags.extend(all_file_tags)
        
        print(CLIENT.add_and_tag_files([i], tags, service_names, service_keys))


def main():
    import argparse

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]... URL..."
    )

    rename = parser.add_argument_group("Options")
    rename.add_argument(
        "-i", "--input",
        dest="input", metavar="FOLDER",
        help="Specify input directory"
    )
    rename.add_argument(
        "-l", "--list-services",
        dest="lists",action="store_true",
        help="List services"
    )
    rename.add_argument(
        "-k", "--kwargs",
        dest="kwargs", metavar="key|value", action="append",
        help="Specify key word arguments"
    )

    args = parser.parse_args()
    
    if args.lists:
        list_services()
        return 
    
    if not args.input:
        parser.error("-i or --input is required")    

    kwargs = {
        "tags" : ['move-to-book-like']
    }

    if args.kwargs:
        
        for i in args.kwargs:
            
            _ = i.split("|", 1)

            if len(_) == 2:

                if _[0] in kwargs:
                    kwargs[_[0]].append(_[1])

                else:
                    kwargs[_[0]] = [_[1]]

    print(kwargs)

    add_doujin(os.path.abspath(args.input), **kwargs)



if __name__ == "__main__":
    main()