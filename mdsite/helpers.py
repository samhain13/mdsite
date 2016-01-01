# -*- coding: utf-8 -*-
import os
import json
from markdown import markdown

def _to_int(value, on_except=0):
    try:
        v = int(value)
    except:
        v = on_except
    return v

def get_page(requested_path):
    if "./" in requested_path:
        return None
    if os.path.isdir(requested_path):
        requested_path = os.path.join(requested_path, "index")
    if not requested_path.endswith(".md"):
        requested_path += ".md"
    if not os.path.isfile(requested_path):
        return None
    # Make sure we remain in the markdown directory.
    rp = requested_path.split("markdown/")
    if len(rp) < 2:
        return None
    page = {
        "filename": unicode(os.path.realpath(requested_path)),
        "path": unicode(rp[-1]),
        "title": u"Generic, Untitled Page",
        "description": u"No description available.",
        "keywords": u"keywords, key phrases",
        "timestamp": None,
        "date": None,
        "image": None,
        "thumbnail": None,
        "template": None,
        "weight": 0,
        "body": None,
    }
    with open(page["filename"]) as f:
        for line in f.readlines():
            line = line[:-1].decode("utf-8")
            if page["body"] is not None:
                page["body"] += u"%s\n" % line
            for t in page.keys():
                tk = "%s:" % t.title()
                v = line[len(tk) + 1:]
                if line.startswith(tk) and len(line) > 1:
                    if t == "weight":
                        page[t] = _to_int(v, 0)
                    else:
                        page[t] = v
    if page["body"] is not None:
        page["body"] = markdown(page["body"])
    if page["path"].endswith("index.md"):
        page["path"] = page["path"][:0 - len("index.md")]
    if page["path"].endswith(".md"):
        page["path"] = page["path"][:0 - len(".md")]
    return page

def get_previous_next(page, files):
    previous = None
    next = None
    current_index = None
    # Makes no sense going further if we have no files or we're using index.md.
    if not files or page["filename"].endswith("index.md"):
        return previous, next, current_index
    current_index = files.index([x for x in files \
        if x["filename"] == page["filename"]][0])
    if current_index > 0: 
        previous = files[current_index - 1] 
    if (current_index + 1) < len(files):
        next = files[current_index + 1]
    return previous, next, current_index

def get_up_level(page):
    if page["filename"].endswith("index.md"):
        d = os.path.realpath(os.path.dirname(os.path.dirname(page["filename"])))
    else:
        d = os.path.realpath(os.path.dirname(page["filename"]))
    df = os.path.join(d, "index.md")
    if os.path.isfile(df):
        return get_page(os.path.join(d, "index"))
    return None

def make_feed(markdowns, atom_template, limit=20):
    # Get some info from the main index page.
    index_page = get_page(os.path.join(markdowns, "index"))
    # Pages will be the atom entries.
    pages = []
    for dirname, subdirs, files in os.walk(markdowns):
        if "_nav_cache" in files:
            with open(os.path.join(dirname, "_nav_cache")) as f:
                data = json.loads(f.read())
                pages += data["files"]
    # Sort the pages according to creation date and trim the list.
    pages = sorted(pages, key=lambda x:x["timestamp"], reverse=True)[:limit]
    if pages:  # Update the index_page information for the feed.
        if pages[0]["timestamp"] and pages[0]["date"]:
            index_page["timestamp"] = pages[0]["timestamp"]
            index_page["date"] = pages[0]["date"]
    return index_page, pages

def make_404():
    return "404 Not Found", 404, {"content-type": "text-plain"}

def make_500():
    return "500 Internal Server Error", 500, {"content-type": "text-plain"}

def make_context(page):
    c = dict()
    path = os.path.dirname(page["filename"])
    c["page"] = page
    c["folders"], c["files"] = make_nav(path)
    c["previous_page"], c["next_page"], c["current_index"] = \
        get_previous_next(page, c["files"])
    c["up_level"] = get_up_level(page)
    return c

def make_nav(path):
    # Do nothing if we already have a nav_cache.
    nav_cache = os.path.join(path, "_nav_cache")
    if os.path.isfile(nav_cache):
        with open(nav_cache) as f:
            data = json.loads(f.read())
            return data["folders"], data["files"]
    return make_nav_cache(path)

def make_nav_cache(path):
    folders = []
    files = []
    for x in os.listdir(path):
        xp = os.path.join(path, x)
        info = None
        list_ = None
        if os.path.isdir(xp):
            info = get_page(os.path.join(xp, "index.md"))
            list_ = folders
        elif os.path.isfile(xp):
            if not x.startswith("_") and x.endswith(".md") and x != "index.md":
                info = get_page(os.path.join(path, x))
                list_ = files
        if info is not None and list_ is not None:
            del info["body"]
            del info["template"]
            list_.append(info)
    # Sort the folders and files according to weight, title, and path.
    folders.sort(key=lambda x: (x["weight"], x["title"], x["path"]))
    files.sort(key=lambda x: (x["weight"], x["title"], x["path"]))
    with open(os.path.join(path, "_nav_cache"), "w") as f:
        data = {"folders": folders, "files": files}
        f.write(json.dumps(data))
    return folders, files

