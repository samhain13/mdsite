#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
from mdsite import app, helpers as h


class MDSiteHelpersTests(unittest.TestCase):
    
    def test_get_page_success(self):
        page = h.get_page(os.path.join(os.getcwd(), "markdown", "index"))
        self.assertTrue(page is not None)
        self.assertTrue(type(page) is dict)
        self.assertEqual(page["path"], "")
        page = h.get_page(os.path.join(os.getcwd(), "markdown", "page1.md"))
        self.assertEqual(page["path"] , "page1")
    
    def test_get_page_failure(self):
        # This is simply not a file in MD_FILES.
        page = h.get_page("--not--a-file")
        self.assertTrue(page is None)
        # This is an existing file outside of MD_FILES.
        page = h.get_page("../requirements.txt")
        self.assertTrue(page is None)
    
    def test_make_context(self):
        # Make sure we're writing a new _nav_cache file.
        nc = os.path.join(app.config["MD_FILES"], "_nav_cache")
        if os.path.isfile(nc):
            os.remove(nc)
        page = h.get_page(os.path.join(os.getcwd(), "markdown", "page2.md"))
        context = h.make_context(page)
        self.assertEqual(len(context["folders"]), 1)
        self.assertEqual(len(context["files"]), 3)
        self.assertEqual(context["current_index"], 1)
        self.assertEqual(context["previous_page"]["path"], "page1")
        self.assertEqual(context["next_page"]["path"], "page3")
        self.assertEqual(context["up_level"]["path"], "")
    
    def test_make_feed(self):
        # Make sure we don't have a feed.
        info, entries = h.make_feed(app.config["MD_FILES"],
            os.path.join(app.template_folder, "_atom.rss"))
        self.assertEqual(len(entries), 3)


class MDSiteTests(unittest.TestCase):
    
    def setUp(self):
        self.client = app.test_client()
    
    # ------------- Settings tests.
    def test_settings_tests(self):
        self.assertTrue(os.path.isdir(app.config["MD_FILES"]))
        self.assertTrue(os.path.isdir(app.static_folder))
        self.assertTrue(os.path.isdir(app.template_folder))
    
    # ------------- HTTP tests.
    def test_http_index(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
    
    def test_http_subsidiary_page(self):
        # We don't allow .md in the page name.
        page = self.client.get("/page1.md")
        self.assertEqual(page.status_code, 404)
        # We don't allow index pages to be accessed directly.
        page = self.client.get("/subdir/index")
        self.assertEqual(page.status_code, 302)
        # Correct requests.
        page = self.client.get("/subdir")
        self.assertEqual(page.status_code, 200)
        page = self.client.get("/page1")
        self.assertEqual(page.status_code, 200)
    
    def test_http_atom(self):
        page = self.client.get("/atom")
        self.assertEqual(page.status_code, 200)
        self.assertIn("<id>http://www.example.com/page1</id>", page.data)


if __name__ == "__main__":
    # Set app config.
    here = os.getcwd()
    app.debug = True
    app.static_folder = os.path.join(here, "static")
    app.template_folder = os.path.join(here, "templates")
    app.config.update(MD_FILES=os.path.join(here, "markdown"))
    # Here we go!
    unittest.main()

