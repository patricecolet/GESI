### GESI
##Gestionnaire d'Environnement Sonore Interactif

#GESI Framework

get Puredata

https://puredata.info/downloads/pure-data

install recent version and keep a track of m_pd.h and s_stuff.h 
to compile externals

pdlua is necessary to edit sqlite files

get pdlua sources:
https://puredata.info/downloads/pdlua
compile pdlua:
```
$ tar -xvf pdlua-0.6.tar-gz
$ cd pdlua/src
$ make
```
if there are complains about threepic, remove it from Makefile,
if it doesn't find s_stuff.h, copy it to src folder:
```
cp  /usr/local/include/pd/*.h .
```
This should be installed in /home/pd-externals, if it doesn't exist create it *$ mdir ~/pd-externals*, 
and put pdlua.pd_linux in it.

Open puredata and go to preférences-->path and add ~/pd-external dir
close puredata, copy pdlua external:

```
cp pdlua.pd_linux ~/pd-externals/
```



