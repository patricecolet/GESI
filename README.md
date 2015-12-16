# GESI
##Gestionnaire d'Environnement Sonore Interactif

###Installation

tested on linux

A sqlite database is used to share memory between puredata and web server, and the web server is running with python and flask module, so we need to install
* python-flask 
* lua51-sql-sqlite3
* [puredata](https://puredata.info/downloads/pure-data)

we use flask_utils to simplify url notation in html templates
```
$ git clone https://github.com/dantezhu/flask_util_js.git
$ cd flask_util_js/
$ sudo python setup.py install
```

install  these puredata externals with [deken](https://github.com/pure-data/deken):
* pdlua
* zexy
* ggee

don't forget to enable externals in puredata File->Preference->Startup

This archive contains everything else








