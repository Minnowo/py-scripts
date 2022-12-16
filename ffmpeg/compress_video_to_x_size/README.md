## Compress Video To X Size
Compresses videos to a target file size in mb

### Usage

 you can run [compress.py](compress.py) directly, 
    (show help command, listed below)
    ```
    python compress.py -h
    ```

 or

 using the batch script,
    (show help command, listed below)
    ```
    python batch_plus_rename.py -h
    ```

### Help

 [compress.py](compress.py)
 ```
 General Options:
  -h, --help              Print this help message and exit

 Options:
  -i FILE, --input FILE      Specify input file. multiple -i can specified
                        
  -t xMB, --target xMB       Target file size in MB

  --overwrite                Overwrite existing files

  -na, --no-audio            Put all the bitrate into the video stream

  -fp PATH, --ffmpeg PATH    Specify the path to ffmpeg
                        
  -fb PATH, --ffprobe PATH   Specify the path to ffprobe
                        
 ```

 [batch_plus_rename.py](batch_plus_rename.py)
 ```
 General Options:
  -h, --help                        Print this help message and exit

 Options:
  -t xMB, --target xMB              Target file size in MB

  -na, --no-audio                   Put all the bitrate into the video stream

  -fp PATH, --ffmpeg PATH           Specify the path to ffmpeg
                        
  -fb PATH, --ffprobe PATH          Specify the path to ffprobe
                        

 Batch + Rename Options:
  -i DIRECTORY, --input DIRECTORY   Specify input directory
                        
  -f FORMAT, --format FORMAT        The name format
                        
  -fh, --format-help                Shows formatting options
 ```


