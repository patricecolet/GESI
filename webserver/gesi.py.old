import os
import fnmatch
import sqlite3
import json
import re

from flask import Flask, request, g, redirect, url_for, abort, \
     render_template, flash, jsonify, send_from_directory

from werkzeug.utils import secure_filename
from flask_util_js import FlaskUtilJs


# create our little application :)
app = Flask(__name__)

fujs = FlaskUtilJs(app)


@app.context_processor
def inject_fujs():
    return dict(fujs=fujs)

app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    SOUND_PATH='/media/sdext/sons',
    SOUND_UPLOAD='/media/sdext/sons/uploads',
    DATABASE=os.path.join(app.root_path, 'gesidb.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='gesi',
    PASSWORD='6351',
    DENSITY=['largo','adagio','moderato','allegro','presto'],
    ALLOWED_EXTENSIONS= set(['wav', 'aif','WAV','AIF']),
    SUFFIXES= ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
))


app.config.from_envvar('FLASKR_SETTINGS', silent=True)

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
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.route('/update')
def update_db():
    sound_id = []
    db = get_db()
    for dirpath, dirnames, files in os.walk(app.config['SOUND_PATH']):
        for name in files:
            if name.lower().endswith('wav'):
                title = query_db('select * from entries where title = ?',
                [name], one=True)
                if title is None:
                    filename = "/".join([dirpath ,  name])
                    path = filename.split("/")
                    if len(path) > 6:
                        env = query_db('select * from environments where title = ?',
                           [path[4]], one=True)
                        if env is None:
                            db.execute('insert into environments (title) values (?)',
                               [path[4]])
                        db.execute('insert into entries (title,env, density,\
                            filename,blacklist) values (?, ?, ?, ?, ?)',\
                            [name, path[4], path[5], filename,0])
                        db.commit()
                else:
                
                    cur = query_db('select id from entries where title = ?',
                        [name], one=True)
                    id = dict(cur)['id']
                    test = query_db('select * from entries where title = ?',
                       [id], one=True)
                    if test is None:

                        sound_id.append(id)

    for id in sound_id:
        pdsend('analysis ' + str(id))
    pdsend('analysis done')          
    return redirect(url_for('show_entries'))


@app.route('/analysis/<id>')
def analysis(id):
    db = get_db()


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()



#@app.route('/<param>', methods=['GET'])
@app.route('/', methods=['GET'])
def show_entries():
    pdsend('test')
    param=dict(request.args.items())
    #flash(param)
    if param == {}:
        param={'env':'default','density':'largo'}
    query =  'select id, title, env, density from entries where blacklist = 0'
    query = query + ' and env = "' + param['env'] + '"'
    query = query + ' and density= "' + param['density']+ '"'  
    db = get_db()
    cur = db.execute(query)
    entries = cur.fetchall()
    cur = db.execute('select title from environments')
    envs = cur.fetchall()
    return render_template('show_entries.html', entries=entries, env=param['env'],density=param['density'], envs = envs, densities=(app.config['DENSITY']))

@app.route('/add_blacklist', methods=['POST'])
def add2blacklist():
    db = get_db()
    db.execute('update entries set blacklist = 1 where  filename = ?',
                 [request.form['filename']])
    db.commit()
    referer = request.headers['Referer']
    env = re.search('(?<=env=)\w+', referer).group(0)
    density = re.search('(?<=density=)\w+', referer).group(0)
    return redirect(url_for('show_entries', env=env, density=density))

@app.route('/sound_info', methods=['GET'])
def sound_info():
    id = request.args.get('id')
    con = sqlite3.connect(app.config['DATABASE'])
    con.row_factory = dict_factory
    cur = con.cursor()
    q = cur.execute('select samplerate, length, channels from sound_info where sound_id =?', [id])
    info = q.fetchone()
    #pdsend(str(info))
    return jsonify(info=info, id=id)
"""
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

"""
@app.route('/pdsend/<message>', methods=['POST'])
def pdsend(message):
    mess=request.args.get('message','')
    os.system("echo '" + message + "' | pdsend 3001 127.0.0.1 udp")
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
                    db = get_db()
                    db.execute('insert into entries (title,env, density,\
                            filename,blacklist) values (?, ?, ?, ?, ?)',\
                            [filename, env, density, file_url,0])
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







