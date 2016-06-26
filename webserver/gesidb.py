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

#this open a fudi socket for sending messages to PureData
@app.route('/pdsend/<message>', methods=['POST'])
def pdsend(message):
    mess=request.args.get('message','')
    os.system("echo '" + message + "' | pdsend 3001 localhost udp")
    return 'Alright then {}'.format(message)


#filter files by extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in (app.config['ALLOWED_EXTENSIONS'])

#get file size for limitation of sound files
def get_file_size(file):
    statinfo = os.stat(file)
    size = statinfo.st_size
    return size

#human readable file size for displaying in upload method
def humansize(nbytes):
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(app.config['SUFFIXES'])-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, app.config['SUFFIXES'][i])

#function for displaying sqlite row content into a dictionary
def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

######################################
#
# methods for accessing database
#    
######################################


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

######################################
#
# methods for sessions
#    
######################################


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


######################################
#
# methods for updating database
#    
######################################


#admin page for updating database and else
@app.route('/admin')
def admin():
    error = None
    query = 'SELECT * FROM entries'  
    db = get_db()
    #flash(gpath)
    cur = db.execute(query)
    entries = cur.fetchall()
    cur = db.execute('SELECT distinct env_title FROM density')
    envs = cur.fetchall()
    cur = db.execute('SELECT * FROM sensors')
    s = cur.fetchall()
    cur = db.execute('SELECT * FROM readsound')
    r = cur.fetchall()
    return render_template('admin.html',entries=entries,envs=envs,sensors=s,reader=r)

#read sound files in user data directory and add to database
@app.route('/update_gesi')
def update_gesi():
    entries = []
    envs    = {}
    db = get_db()
    for dirpath, dirnames, files in os.walk(app.config['SOUND_PATH']):
        for name in files:
            if name.lower().endswith(app.config['ALLOWED_EXTENSIONS']):
                filename = "/".join([dirpath ,  name])
                entry = query_db('SELECT * FROM entries WHERE filename = ?',
                [filename], one=True)
                if entry is None:
                    path = filename.split("/")
                    if len(path) > 7:
                        name = os.path.splitext(name)[0]
                        db.execute('INSERT INTO entries (filename,blacklist,\
                            samplerate,length,headersize,channels,resolution,endianness,format) VALUES (\
                            ?,?,?,?,?,?,?,?,?)',\
                            [filename,0,44100,'44100s',100,1,16,'b',1])
                        db.commit()
                        entries.append([path[5],path[6],name,filename])
                        if path[5] not in envs:
                            envs[path[5]] = []
                            envs[path[5]].append(1)
                        else:
                            if path[6] not in envs[path[5]]:
                                e = envs[path[5]][0]
                                envs[path[5]][0] = e + 1
                                envs[path[5]].append(path[6])
                                db.execute('insert into density (env_title,density,density_index) values (?,?,?)',\
                                    [path[5], path[6],e])
                                db.commit()
    for entry in entries:
     #   id = dict(sql_id)['id']
        sound_id = query_db('SELECT id FROM entries WHERE filename = ?',[entry[3]], one=True)
        db.execute('insert into wav_slice (entry_id, ram,  pitch, fine_pitch, start, stop) values (\
                ?,?,?,?,?,?)',\
                [sound_id['id'],0,60,0,'0s','44100s'])
        db.commit()
        test = query_db('SELECT id FROM wav_slice WHERE entry_id = ?',[sound_id['id']], one=True)
        sid = str(dict(test)['id'])
        #flash(str(sound_id))
        pdsend('analysis ' + sid + ' ' + str(sound_id['id']) + ' ' + ' '.join(entry) )
    pdsend('analysis done') 
    return redirect(url_for('admin'))


######################################
#
# methods for sound settings panel
#    
######################################

