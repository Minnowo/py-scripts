## OGG Thumbnail
Adds images/thumbnails to ogg/opus files  
[ffmeta.py](ffmeta.py) is a re-write of https://github.com/twopoint71/ogg-image-blobber  

### Usage

 you can run [add_thumbnail.py](add_thumbnail.py), 
    (show help command, listed below)
    ```
    python add_thumbnail.py -h
    ```

 or

 if you just want to generate the metadata file run [ffmeta.py](ffmeta.py). And use ffmpeg directly 
   ```
   python ffmeta.py -i 'filename.jpg'
   >> filename.jpg.base64

   ffmpeg -i audio.ogg -i filename.jpg.base64 -map_metadata 1 -codec copy out.ogg
   ```

### Help

 [add_thumbnail.py](add_thumbnail.py)
 ```
 usage: add_thumbnail.py [-h] [-a FILE] [-j FILE] [-o FILE]

 General Options:
  -h, --help               Print this help message and exit
  -a FILE, --audio FILE
                           Specify the audio file.
  -j FILE, --jpg FILE      Specify the jpg file.
  -o FILE, --output FILE
                           Specify the output audio filename.             
 ```

