import os
import sys
import json
from re import compile

METADATA_FILE = ".json"

MAIN_INDEX_HTML = "index.html"
SUB_INDEX_HTML = ".html"

ASSETS_FOLDER = ".\\assets"

def natural_sort_key(s, _nsre=compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

def serialize_unique(lst : list):
    dictionary = {}
    parody = []
    character = []
    tag = []
    artist = []
    group = []
    for dic in lst:
        if 'parody' in dic:
            parody.extend([i for i in dic['parody']])
        elif 'parodies' in dic:
            parody.extend([i for i in dic['parodies']])

        if 'character' in dic:
            character.extend([i for i in dic['character']])
        elif 'characters' in dic:
            character.extend([i for i in dic['characters']])

        if 'tag' in dic:
            tag.extend([i for i in dic['tag']])
        elif 'tags' in dic:
            tag.extend([i for i in dic['tags']])

        if 'artist' in dic:
            artist.extend([i for i in dic['artist']])
        elif 'artists' in dic:
            artist.extend([i for i in dic['artists']])

        if 'group' in dic:
            group.extend([i for i in dic['group']])
        elif 'groups' in dic:
            group.extend([i for i in dic['groups']])

    dictionary['parody'] = list(set(parody))
    dictionary['character'] = list(set(character))
    dictionary['tag'] = list(set(tag))
    dictionary['artist'] = list(set(artist))
    dictionary['group'] = list(set(group))
    return dictionary


def merge_json(path : str):
    output_json = []

    doujinshi_dirs = list_dirs(path)

    for folder in doujinshi_dirs:
        _folder = os.path.join(path, folder)
        files = os.listdir(_folder)

        if METADATA_FILE not in files:
            continue

        with open(os.path.join(_folder , METADATA_FILE), 'r') as f:
            json_dict = json.load(f)

            if 'Pages' in json_dict:
                del json_dict['Pages']
            elif 'pages' in json_dict:
                del json_dict['pages']
            elif 'count' in json_dict:
                del json_dict['count']

            json_dict['Folder'] = folder
            output_json.append(json_dict)

    return output_json


def set_js_database(path : str):
    with open(os.path.join(path, 'data.js'), 'w') as f:
        indexed_json = merge_json(path)
        unique_json = json.dumps(serialize_unique(indexed_json), separators=(',', ':'))
        indexed_json = json.dumps(indexed_json, separators=(',', ':'))
        f.write('var data = ' + indexed_json)
        f.write(';\nvar tags = ' + unique_json)


def list_dirs(path : str) -> list:
    current_directory = os.getcwd()
    try:
        os.chdir(path)
        return next(os.walk('.'))[1]
    finally:
        os.chdir(current_directory)

def read_file(path : str) -> str:
    """Reads a file in the same directory as this script"""
    loc = os.path.dirname(__file__)

    with open(os.path.join(loc, path), 'r') as file:
        return file.read()

def write_text(path : str, text : str) -> str:
    """Writes text to the given file"""
    if sys.version_info < (3, 0):
        with open(path, 'w') as f:
            f.write(text)

    else:
        with open(path, 'wb') as f:
            f.write(text.encode('utf-8'))

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def is_image(file):
    return os.path.splitext(file)[1].lower() in (".png",".jpg",".jpeg",".jfif",".jpe",".gif",".webp",".bmp",".tif",".tiff")

def generate_html(input, template, tab_name, view):
    WINDOWS = (os.name == "nt")
    
    files = []
    for i in os.listdir(input):

        path = os.path.join(input, i)
        if os.path.exists(path):

            if os.path.isfile(path):
                files.append(path)

    files.sort(key=natural_sort_key)

    image_html = ""
    for i in files:
        if is_image(i):
            if view:
                print(i)
            image_html += '<img loading="lazy" src="{0}" class="image-item"/>\n'.format(os.path.basename(i))
            # image_html += '<img src="{0}" class="image-item"/>\n'.format(os.path.basename(i))
        

    html = read_file(resource_path(os.path.join(ASSETS_FOLDER, '{}\\index.html'.format(template))))
    css = read_file(resource_path(os.path.join(ASSETS_FOLDER, '{}\\styles.css'.format(template))))
    js = read_file(resource_path(os.path.join(ASSETS_FOLDER, '{}\\scripts.js'.format(template))))

    name = SUB_INDEX_HTML

    if tab_name:
        t = tab_name
    elif input.strip() == ".":
        t = os.path.basename(os.getcwd())
    else:
        t = os.path.basename(os.path.dirname(input))

    data = html.format(TITLE=t, IMAGES=image_html, SCRIPTS=js, STYLES=css)

    try:
        if WINDOWS:
            # unlcok path length limit
            outn = "\\\\?\\" + os.path.abspath(os.path.join(input, name))
        else:
            outn = os.path.abspath(os.path.join(input, name))

        write_text(outn, data)
    except:
        print("ERROR writing file") 

def generate_main_html(output_dir='./', template="default"):
    """
    Generate a main html to show all the contain doujinshi.
    With a link to their `index.html`.
    Default output folder will be the CLI path.
    """

    image_html = ''

    main = read_file(resource_path(os.path.join(ASSETS_FOLDER, 'main.html')))
    css = read_file(resource_path(os.path.join(ASSETS_FOLDER, 'main.css')))
    # js = read_file(resource_path('.depends\\html_image_viewer\\main.js'))

    element = '\n\
            <div class="gallery-favorite">\n\
                <div class="gallery">\n\
                    <a href="./{FOLDER}/{SUB_HTML}" class="cover" style="padding:0 0 141.6% 0"><img\n\
                            src="./{FOLDER}/{IMAGE}" />\n\
                        <div class="caption">{TITLE}</div>\n\
                    </a>\n\
                </div>\n\
            </div>\n'

    doujinshi_dirs = list_dirs(output_dir)

    for folder in doujinshi_dirs:

        files = os.listdir(os.path.join(output_dir, folder))
        files.sort()
        title = (os.path.basename(os.path.abspath(output_dir)) + " - " + folder).replace('_', ' ')

        if SUB_INDEX_HTML in files:
            print('Add doujinshi \'{0}{1}\''.format(output_dir,folder))
        else:
            if template == "full":
                generate_html(os.path.join(output_dir,folder), "default", title, False)
            else:
                generate_html(os.path.join(output_dir,folder), template, title, False)

        image = None 
        i = 0
        while i < len(files):
            image = files[i]
            
            if is_image(image):
                break 
            
            i += 1

        if title is None:
            title = 'nHentai HTML Viewer'

        image_html += element.format(FOLDER=folder, IMAGE=image, TITLE=title, SUB_HTML=SUB_INDEX_HTML)

    if image_html == '':
        print('No index.html found, --gen-main paused.')
        return

    try:
        data = main.format(MAIN_TITLE=str(os.path.basename(os.path.abspath(output_dir)).replace('_', ' ')), STYLES=css, PICTURE=image_html)
        # data = main.format(STYLES=css, SCRIPTS=js, PICTURE=image_html)
        write_text(os.path.join(output_dir, MAIN_INDEX_HTML), data)
        # set_js_database(output_dir)

        print('Main Viewer has been written to \'{0}main.html\''.format(output_dir))
    except Exception as e:
        print('Writing Main Viewer failed ({})'.format(str(e)))


def main():
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
        dest="input", metavar="FOLDER",
        help="Specify input directory"
    )
    rename.add_argument(
        "-tn", "--tab-name",
        dest="tab_name", metavar="STRING",
        help="Specify the name of the tab in browser"
    )
    rename.add_argument(
        "-t", "--template",
        dest="template", metavar="minimal or default or full",
        help="Specify the html template"
    )
    rename.add_argument(
        "-v", "--view",
        dest="view", action="store_true",
        help="Display directory names as they are created"
    )

    args = parser.parse_args()
    input = args.input 
    template = args.template
    tab_name = args.tab_name

    if not input:
        print("No input specified. Exiting...")
        return 

    if not os.path.isdir(input):
        print("Input directory doesn't exist. Exiting...")
        return

    if not args.template:
        template = "default"

    if template not in ("default", "minimal", "full"):
        parser.error("Invalid template provided")
        return

    if template == "full":
        generate_main_html(input, template)
        return

    generate_html(input, template, tab_name, args.view)


if __name__ == "__main__":
    # print(os.getcwd())
    main()