#get sound info
@app.route('/get_file_info', methods=['GET'])
def get_file_info():
    title = request.args.get('title')
    db = get_db()
    env = query_db('SELECT * FROM environments WHERE title = ?',[title])
 #here we put settings in temporary table
    query_db('DELETE FROM environments_temp')
    query_db('DELETE FROM wav_slice_temp')
    db.execute('INSERT INTO environments_temp SELECT * FROM environments WHERE title=?',[title])
    db.commit()
    db.execute('INSERT INTO wav_slice_temp SELECT * FROM wav_slice WHERE id=?',[env[0]['sound_id']])
    db.commit()
 #and do the query
    settings = query_db('SELECT * FROM ' + env[0]['sound_table'] + ' WHERE id = ?',[env[0]['sound_id']])
    fileinfo = query_db('SELECT * FROM (SELECT * FROM environments WHERE title = ?),\
       (SELECT * FROM ' + env[0]['sound_table'] + ' WHERE id = ?),\
        (SELECT * FROM entries WHERE id = ?)'\
        ,[title,env[0]['sound_id'],settings[0]['entry_id']], one=True)
    return jsonify(**fileinfo)

#update sound info in temp table
@app.route('/update_file_info', methods=['POST'])
def update_file_info():
    id = request.args.get('id')
    item = json.loads(request.args.get('item'))
    table = request.args.get('table')
    db = get_db()
    db.execute('UPDATE '+table+'_temp SET '+item[0]+'=? WHERE id = ?',[item[1],id])
    db.commit()
    print('id:'+id+' item:'+item[0]+' val:'+item[1])    
    return jsonify('data')

#get sound environment and densities
@app.route('/get_tree', methods=['GET'])
def get_tree():
    db = get_db()
    entries = {}
    for e in query_db('SELECT distinct env_title FROM density'):
        env = e['env_title']
        dens = []
        for d in query_db('SELECT distinct density FROM density WHERE env_title = ?',[env]):
            #print(env + ':' + d['density'])
            dens.append(d['density'])
        entries[env]=dens
    return jsonify(**entries)


#copy temp table row to table
@app.route('/save_snd', methods=['POST'])
def save_snd():
    db = get_db()
    title = request.args.get('name')
    cur = query_db('SELECT sound_table,sound_id FROM environments WHERE title = ?', [title])
    tables = ['environments',cur[0]['sound_table']]
    for table in tables:
        query  = 'UPDATE ' + table + ' SET '
        keys = query_db('PRAGMA table_info(' + table + ')')
        for k in keys:
            key = dict(k)['name']
            query += key + '=(SELECT distinct ' + key + ' FROM ' + table + '_temp),'
        query = query[:-1]
        if table == 'environments':
            query += ' WHERE title = "' + title + '"'
        else:
            query += ' WHERE id = "' + str(cur[0]['sound_id']) + '"'
        db.execute(query)
        db.commit()
    return jsonify('data')


#save from temp table to a new row
@app.route('/save_snd_as', methods=['POST'])
def save_snd_as():
    db = get_db()
    e = request.args.get('env')
    d = request.args.get('density')
    title = request.args.get('name')
    db.execute('UPDATE environments_temp SET title = ? ',[title])
    db.commit()
    cur = query_db('SELECT sound_table FROM environments_temp WHERE title = ?', [title])
    table = cur[0]['sound_table']
    query = 'INSERT INTO ' + table + ' SELECT NULL,'
    keys = query_db('PRAGMA table_info(' + table + ')')
    for k in keys:
        key = dict(k)['name']
        if key !='id':
         query += key + ','
    query = query[:-1]
    query += ' FROM ' + table + '_temp'
    db.execute(query)
    db.commit()
    sound_id = query_db('SELECT id FROM ' + table + ' ORDER BY id DESC LIMIT 1')[0]['id']
    table = 'environments' 
    test = query_db('SELECT title FROM ' + table + '_temp')[0]['title']
    if test == title:
        title += '-copy'
    db.execute('UPDATE environments_temp SET sound_id = ? ,title = ?',[sound_id,title])
    db.commit()
    table = 'environments'
    query = 'INSERT INTO ' + table + ' SELECT NULL,'
    keys = query_db('PRAGMA table_info(' + table + ')')
    for k in keys:
        key = dict(k)['name']
        if key !='id':
         query += key + ','
    query = query[:-1]
    query += ' FROM ' + table + '_temp'
    db.execute(query)
    db.commit()
# keep this commented, usefull for redirecting to def
#    return redirect(url_for('save_snd', name=n), code=307)
    return jsonify('data')


