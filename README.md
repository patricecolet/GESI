# GESI
Gestionnaire d'Environnement Sonore Interactif
### Synopsis

GESI is composed in two parts, a python flask webserver for the interface and puredata for sound processing.
They communicate through websockets and shares a single sqlite3 database.
This project is made for running into tiny computers like pcduino or raspberry pi 3, where sensors and actuators can be connected and controlled with the GESI interactive sound manager.

## Installation (tested on GNU/linux)
### webserver
SQLITE database is used to share memory between puredata and web server running with python and flask module, so we need to install
* python-flask 
* lua-sql-sqlite3
* [pd-vanilla 0.47](http://msp.ucsd.edu/software.html)
 
flask_utils is used to simplify url notation in html templates
```
$ pip install flask_util_js

```
----
On windows use installers and start pip from admin cmd

```
C:\Program Files(x86)\Python 3.5\Scripts>py get-pip.py

```

----

### Puredata settings
install these externals with deken (Help->find external):
* pdlua
* zexy
* mrpeach
* iemlib

### Patches
Download sources:
```
$ git clone https://github.com/patricecolet/GESI.git
```

----

On windows we need to install lua-sqlite manually, download windows mingw binaries from 
[luadist.org](luadist.org), extract luadist/lib/lua/luasql folder into GESI/pdpatch, then [lsql] should access the sqlite3 dll.

----
Run web server:
 ```
$ cd GESI/webserver
$ sudo python ./gesidb.py
```
and puredata in another shell:
```
$ cd ../pdpatch
$ pd gesi-arduino.pd
```
Add console verbose mode in puredata preferences if you run into problems...

There are scripts to add to /etc/init.d for running at boot.


### Database
GESI interface runs in a web browser at localhost. The database is made by running a python script from web server,
puredata patch must be running for doing the sound analysis and complete the database.
 The folder containing sounds must be at ~/.gesi/ directory, like this:
```
~/.gesi
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
Create *.gesi* directory in */home/user* folder if it's not there, download and extract sons.zip into */home/user/.gesi/* folder.
Now we can rebuild database by accessing localhost/admin in web browser.

###TODO

add path to external in patch instead of preferences
use IPTABLES for redirecting port 80
put interface to GPIO in pure data
add virtual keyboard, mic handling and virtual pot in sensors
add sequencer, webcast in actuators





