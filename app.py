import os
from flask import Flask, jsonify, render_template, redirect, url_for, request, session
import hashlib
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import ObjectId
from datetime import datetime


MONGODB_CONNECTION_STRING = "mongodb+srv://annisarahmaningsih55:sparta@cluster0.h7c5are.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client.Sekolah

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['UPLOAD_FOLDER'] = 'static/dokumen'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

students = []

# Admin credentials
ADMIN_EMAIL = "admin@admin.admin"
ADMIN_PASSWORD = "admin"



@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)


@app.route('/')
def home():
    dokumentasi_list = list(db.dokumentasi.find())
    return render_template('index.html', dokumentasi_list=dokumentasi_list, enumerate=enumerate)

    
@app.route('/homeuser')
def homeuser():
    dokumentasi_list = list(db.dokumentasi.find())
    return render_template('home.html', dokumentasi_list=dokumentasi_list, enumerate=enumerate)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_receive = request.form["email_give"]
        pw_receive = request.form["pw_give"]

        pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

        # Check admin credentials
        if email_receive == ADMIN_EMAIL and pw_receive == ADMIN_PASSWORD:
            session['admin'] = True
            return jsonify({"result": "admin"})
        
        findUser = db.user.find_one({"email": email_receive, "pw": pw_hash})
        
        if findUser:
            session['user'] = email_receive
            return jsonify({"result": "success"})
        else:
            return jsonify({"result": "error"})

    return render_template('login.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST" :
        email_receive = request.form["email_give"]
        pw_receive = request.form["pw_give"]
        name_receive = request.form["name_give"]
        
        pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

        findEmail = db.user.find_one({"email": email_receive})

        if findEmail:
            return jsonify({"result": "error"})

        else:
            db.user.insert_one({"name" : name_receive, "email": email_receive, "pw": pw_hash})

    return render_template('register.html')


@app.route('/pengumuman')
def pengumuman():
    students = list(db.data_siswa.find())
    today_date = datetime.today().strftime('%Y-%m-%d')
    return render_template('pengumuman.html', students=students, enumerate=enumerate, today_date=today_date)


@app.route('/profile', methods=["GET", "POST"])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        nama_receive = request.form["nama_give"]
        gender_receive = request.form["gender_give"]
        alamat_receive = request.form["alamat_give"]
        tempatLahir_receive = request.form["tempatLahir_give"]
        tanggalLahir_receive = request.form["tanggalLahir_give"]

        if 'foto_give' in request.files:
            foto_receive = request.files["foto_give"]
            foto_path = f"static/profile_pics/{foto_receive.filename}"
            foto_receive.save(foto_path)
        else:
            foto_path = "static/profile_pics/profile_placeholder.jpeg"

        doc = {
            "nama": nama_receive,
            "gender": gender_receive,
            "alamat": alamat_receive,
            "tempatLahir": tempatLahir_receive,
            "tanggalLahir": tanggalLahir_receive,
            "email": session['user'],
            "foto": foto_path
        }

        profile = db.profile.find_one({"email": session['user']})

        if profile:
            db.profile.update_one(
                {"email": session['user']},
                {"$set": {
                    "nama": nama_receive,
                    "gender": gender_receive,
                    "alamat": alamat_receive,
                    "tempatLahir": tempatLahir_receive,
                    "tanggalLahir": tanggalLahir_receive,
                    "foto": foto_path
                }}
            )
        else:
            db.profile.insert_one(doc)
        return jsonify({"result": "success"})

    profile = db.profile.find_one({"email": session['user']})

    if profile:
        user_info = {
            "nama": profile.get('nama', ''),
            "gender": profile.get('gender', ''),
            "alamat": profile.get('alamat', ''),
            "tempatLahir": profile.get('tempatLahir', ''),
            "tanggalLahir": profile.get('tanggalLahir', ''),
            "foto": profile.get('foto', 'static/profile_pics/profile_placeholder.jpeg')
        }
    else:
        user_info = {
            "nama": '',
            "gender": '',
            "alamat": '',
            "tempatLahir": '',
            "tanggalLahir": '',
            "foto": 'static/profile_pics/profile_placeholder.jpeg'
        }
    return render_template('profile.html', user_info=user_info)


@app.route('/pendaftaran')
def daftar():
    return render_template('pendaftaran.html')


#untuk mengirim data pendaftaran
@app.route('/kirim-data', methods=['POST'])
def kirim_data():
    if request.method == 'POST':
        nama_lengkap = request.form['nama_lengkap']
        nama_panggilan = request.form['nama_panggilan']
        asalprovinsi = request.form['asalprovinsi']
        asalkota_kabupaten = request.form['asalkota_kabupaten']
        asaldusun_desa = request.form['asaldusun_desa']
        jenis_kelamin = request.form['jenis_kelamin']
        nomor_hp = request.form['nomor_hp']
        dokumen = request.files['dokumen']

        filename = None
        if dokumen:
            filename = secure_filename(dokumen.filename)
            dokumen_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(os.path.dirname(dokumen_path), exist_ok=True)
            dokumen.save(dokumen_path)

        student = {
            'nama_lengkap': nama_lengkap,
            'nama_panggilan': nama_panggilan,
            'asalprovinsi': asalprovinsi,
            'asalkota_kabupaten': asalkota_kabupaten,
            'asaldusun_desa': asaldusun_desa,
            'jenis_kelamin': jenis_kelamin,
            'nomor_hp': nomor_hp,
            'dokumen': filename
        }

        # Masukkan data ke koleksi students di MongoDB
        db.students.insert_one(student)
        
        return render_template('home.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/homeadmin')
def homeadmin():
    if 'admin' in session:
        # Hitung jumlah dokumen dalam koleksi students dan data_siswa
        jumlah_students = db.students.count_documents({})
        jumlah_data_siswa = db.data_siswa.count_documents({})
        jumlah_user = db.user.count_documents({})
        jumlah_dokumentasi = db.dokumentasi.count_documents({})
        
        return render_template('dashboard.html', jumlah_students=jumlah_students, jumlah_data_siswa=jumlah_data_siswa, jumlah_user=jumlah_user, jumlah_dokumentasi=jumlah_dokumentasi)
    return redirect(url_for('login'))


@app.route('/datasiswamasuk')
def datasiswamasuk():
    students = list(db.students.find())
    return render_template('datamasuk.html', students=students, enumerate=enumerate)


@app.route('/datasiswa')
def datasiswa():
    students = list(db.data_siswa.find())
    return render_template('datasiswa.html', students=students, enumerate=enumerate)


@app.route('/editdokumentasi', methods=['GET', 'POST'])
def editdokumentasi():
    if request.method == 'POST':
        judul = request.form['judul']
        deskripsi = request.form['deskripsi']
        file = request.files['inputFile']

        # Simpan file yang diunggah
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Simpan informasi dokumentasi ke MongoDB
        db.dokumentasi.insert_one({
            'judul': judul,
            'deskripsi': deskripsi,
            'file_path': file_path
        })
        
        return redirect(url_for('homeadmin'))
    
    return render_template('editdokumentasi.html')


@app.route('/setujui/<student_id>', methods=['POST'])
def setujui(student_id):
    student = db.students.find_one({'_id': ObjectId(student_id)})
    if student:
        # Pindahkan data ke koleksi "data siswa"
        db.data_siswa.insert_one(student)
        # Hapus data dari koleksi "data siswa masuk"
        db.students.delete_one({'_id': ObjectId(student_id)})
    return redirect(url_for('datasiswamasuk'))


@app.route('/hapus/<student_id>', methods=['POST'])
def hapus(student_id):
    db.students.delete_one({'_id': ObjectId(student_id)})
    return redirect(url_for('datasiswamasuk'))


@app.route('/updateprofile', methods=["POST"])
def updateprofile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run("0.0.0.0", port=5000, debug=True)