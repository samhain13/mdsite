# -*- coding: utf-8 -*-
import os
from flask import Flask, redirect, render_template, url_for
from jinja2 import TemplateNotFound
from .helpers import get_page, make_context, make_feed, make_404, make_500

def respond(context):
    try:
        t = render_template(context["page"]["template"], **context)
    except TemplateNotFound:
        t = render_template("_failsafe.html", **context)
    except:
        t = make_500()
    return t

app = Flask("mdsite")

@app.route("/")
def index():
    page = get_page(os.path.join(app.config["MD_FILES"], "index"))
    if page is None:
        return make_404()
    context = make_context(page)
    return respond(context)

@app.route("/<path:sub_path>")
def subsidiary_page(sub_path):
    if sub_path.endswith(".md"):
        return make_404()
    if sub_path.endswith("index"):
        return redirect(url_for("subsidiary_page",
            sub_path=sub_path[:(0 - len("index"))]))
    page = get_page(os.path.join(app.config["MD_FILES"], sub_path))
    if page is None:
        return make_404()
    context = make_context(page)
    return respond(context)

@app.route("/atom")
def atom_feed():
    #info, entries = make_feed(app.config["MD_FILES"],
    #    app.config.get("MD_ATOM_ITEMS", 20))
    #return render_template("_atom.rss", info=info, entries=entries), 200, \
    #    {"content-type": "application/atom+xml; coding=utf-8"}
    try:
        atom = render_template("atom.rss")
        return atom, 200, {"content-type": "application/atom+xml; coding=utf-8"}
    except:
        return make_404()


