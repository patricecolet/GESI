# GESI
Gestionnaire d'Environnement Sonore Interactif
## Installation (GNU/linux only)
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

in puredata Edit->Preference->Startup add *pdlua* and in Edit->Preference->Path add *~/pd-externals/mrpeach ~/pd-externals/iemlib ~/pd-externals/zexy*
### Patches
Download sources:
```
$ git clone https://github.com/patricecolet/GESI.git
```

----

On windows we need to install lua-sqlite manually, download windows binaries from 
[luadist.org](luadist.org), extract tree to C:\lua53, add c:\lua53\bin to [PATH environment variable](http://superuser.com/questions/284342/what-are-path-and-other-environment-variables-and-how-can-i-set-or-use-them), and add c:\lua53\lib\lua\luasqlite folder to puredata path in preferences.

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

### Database
GESI interface runs in a web browser at localhost. The database is made by running a python script from web server,
the folder containing sounds must be at ~/.gesi/ directory, like this:
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
Now we can rebuild database by accessing localhost/update_gesi in web browser.

###TODO
start pd instance from web gui
replace python with puredata server instance, and jinja with lua html template
add virtual keyboard, mic handling and virtual pot in sensors
add sequencer, webcast in actuators





