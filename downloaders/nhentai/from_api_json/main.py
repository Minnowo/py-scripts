

# A script used to download doujin from nhentai.net from their api json files
# Just give the script a json file and wait


import requests 
import collections 
import threading 
import os 
import traceback
import time 

API = "https://i5.nhentai.net/galleries/"

class Worker_Queue():

    def __init__(self, function, daemon=False) -> None:
        
        self.kill = False 
        self.dead = False 
        self.alive = True 
        self.is_working = False 
        self.__items = []
        self.__callbacks = []

        self.__callback = function

        self.__signal = threading.Event()
        self.__thread = threading.Thread(target=self.__worker_thread, daemon=daemon)
        self.__thread.start()

    def update_callback(self, callback):
        
        self.callback = callback 
   
    def enqueue_callback(self, item, callback, set_flag = True):

        self.__callbacks.append(callback)
        self.__items.append(item)

        if set_flag:
            self.__signal.set()

    def enqueue(self, item, set_flag = True):
        # enqueue the item and set the flag -> True 
        self.__callbacks.append(self.__callback)
        self.__items.append(item)
        
        if set_flag:
            self.__signal.set()

    def __worker_thread(self):
        
        # keep thread waiting
        while not self.kill:
            
            # if there are items in the queue
            # process until the queue is empty 
            if self.__items:
                # invoke the callback given by the user and return their item 
                self.is_working = True 

                callback = self.__callbacks.pop(0)
                item     = self.__items.pop(0)

                callback(item)

            else:
                # only kill thread after all items have been processed with
                if not self.alive:
                    break

                self.is_working = False 

                # reset the flag and pause the thread
                self.__signal.clear()
                self.__signal.wait()

    def has_items(self):

        return not not self.__items

    def clear(self):

        self.__items.clear()

    def cleanup(self, fast=False):
        
        if fast:
            self.__items.clear() 
            self.kill = True 

        # allow while loop to end
        self.alive = False

        # trigger signal to end while loop
        self.__signal.set()

        self.__thread.join()

        del self.__thread 
        del self.__signal 

        self.dead = True 

    def __del__(self):

        if not self.dead:
            self.cleanup()



def parse_int(value, default=0):
    """Convert 'value' to int"""
    if not value:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def metadata_api( json):
    data = json

    title_en = data["title"].get("english", "")
    title_ja = data["title"].get("japanese", "")

    info = collections.defaultdict(list)
    for tag in data["tags"]:
        info[tag["type"]].append(tag["name"])

    return {
        "title"     : title_en or title_ja,
        "title_en"  : title_en,
        "title_ja"  : title_ja,
        "gallery_id": data["id"],
        "media_id"  : parse_int(data["media_id"]),
        "date"      : data["upload_date"],
        "scanlator" : data["scanlator"],
        "artists"   : info["artist"],
        "groups"    : info["group"],
        "parodies"  : info["parody"],
        "characters": info["character"],
        "tags"      : info["tag"],
        "type"      : info["category"][0] if info["category"] else "",
        "languages" : [i.capitalize() for i in info["language"]],
    } 


def download(data):

    try:
        sess = data['sess']
        url = data['url']
        output = data['output']
        file = data['file']
        
        print("downloading: " + url)
        res = sess.get(url)

        if res.status_code == 200:

            with open(os.path.join(str(output), file), "wb") as writer:

                writer.write(res.content)

    except Exception as e:

        print(e)
        print(traceback.format_exc())


def main():
    import json 
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
        dest="input", metavar="FOLDER", action="append",
        help="Specify input file(s)"
    )
    rename.add_argument(
        "-o", "--output",
        dest="output", metavar="FOLDER",
        help="Specify the output directory"
    )
    rename.add_argument(
        "-t", "--threads",
        dest="thread_count", metavar="INT",
        help="Thread count"
    )

    args = parser.parse_args()

    if not args.input:
        parser.error("input folder is required. use -i 'folder'")
    
    thread_counot = max(parse_int(args.thread_count, 1), 1)

    if not args.thread_count:
        thread_counot = 1

    if not args.output:
        args.output = "."

    # making the threads daemon cause thread.join never works with keyboard interrupt no matter how much i try,
    # still leaving in the code to actually join them tho, so it's a real mess ngl 
    threads = [Worker_Queue(download, True) for i in range(thread_counot)]

    def m(input):

        with open(os.path.abspath(input), "r") as reader:
            data = json.load(reader)

        metadata = metadata_api(data)

        output = str(data['media_id'])
        pages  = parse_int(data['num_pages'])

        ext = { "j" : "jpg", "p" : "png", "g" : "gif" }

        os.makedirs(os.path.join(args.output, output), exist_ok=True)

        with open(os.path.join(args.output, output, ".json"), "w") as writer:
            
            json.dump(metadata, writer, indent=3)

        try:

            t = 0
            with requests.Session() as sess:

                for i in range(1, pages + 1):

                    n = str(i) + "." + ext[data['images']["pages"][i - 1]['t']]
                    url = API + output + "/" + n

                    d = { 
                        'sess' : sess ,
                        'url' : url ,
                        'output' : os.path.join(args.output, output),
                        'file' : n,
                    }

                    threads[t].enqueue(d)

                    t = (t + 1) % thread_counot


            while any(i.has_items() for i in threads):
                
                time.sleep(1)

        except KeyboardInterrupt:
            
            for i in threads:
            
                i.clear()


        except Exception as e:

            print(e)
            print(traceback.format_exc())

            for i in threads:
                i.clear()
            
    try:
        x = 0 
        args.input = list(filter(lambda x : os.path.isfile(os.path.abspath(x)), args.input))
        for i in args.input:

            print(f'\n{x + 1}/{len(args.input)}')
            m(os.path.abspath(i))

            x += 1

    except KeyboardInterrupt:
        for i in threads:
            i.clear() 

    finally:
        for i in threads:

            i.cleanup(True)


if __name__ == "__main__":
    main() 