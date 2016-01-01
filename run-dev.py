#! /usr/bin/env python
import os
from mdsite import app


if __name__ == "__main__":
    # Set app config.
    here = os.getcwd()
    app.debug = True
    app.static_folder = os.path.join(here, "static")
    app.template_folder = os.path.join(here, "templates")
    app.config.update(MD_FILES=os.path.join(here, "markdown"))
    app.run()
