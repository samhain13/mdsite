# mdsite
A Flask application that serves up markdown files.

## Requirements
* Flask>=0.10.1
* Markdown>=2.6.5

## First use
1. Run tests.py
2. Run run-commands.py <command> -i to see command requirements. Available commands are make-page, make-series, update-caches, update-feed, update-page.
3. Run run.dev.py to serve on localhost:5000

## Setting up a site/instance
1. create empty “markdown” and “static” directories
2. copy the “templates” directory
3. copy run-command.py and run-dev.py
4. add *sys.path.insert(0, "/path/to/mdsite")* in both run- files if necessary
