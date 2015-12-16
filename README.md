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
* mrpeach
* mediasettings

in puredata Edit->Preference->Startup add *pdlua zexy* and in Edit->Preference->Path add *~/pd-externals/mrpeach ~/pd-externals/mediasettings ~/pd-externals/ggee*

get scripts and patch, run web server
```
$ cd webserver
$ git clone https://github.com/patricecolet/GESI.git
$ cd GESI/webserver
$ sudo python ./gesidb.py &
```
, and puredata in another shell
```
$ cd GESI/pdpatch
$ pd gesi-arduino.pd &
```








