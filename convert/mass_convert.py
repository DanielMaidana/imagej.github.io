import os
import markdown_link_extractor
from ij_mw_preprocess_debo import *
import re
from shutil import copyfile


converted_pages = []
converted_media = []
missing_pages = []
missing_media = []


def delete_autogenerated_media():
    media_dir = images_dir(root_out)
    for filename in os.listdir(media_dir):
        file = os.path.join(media_dir, filename)
        os.remove(file)


def images_dir():
    return os.path.join(os.path.join(root_out, "images"), "pages")


def catch_media(path_in, root_out):
    content = read_file(path_in)
    pattern = re.compile(r'\[\[File\:([^ |]*)[ ]*\|[ ]*[^ |]*[ ]*\|[ ]*link=[^\]]*[ ]*\]\]')
    for (file_name) in re.findall(pattern, content):
        copy_media(file_name, path_in, root_out)
    pattern = re.compile(r'\[\[Image:([^\|\]]*)[^\]]*\]\]')
    for (file_name) in re.findall(pattern, content):
        copy_media(file_name, path_in, root_out)


def copy_media(file_name, path_in, root_out):
    file_out = os.path.join(root_out, file_name)
    file_in = os.path.join(os.path.dirname(path_in), file_name)
    if not os.path.exists(file_in):
        if file_name not in missing_media:
            missing_media.append(file_name)
        print("Could not find media " + file_in)
        return
    converted_media.append(file_name)
    if os.path.exists(file_out):
        return
    print("Copying " + file_name)
    copyfile(file_in, file_out)


def delete_autogenerated_pages():
    pages_dir = os.path.join(root_out, "pages")
    for filename in os.listdir(pages_dir):
        if filename.endswith(".md"):
            file = os.path.join(pages_dir, filename)
            with open(file, 'r') as f:
                lines = f.readlines()
                if lines[1] == autogenerated_line:
                    print("Deleting " + file)
                    os.remove(file)


def _convert(page_title, recursive=False):
    layout = "page"
    metapage = False
    title = page_title
    if "#" in page_title:
        parts = page_title.split("#", 1)
        if parts[0].strip():
            _convert(parts[0], recursive)
        return
    if "(" in page_title:
        print("Cannot process names with parentheses: " + page_title)
        return
    if ":" in page_title:
        if "Special:" in page_title:
            # print("Cannot create mediawiki special pages")
            return
        if "File:" in page_title:
            return
        if "Template:" in page_title:
            return
        if "Category:" in page_title:
            layout = "category"
            metapage = True
            page_title = page_title.replace(":Category:", "Category:")
            title = page_title.replace("Category:", "")
        else:
            print("Cannot convert pages with colon in title: " + page_title)
            return
    if page_title in [i[0].strip() for i in blacklist]:
        print("Cannot process, blacklisted: " + page_title)
        return
    path_in = None
    mw_title = page_title + ".mw"
    if not metapage:
        path_in = os.path.join(root_in, mw_title)
        if not os.path.exists(path_in):
            if mw_title not in missing_pages:
                missing_pages.append(mw_title)
            # print("Could not find " + page_title)
            return
        title = get_title(path_in)
        catch_media(path_in, images_dir())
    path_out = os.path.join(os.path.join(root_out, "pages"), page_title + ".md")
    if os.path.exists(path_out):
        return
    convert(path_in, path_out, layout, title)
    converted_pages.append(mw_title)
    if recursive:
        convert_links(path_out)


def convert_links(path_out):
    output = read_file(path_out)
    links = markdown_link_extractor.getlinks(output)
    for link in links:
        if link.startswith("http"):
            continue
        if link.startswith("wikipedia"):
            continue
        _convert(link, True)


def convert_all():
    for filename in os.listdir(root_in):
        if filename.endswith(".mw"):
            title = filename.replace(".mw", "")
            # print("trying to convert " + title + "...")
            _convert(title, recursive=True)


def load_blacklist(blacklist_path):
    path = os.path.join(root_out, blacklist_path)
    with open(path) as f:
        return [line.rstrip('\n').split(",") for line in f.readlines()]


def get_unused_pages():
    res = []
    for filename in os.listdir(root_in):
        if filename.endswith(".mw"):
            if filename not in converted_pages:
                res.append(filename)
    return res


def get_unused_media():
    res = []
    for filename in os.listdir(root_in):
        if not filename.endswith(".mw"):
            title = os.path.splitext(filename)[0]
            if title not in converted_pages:
                res.append(filename)
    return res


def save_status():
    write_list(converted_pages, converted_pages_path)
    write_list(converted_media, converted_media_path)
    write_list(missing_pages, missing_pages_path)
    write_list(missing_media, missing_media_path)
    write_list(get_unused_pages(), unused_pages_path)
    write_list(get_unused_media(), unused_media_path)


def write_list(list, path):
    list.sort()
    with open(os.path.join(root_out, path), "w") as txt_file:
        for line in list:
            txt_file.write(line + "\n")


root_in = "/home/random/Development/imagej/imagej/imagej-net-temp/"
root_out = "/home/random/Development/imagej/imagej/imagej.github.io/"
blacklist_path = "convert/status/blacklisted-pages.csv"
converted_media_path = "convert/status/converted_media.csv"
converted_pages_path = "convert/status/converted_pages.csv"
missing_pages_path = "convert/status/missing_pages.csv"
missing_media_path = "convert/status/missing_media.csv"
unused_pages_path = "convert/status/unused_pages.csv"
unused_media_path = "convert/status/unused_media.csv"

blacklist = load_blacklist(blacklist_path)
delete_autogenerated_pages()
# _convert("Development", blacklist, recursive=True)
# _convert("News", blacklist, recursive=True)
# _convert("Introduction", blacklist, recursive=True)
# _convert("Upcoming_Events", blacklist, recursive=True)
# _convert("Help", blacklist, recursive=True)
convert_all()
save_status()
