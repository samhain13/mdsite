import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from jinja2 import Environment
from time import sleep
from .helpers import make_nav_cache, make_feed

class Commands:
    
    def _ask_to_continue(self, question):
        sys.stdout.write("** %s **\n" % question)
        return raw_input("Continue? [y/n] ").lower().startswith("y")
    
    def _check_args(self, *args):
        for i in args:
            if getattr(self.args, i) is None:
                sys.exit("This command requires a --%s value.\n" % i)
    
    def _is_series_image(self, filename):
        f, e = os.path.splitext(filename)
        if e.lower() not in [".jpg", ".png", ".gif", ".svg", ".bmp"]:
            return False
        if not f.isdigit():
            return False
        return True
    
    def _make_args_from_shell(self):
        cmds = sorted([x.replace("_", "-") for x in dir(self) \
            if x.startswith("make") or x.startswith("update")])
        ap = ArgumentParser()
        ap.add_argument("command",
            help="command must be one of: %s" % ", ".join(cmds))
        ap.add_argument("-p", "--path", help="path to markdown directory")
        ap.add_argument("-d", "--directory", help="path to resource directory")
        ap.add_argument("-t", "--title", help="title string")
        ap.add_argument("-k", "--keywords", help="keywords and key phrases")
        ap.add_argument("-l", "--limit", type=int, help="maximum items")
        ap.add_argument("-i", "--info", action="store_true",
            help="only print information about the command")
        self.args = ap.parse_args()
    
    def _make_stamps(self):
        d = datetime.utcnow()
        ts = d.strftime("%Y-%m-%dT%H:%M:%SZ")
        ds = d.strftime("%A, %d %B %Y - %H:%M:%S")
        return ts, ds
    
    def _multiline_input(self, intro, uncle):
        text = u""
        sys.stdout.write("%s: [type '%s' to quit]\n" % (intro, uncle))
        for line in iter(raw_input, uncle):
            text += line.decode("utf-8") + "\n"
        return text
    
    def main(self):
        self._make_args_from_shell()
        command = self.args.command.replace("-", "_")
        if hasattr(self, command):
            c = getattr(self, command)
            if self.args.info:
                sys.stdout.write("Information about %s:\n" % self.args.command)
                sys.stdout.write("        %s\n" % c.__doc__)
                sys.exit()
            else:
                c.__call__()
        else:
            sys.exit("Unknown command %s.\n" % command)
    
    def make_page(self):
        """Creates a new page or replaces an existing one.
        
        Requires:
            --path - path to a .md file
        """
        self._check_args("path")
        self.args.path = os.path.realpath(self.args.path)
        # Start getting more input from the user.
        if not self._ask_to_continue\
            ("This command will help you make a new page."):
            sys.exit("Goodbye.\n")
        # We need a filename at the end of our path.
        if not self.args.path.endswith(".md"):
            if not os.path.isdir(self.args.path):
                sys.exit("The directory does not exist yet.")
            filename = raw_input("Filename: [like index.md] ")
            self.args.path = os.path.join(self.args.path, filename)
        if os.path.isfile(self.args.path):
            if not self._ask_to_continue\
                ("This will overwrite an existing file."):
                sys.exit("Goodbye.")
        # What will be saved in the file.
        page = dict()
        # Because we want the keys to be in this order.
        page_keys = ("title", "description", "keywords", "template", "image",
            "thumbnail", "atom_stamp", "date", "weight", "body", )
        timestamp, datestamp = self._make_stamps()
        for k in page_keys:
            kq = u"%s: " % k.title()
            if k == "body":
                page[k] = u"Body:\n%s" % self._multiline_input("Body", "/end")
            elif k == "atom_stamp":
                page[k] = "Timestamp: %s" % timestamp
            elif k == "date":
                page[k] = "Date: %s" % datestamp
            else:
                page[k] = u"%s%s" % (kq, raw_input(kq).decode("utf-8"))
        with open(self.args.path, "w") as f:
            f.write(u"\n".join([page[x] for x in page_keys]).encode("utf-8"))
        # Update the directory's _nav_cache and the site feed.
        folders, files = \
            make_nav_cache(os.path.abspath(os.path.dirname(self.args.path)))
        sys.stdout.write("Page has been saved. Goodbye.\n")
        sys.exit()
    
    def make_series(self):
        """Creates a series of .md files based on images in static.
        
        Requires:
            --path - path to where new .md files will be saved
            --directory - path to static folder containing image series
            --title - title of the series
            --keywords - keywords and key phrases
        """
        self._check_args("path", "directory", "title", "keywords")
        mds = os.path.realpath(self.args.path)
        img = os.path.realpath(self.args.directory)
        if not os.path.isdir(mds) or not os.path.isdir(img):
            sys.exit("Path or directory does not exist.")
        imgs = sorted([x for x in os.listdir(img) if self._is_series_image(x)])
        for i in imgs:
            f, e = os.path.splitext(i)
            item_num = unicode(int(f) + 1)
            md = os.path.join(mds, "%s.md" % f)
            if not os.path.isfile(md):
                timestamp, datestamp = self._make_stamps()
                img = os.path.join(self.args.directory, i)
                thmb = os.path.join(self.args.directory, "%s-thumb%s" % (f, e))
                thumbnail = "/%s" % thmb if os.path.isfile(thmb) else ""
                page = [
                    u"Title: %s, Page %s" % (self.args.title, item_num),
                    u"Description: Page %s of %s. Created on %s." % \
                        (item_num, self.args.title, datestamp),
                    u"Keywords: %s" % self.args.keywords,
                    u"Template: ",
                    u"Image: /%s" % img,
                    u"Thumbnail: %s" % thumbnail,
                    u"Timestamp: %s" % timestamp,
                    u"Date: %s" % datestamp,
                    u"Weight: %s" % item_num,
                    u"Body: ",
                ]
                with open(md, "w") as f:
                    f.write(u"\n".join(page).encode("utf-8"))
                    sys.stdout.write("* %s saved.\n" % md)
                sleep(5)
        # Update caches.
        folders, files = make_nav_cache(mds)
        sys.exit()
    
    def update_caches(self):
        """Updates the _nav_cache files in all markdown directories.
        
        Requires:
            --path - path to the site's markdown directory
        """
        self._check_args("path")
        for dirname, subdirs, files in os.walk(self.args.path):
            if "index.md" in files:
                sys.stdout.write("* Updating _nav_cache at %s\n" % dirname)
                make_nav_cache(dirname)
        sys.stdout.write("_nav_cache files have been saved.\n")
        sys.exit()
    
    def update_feed(self):
        """Updates the website's ATOM feed.
        
        Requires:
            --path - path to the site's markdown directory
            --directory - path to the templates directory
        
        Optional:
            --limit <int> maximum number of entries to include
        """
        self._check_args("path", "directory")
        if not self.args.limit:
            self.args.limit = 25
        info, entries = make_feed(self.args.path, self.args.limit)
        # Render the template to a file.
        with open(os.path.join(self.args.directory, "_atom.rss")) as f:
            template = f.read().decode("utf-8")
        env = Environment().from_string(template)
        with open(os.path.join(self.args.directory, "atom.rss"), "w") as f:
            f.write(env.render(info=info, entries=entries).encode("utf-8"))
        sys.stdout.write("Atom feed has been updated. Goodbye.\n")
        sys.exit()
    
    def update_page(self):
        """Updates the Timestamp and Date values of a page. Use this command
        after updating a page's content in a text editor.
        
        Requires:
            --path - path to the .md file to be updated
        """
        self._check_args("path")
        if not os.path.isfile(self.args.path):
            sys.exit("File does not exist.")
        timestamp, datestamp = self._make_stamps()
        with open(self.args.path, "r+") as f:
            lines = u""
            for line in f.readlines():
                if line.startswith("Timestamp: "):
                    lines += u"Timestamp: %s\n" % timestamp
                elif line.startswith("Date: "):
                    lines += u"Date: %s\n" % datestamp
                else:
                    lines += line.decode("utf-8")
            f.seek(0)
            f.write(lines.encode("utf-8"))
            f.truncate()
        sys.stdout.write("* %s has been updated.\n" % self.args.path)
        make_nav_cache(os.path.dirname(self.args.path))
        sys.exit()

