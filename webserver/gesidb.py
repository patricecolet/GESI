#! /usr/bin/env python
import os
#import fnmatch
import sqlite3
import json
import re
from flask import Flask, request, g, redirect, url_for, abort, \
     render_template, flash, jsonify, send_from_directory, session

#from werkzeug.utils import secure_filename
from flask_util_js import FlaskUtilJs



# create flask application :)
app = Flask(__name__)
app.config.from_object(__name__)

fujs = FlaskUtilJs(app)

@app.context_processor
def inject_fujs():
    return dict(fujs=fujs)

# get user home path where resides .gesi data folder
user = os.getenv("SUDO_USER")
home =  '/home/' + user
gpath = os.path.dirname(home + '/.gesi/')

# Load default config and override config from an environment variable
app.config.update(dict(
    SOUND_PATH=         gpath + '/sons',
    SOUND_UPLOAD=       gpath + '/sons/uploads',
    DATABASE=           gpath + '/gesidb.db',
    DEBUG=              True,
    SECRET_KEY=         'development key',
    USERNAME=           'gesi',
    PASSWORD=           '6351',
    DENSITY=            ['largo','adagio','moderato','allegro','presto'],
    ALLOWED_EXTENSIONS= tuple(['wav', 'aif','WAV','AIF']),
    SUFFIXES=           ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
))


app.config.from_envvar('FLASKR_SETTINGS', silent=True)

#filter files by extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in (app.config['ALLOWED_EXTENSIONS'])

def get_file_size(file):
    statinfo = os.stat(file)
    size = statinfo.st_size
    return size


