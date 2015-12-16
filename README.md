# GESI
##Gestionnaire d'Environnement Sonore Interactif

###Installation

tested on linux

A sqlite database is used to share memory between puredata and web server running with python and flask module, so we need to install
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

GESI interface runs in a web browser at localhost. The database is made by running update python script in web browser,
but the folder containing sounds must be at GESI root directory, like this:

gesi
-/**sons**
--/[environment1]
---/**largo**
----/[sound01.wav]
----/[sound02.wav]
----/...
---/**adagio**
----/[sound101.wav]
----/...
---/**moderato**
---/**allegro**
---/**presto**
--/[environment2]
---/**largo**
---/...
--/[environment3]
--/...

an archive containing samples is here: http://megalego.free.fr/gesi/sons.zip
create *gesi/sons* folder if it's not there, download and extract sons.zip into *sons* folder.

Now we can rebuild database by accessing localhost/update in web browser, after a few minutes...






