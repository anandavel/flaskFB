import os
from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, hashlib
import requests


app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'MP4', 'MOV', 'AVI', 'MPEG', '3gp', 'DivX', 'f4v'}
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskdb'
mysql = MySQL(app)

PAGE_ACCESS_TOKEN = 'your_page_access_token'
PAGE_ID = 'your_page_id'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
def allowed_filevideo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_VIDEO_EXTENSIONS']
@app.route('/')
def index():
    return render_template('login.html')
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('dashboard'))
        msg = "Invalid username or password"
        return render_template('login.html', msg=msg)
    return redirect(request.url)
@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('index'))
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))        
@app.route('/facebookphoto')
def facebookphoto():
    return render_template('photo.html')

@app.route('/facebookphoto/upload', methods=['POST'])
def upload_filephoto():
    if 'file' not in request.files:
        flash('Facebook Page upload files not exist', 'warning')
        return render_template('photo.html')
    file = request.files['file']
    content = request.form.get('content')
    if file.filename == '':
        flash('Facebook Page upload files not exist', 'warning')
        return render_template('photo.html')
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        post_photo_to_facebook(filepath, content)
        flash('Post submitted successfully!', 'success')
        
    return redirect(url_for('facebookphoto'))

def post_photo_to_facebook(photo_path, caption):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM facebook WHERE status=0')
    fbdata = cursor.fetchall()
    for fbapi in fbdata:
        pageid = fbapi['pageid']
        pageasscesstoken = fbapi['pageaccesstoken']
        url = f"https://graph.facebook.com/{pageid}/photos"
        payload = {
            'caption': caption,
            'access_token': pageasscesstoken
        }
        files = {
            'source': open(photo_path, 'rb')
        }
        response = requests.post(url, data=payload, files=files)
    
    return response.json()
#videos post to facebook
@app.route('/facebookvideo')
def facebookvideo():
    return render_template('video.html')

@app.route('/facebookvideo/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Facebook Page upload files not exist', 'warning')
        return render_template('video.html')
    file = request.files['file']
    content = request.form.get('content')
    if file.filename == '':
        flash('Facebook Page upload files not exist', 'warning')
        return render_template('video.html')
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    post_video_to_facebook(filepath, content)
    flash('Post submitted successfully!', 'success')
    return redirect(url_for('facebookvideo'))

def post_video_to_facebook(video_path, content):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM facebook WHERE status=0')
    fbdata = cursor.fetchall()
    for fbapi in fbdata:
        pageid = fbapi['pageid']
        pageasscesstoken = fbapi['pageaccesstoken']
        url = f"https://graph.facebook.com/{pageid}/videos"
        payload = {
            'access_token': pageasscesstoken,
            'message': content
        }
        files = {
            'source': open(video_path, 'rb')
        }
        response = requests.post(url, data=payload, files=files)
    
    return response.json()
@app.route('/fbprofile')
def fbprofile():
     return render_template('fbprofile.html')
@app.route('/fbprofile/upload', methods=['POST'])
def fbprofileupdate():
    if request.method == 'POST' and 'name' in request.form and 'fbpid' in request.form:
        name = request.form.get('name')
        fbpid = request.form.get('fbpid')
        fbpat = request.form.get('fbpat')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = "INSERT INTO facebook (pageid, pageaccesstoken, pagename) VALUES (%s, %s, %s)"
        values = (fbpid, fbpat, name)
        cursor.execute(query, values)
        mysql.connection.commit()
        flash('Facebook page submitted successfully!', 'success')
        return redirect(url_for('fbprofile'))
    flash('Please enter facebook page details!', 'warning')
    return redirect(url_for('fbprofile'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