def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(app.config['SUFFIXES'])-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, app.config['SUFFIXES'][i])

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def query_db_one(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchone()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource(app.config['DATABASE'], mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

#admin page for updating database and else
@app.route('/admin')
def admin():
    error = None
    query = 'select * from entries'  
    db = get_db()
    #flash(gpath)
    cur = db.execute(query)
    entries = cur.fetchall()
    cur = db.execute('select distinct title from environments')
    envs = cur.fetchall()
    cur = db.execute('select * from sensors')
    s = cur.fetchall()
    cur = db.execute('select * from readsound')
    r = cur.fetchall()
    return render_template('admin.html',entries=entries,envs=envs,sensors=s,reader=r)

#read sound files in user data directory and add to database
@app.route('/update_gesi')
def update_gesi():
    entries = []
    db = get_db()
    for dirpath, dirnames, files in os.walk(app.config['SOUND_PATH']):
        for name in files:
            if name.lower().endswith(app.config['ALLOWED_EXTENSIONS']):
                title = query_db('select * from entries where title = ?',
                [name], one=True)
                if title is None:
                    filename = "/".join([dirpath ,  name])
                    path = filename.split("/")
                    if len(path) > 7:
                        name = os.path.splitext(name)[0]
                        db.execute('insert into entries (title,filename,blacklist,\
                            samplerate,length,headersize,channels,resolution,endianness,format) values (\
                            ?,?,?,?,?,?,?,?,?,?)',\
                            [name, filename,0,44100,44100,100,1,16,'b',1])
                        db.commit()
                        entries.append([path[5],path[6],filename])
    for entry in entries:
     #   id = dict(sql_id)['id']
        sound_id = query_db('select id from entries where filename = ?',[entry[2]], one=True)
        sid = str(dict(sound_id)['id'])
        #flash(str(sound_id))
        pdsend('analysis ' + sid + ' ' +' '.join(entry) )
    pdsend('analysis done')          
    return redirect(url_for('admin'))

#update database
@app.route('/update_data', methods=['POST'])
def update_data():
    param=dict(request.args.items())
    db = get_db()
    query =  'update '+ param['table'] + ' set ' + param['col'] + '='
    query =  query + '"' + param['data'].replace(',', ' ') + '" where title="' + param['row'] + '"'
    db.execute(query)
    db.commit()
    return redirect(url_for('actuators'))


#get sound info
@app.route('/get_file_info', methods=['GET'])
def get_file_info():
    title = request.args.get('title')
    pdsend('test '+ title )
    db = get_db()
    fileinfo = query_db('select * from (select * from entries where title = ?),\
        (select * from environments where sound_id in (select id from entries where title = ?))'\
        ,[title,title], one=True)
    id = str(dict(fileinfo)['id'])
    pdsend('test2 '+ id) 
    return jsonify(fileinfo)

#get sound environment and densities
@app.route('/get_tree', methods=['GET'])
def get_tree():
    db = get_db()
    fileinfo = query_db('select * from \
        (select distinct title from environments),\
        (select distinct density from environments where title in \
        (select distinct title from environments))')
    id = str(dict(fileinfo))
    pdsend('test2 '+ id) 

    return jsonify(fileinfo)




#home page shows sound files database
@app.route('/', methods=['GET'])
def show_entries():
#    pdsend('test')
    param=dict(request.args.items())
    #flash(param)
    if param == {}:
        param={'env':'default','density':'largo'}
    query = 'from environments where title = "' + param['env'] + '" and density= "' + param['density']+ '"'
    db = get_db()
    cur = db.execute('select * from entries where id in (select sound_id ' + query + ')')
    ent = cur.fetchall()
    cur = db.execute('select * ' + query)
    real = cur.fetchall()
    cur = db.execute('select distinct title from environments')
    envs = cur.fetchall()
    cur = db.execute('select distinct density from environments where title="'+ param['env'] +'"')
    dens = cur.fetchall()
    filenum = db.execute('select count()  from environments where title="'+ param['env'] +'"').fetchone()
    D = []
    for d in dens:
        cur = db.execute('select count(*) from environments where title="' + param['env'] + '" and density= "' + d[0] + '"')
        dn = cur.fetchone()
        dnp = dn[0]*100/filenum[0]
        D.append([dnp,d[0]])
    return render_template('show_entries.html',entries=ent,real=real, env=param['env'],densities=D,envs=envs,density=param['density'])
    
#renders a dialog box
@app.route('/dialog/<method>', methods=['GET'])
def dialog(method):
    return render_template(method + '.html')


@app.route('/del_env/<env>', methods=['POST'])
def del_env(env):
    pdsend('deleted environment: ' + env)
    db = get_db()
    qenv = query_db('select * from environments where title = ?',[env], one=True)
    db.execute('delete from environments where title=?',[env])
    db.commit()
    return redirect(url_for('show_entries'))



@app.route('/add_blacklist/<id>', methods=['POST'])
def add2blacklist(id):
    db = get_db()
    db.execute('update entries set blacklist = 1 where  id = ?',
                 [id])
    db.commit()
    referer = request.headers['Referer']
    env = re.search('(?<=env=)\w+', referer).group(0)
    density = re.search('(?<=density=)\w+', referer).group(0)
    pdsend(id)

    return redirect(url_for('show_entries', env=env, density=density))

@app.route('/actuators')
def actuators():
    db = get_db()
    cur = db.execute('select title,\
    largo,adagio,moderato,allegro,presto,voices,outputs,\
    environments from readsound')
    r = cur.fetchall()
    cur = db.execute('select input,send2 from sensors')
    s = cur.fetchall()
    env = query_db('select * from environments')
    return render_template('actuators.html', readsound = r,
    densities = (app.config['DENSITY']),env = env,sensors = s)

@app.route('/add_actuator/<actuator>',methods=['POST'])
def add_actuator(actuator):
    db = get_db()
    cursor = db.execute('SELECT max(id) FROM readsound')
    cnt = cursor.fetchone()[0]
    db.execute('insert into readsound (preset,\
    title,largo,adagio,moderato,allegro,presto,\
    voices,outputs,environments) values (?,?,?,?,?,?,?,?,?,?)',\
    [0,'readsound'+ str(cnt),20,40,50,60,80,0,'1 2','default'])
    db.commit()
    return redirect(url_for('actuators'))

@app.route('/del_actuator/<name>',methods=['POST'])
def del_actuator(name):
    db = get_db()
    pdsend('test: ' + name)
    db.execute('DELETE FROM readsound WHERE title=?',[name])
    db.commit()
    return redirect(url_for('actuators'))

@app.route('/sensors')
def sensors():
    flash('Sensors Settings')
    db = get_db()
    cur = db.execute('select id,title,sensor,send2,input,window,refresh from sensors where preset=0')
    s = cur.fetchall()
    cur = db.execute('select title from readsound where preset=0')
    r = cur.fetchall()
    #pdsend('test ' + str(a))
    return render_template('sensors.html', sensors = s, readsound = r)



@app.route('/del_sensor/<name>',methods=['POST'])
def del_sensor(name):
    db = get_db()
    pdsend('test: ' + name)
    db.execute('DELETE FROM sensors WHERE title=?',[name])
    db.commit()
    return redirect(url_for('sensors'))


@app.route('/add_sensor/<sensor>',methods=['POST'])
def add_sensor(sensor):
    db = get_db()
    cursor = db.execute('SELECT max(id) FROM sensors')
    cnt = cursor.fetchone()[0]
    db.execute('insert into sensors (preset,\
    title,sensor,send2,input,window,refresh) values (?,?,?,?,?,?,?)',\
    [0,'sensor'+ str(cnt),sensor,'None','None',25,100])
    db.commit()
    return redirect(url_for('sensors'))


@app.route('/pdsend/<message>', methods=['POST'])
def pdsend(message):
    mess=request.args.get('message','')
    os.system("echo '" + message + "' | pdsend 3001 localhost udp")
    return 'Alright then {}'.format(message)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        sound_id = []
        referer = request.headers['Referer']
        pdsend(str(request.files.getlist('file')))
        env = re.search('(?<=env=)\w+', referer).group(0)
        density = re.search('(?<=density=)\w+', referer).group(0)
        for file in request.files.getlist('file'):
           if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                title = query_db('select * from entries where title = ?',
                [filename], one=True)
                if title is None:
                    file_url = os.path.join(app.config['SOUND_UPLOAD'], filename)
                    file.save(file_url)
                    file_size = get_file_size(file_url)
                    param=dict(request.args.items())
                    name = os.path.splitext(os.path.basename(filename))[0]
                    db = get_db()
                    db.execute('insert into entries (title,filename,blacklist,\
                            samplerate,length,headersize,channels,resolution,endianness,format) values (\
                            ?,?,?,?,?,?,?,?,?,?)',\
                            [name, filename,0,44100,44100,100,1,16,'b',1])
                    db.commit()
                    cur = query_db('select id from entries where title = ?',
                        [filename], one=True)
                    id = dict(cur)['id']
                    pdsend('analysis ' + str(id))
                    pdsend('TEST:' + str(id))
                    pdsend('analysis done')
 
                    json_data = jsonify({ 
  'files':
    [
      {
        'url': file_url,
        'thumbnail_url': "http://url.to/thumnail.jpg ",
        'name': filename,
        'type': "audio/wav",
        'size': file_size,
        'delete_url': "http://url.to/delete /file/",
        'delete_type': "DELETE"
      }
    ]
})           
                    return json_data                    
                else:
                    pdsend('error:' + filename + 'exist')
                    json_data = jsonify({ 
  'files':
    [
      {
        'name': filename,
        "error": "File exist"
      }
    ]
})  

                    return json_data    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)







