from flask import Flask, render_template, request, redirect, send_file
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import check_password_hash
import pandas as pd

app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username FROM users WHERE id=%s", (user_id,))
    u = cur.fetchone()
    if u:
        return User(u[0], u[1])

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (request.form['username'],))
        u = cur.fetchone()

        if u and check_password_hash(u[2], request.form['password']):
            login_user(User(u[0], u[1]))
            return redirect('/dashboard')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM barang")
    data = cur.fetchall()
    return render_template('dashboard.html', data=data)

@app.route('/barang', methods=['GET', 'POST'])
@login_required
def barang():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        cur.execute("""
            INSERT INTO barang (kode_barang, nama_barang, kategori, stok, satuan)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            request.form['kode'],
            request.form['nama'],
            request.form['kategori'],
            request.form['stok'],
            request.form['satuan']
        ))
        mysql.connection.commit()

    cur.execute("SELECT * FROM barang")
    data = cur.fetchall()
    return render_template('barang.html', data=data)

@app.route('/masuk/<int:id>', methods=['POST'])
@login_required
def masuk(id):
    jumlah = int(request.form['jumlah'])
    cur = mysql.connection.cursor()

    cur.execute("INSERT INTO barang_masuk (id_barang, tanggal, jumlah) VALUES (%s, CURDATE(), %s)", (id, jumlah))
    cur.execute("UPDATE barang SET stok = stok + %s WHERE id=%s", (jumlah, id))

    mysql.connection.commit()
    return redirect('/dashboard')

@app.route('/keluar/<int:id>', methods=['POST'])
@login_required
def keluar(id):
    jumlah = int(request.form['jumlah'])
    cur = mysql.connection.cursor()

    cur.execute("INSERT INTO barang_keluar (id_barang, tanggal, jumlah) VALUES (%s, CURDATE(), %s)", (id, jumlah))
    cur.execute("UPDATE barang SET stok = stok - %s WHERE id=%s", (jumlah, id))

    mysql.connection.commit()
    return redirect('/dashboard')

@app.route('/export')
@login_required
def export():
    df = pd.read_sql("SELECT * FROM barang", mysql.connection)
    file = "stok_bengkel_motor.xlsx"
    df.to_excel(file, index=False)
    return send_file(file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
