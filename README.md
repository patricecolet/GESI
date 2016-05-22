# GESI
Gestionnaire d'Environnement Sonore Interactif
## Installation (GNU/linux only)
### webserver
SQLITE database is used to share memory between puredata and web server running with python and flask module, so we need to install
* python-flask 
* lua-sql-sqlite3
* [pd-vanilla ](https://puredata.info/downloads/pure-data)
 
flask_utils is used to simplify url notation in html templates
```
$ pip install flask_util_js

```
### Puredata settings
install  these externals with [deken](https://github.com/pure-data/deken):
* pdlua
* zexy
* ggee
* mrpeach
* mediasettings

in puredata Edit->Preference->Startup add *pdlua zexy* and in Edit->Preference->Path add *~/pd-externals/mrpeach ~/pd-externals/mediasettings ~/pd-externals/ggee*
### Patches
Download sources:
```
$ git clone https://github.com/patricecolet/GESI.git
```
Run web server:
 ```
$ cd GESI/webserver
$ sudo python ./gesidb.py &
```
and puredata in another shell.
```
$ cd GESI/pdpatch
$ pd gesi-arduino.pd &
```
### Database
GESI interface runs in a web browser at localhost. The database is made by running a python script from web server,
the folder containing sounds must be at GESI root directory, like this:
```
-/gesidb
-/pdpatch
-/sons
--/[environment1]
---/largo
----/[sound01.wav]
----/[sound02.wav]
----/...
---/adagio
----/[sound101.wav]
----/...
---/moderato
---/allegro
---/presto
--/[environment2]
---/largo
---/...
--/[environment3]
--/...
```
An archive containing samples is here: http://megalego.free.fr/gesi/sons.zip.
Create *gesi/sons* folder if it's not there, download and extract sons.zip into *sons* folder.
Now we can rebuild database by accessing localhost/update_gesi in web browser.






