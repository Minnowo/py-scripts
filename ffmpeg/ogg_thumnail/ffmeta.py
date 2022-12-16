

# a python re-write of https://github.com/twopoint71/ogg-image-blobber

import os 
import base64

GREEN  ="\033[92m"
YELLOW ="\033[93m"
RED    ="\033[91m"
ENDC   ="\033[0m"

def generate_blobber(image_path : str, output : str):

    DESCRIPTION      = "Cover Artwork"
    IMAGE_MIME_TYPE  = "image/jpeg"
    TYPE_ALBUM_COVER = 3

    FILE_SIZE = os.stat(image_path).st_size

    buffer = bytearray()

    with open(image_path, "rb") as binary_reader:
        with open(output , "wb") as binary_writer:

            # write ffmetadata header
            binary_writer.write(b";FFMETADATA1\n")
            binary_writer.write(b"METADATA_BLOCK_PICTURE=")
            
            # i've never used bytearray in python, this is the only way i could figure out to add more bytes
            # Picture type <32>
            buffer += bytearray(TYPE_ALBUM_COVER.to_bytes(4, byteorder="big", signed=False)) 

            # Mime type length <32>
            buffer += bytearray(len(IMAGE_MIME_TYPE).to_bytes(4, byteorder="big", signed=False))

            # Mime type (n * 8)
            buffer += bytearray(IMAGE_MIME_TYPE.encode())

            # Description length <32>
            buffer += bytearray(len(DESCRIPTION).to_bytes(4, byteorder="big", signed=False))

            # Description (n * 8)
            buffer += bytearray(DESCRIPTION.encode())

            # Picture width <32>
            buffer += bytearray((0).to_bytes(4, byteorder="big", signed=False)) # why does this work?

            # Picture height <32>
            buffer += bytearray((0).to_bytes(4, byteorder="big", signed=False))  # why does this work?

            # Picture color depth <32> (probably should figure this out, but seems to be okay at 0)
            buffer += bytearray((0).to_bytes(4, byteorder="big", signed=False))
            
            # Picture color index <32> (0 for jpg, only really applicable to gifs)
            buffer += bytearray((0).to_bytes(4, byteorder="big", signed=False))

            # Image file size <32>
            buffer += bytearray(FILE_SIZE.to_bytes(4, byteorder="big", signed=False))

            # Image file (n * 8)
            buffer += bytearray(binary_reader.read(FILE_SIZE))

            binary_writer.write(base64.b64encode(buffer))


if __name__ == "__main__":
    
    import argparse

    parser = argparse.ArgumentParser(add_help=False)

    general = parser.add_argument_group("General Options")
    general.add_argument("-h", "--help", action="help", help="Print this help message and exit")
    general.add_argument("-i", "--input",dest="inputs", metavar="FILE", action="append",help="Specify input file (jpg/jpeg). multiple -i can specified")

    args = parser.parse_args()

    if not args.inputs:
        parser.error("must specify an input jpg file. see -h for more info.")

    os.system("") # enable color in windows
  
    for i in args.inputs:
        
        try:
            print(f"converting {YELLOW}{i}{ENDC}", end="", flush=True)
            generate_blobber(i, i + ".base64")
            print(f" -> {GREEN}" + os.path.basename(i + ".base64") + ENDC)
        except Exception as e:
            print(" -> {0}{1}: {2}{3}".format(RED, type(e).__name__, e , ENDC))