######################################
#
# methods for managing sound library
#    
######################################


#home page shows sound files database
@app.route('/', methods=['GET'])
def show_entries():
    param=dict(request.args.items())
    if param == {}:
        param={'env':'default'}
    db = get_db()
    entries = {}
    sub_id = query_db('SELECT id FROM density WHERE env_title = "' + param['env'] + '"')
    sounds = query_db('SELECT * FROM environments WHERE sub_id in (SELECT id FROM density WHERE env_title = "' + param['env'] + '")')
    path = query_db('SELECT * FROM density WHERE env_title = "' + param['env'] + '"')
    cur = db.execute('SELECT distinct env_title FROM density')
    envs = cur.fetchall()
    return render_template('show_entries.html',sounds=sounds,path=path,env=param['env'],envs=envs)

    
#ajax function re order density list in database
@app.route('/order_density', methods=['POST'])
def order_density():
    db = get_db()
    ido = json.loads(request.args.get('oldId'))
    idn = json.loads(request.args.get('newId'))
    e = request.args.get('e')
    o = [int(c) for c in ido.split(',')]
    d = []
    for i in range(0, len(idn)):
        d.append(db.execute('SELECT density FROM density WHERE (env_title = ? and density_index = ?)',[e,idn[i]]).fetchone()[0])
    for i in range(0, len(idn)):
            db.execute('update density set density_index = ? WHERE (env_title= ? and density = ?)',[i+1,e,d[i]])
            db.commit()
    return jsonify(set='set')
    
# this renders a dialog box (not used yet)
@app.route('/dialog/<method>', methods=['GET'])
def dialog(method):
    return render_template(method + '.html')


# this remove an environment (not used yet)
@app.route('/del_env/<env>', methods=['POST'])
def del_env(env):
    pdsend('deleted environment: ' + env)
    db = get_db()
    qenv = query_db('SELECT * FROM environments WHERE title = ?',[env], one=True)
    db.execute('delete FROM environments WHERE title=?',[env])
    db.commit()
    return redirect(url_for('show_entries'))

# this blacklist a sound (not used yet)
@app.route('/add_blacklist/<id>', methods=['POST'])
def add2blacklist(id):
    db = get_db()
    db.execute('update entries set blacklist = 1 WHERE  id = ?',[id])
    db.commit()
    referer = request.headers['Referer']
    env = re.search('(?<=env=)\w+', referer).group(0)
    density = re.search('(?<=density=)\w+', referer).group(0)
    pdsend(id)
    return redirect(url_for('show_entries', env=env, density=density))

@app.route('/actuators')
def actuators():
    db = get_db()
    cur = db.execute('SELECT title,\
    largo,adagio,moderato,allegro,presto,voices,outputs,\
    environments FROM readsound')
    r = cur.fetchall()
    cur = db.execute('SELECT input,send2 FROM sensors')
    s = cur.fetchall()
    env = query_db('SELECT * FROM environments')
    return render_template('actuators.html', readsound = r,
    densities = (app.config['DENSITY']),env = env,sensors = s)

######################################
#
# methods for managing actuators
#    
######################################

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

#update actuator table
@app.route('/update_data', methods=['POST'])
def update_data():
    param=dict(request.args.items())
    db = get_db()
    query =  'update '+ param['table'] + ' set ' + param['col'] + '='
    query =  query + '"' + param['data'].replace(',', ' ') + '" WHERE title="' + param['row'] + '"'
    db.execute(query)
    db.commit()
    return redirect(url_for('actuators'))

######################################
#
# methods for managing sensors
#    
######################################

@app.route('/sensors')
def sensors():
    flash('Sensors Settings')
    db = get_db()
    cur = db.execute('SELECT id,title,sensor,send2,input,window,refresh FROM sensors WHERE preset=0')
    s = cur.fetchall()
    cur = db.execute('SELECT title FROM readsound WHERE preset=0')
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

######################################
#
# upload sound file dialog
#    
######################################
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
                title = query_db('SELECT * FROM entries WHERE title = ?',
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
                    cur = query_db('SELECT id FROM entries WHERE title = ?',
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
#this run the web server, since it's on port 80, use sudo or IPTABLES for redirecting   
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)







