from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure random key

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'stone10242003',
    'database': 'snsu_drrm'
}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM responders WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and user[0] == password:
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid credentials"
        except mysql.connector.Error as err:
            error = f"Database error: {err}"
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']

        if not re.match(r'^Responder_[A-Za-z]+$', username):
            error = "Username must be in the format: Responder_lastname"
        elif len(password) > 20:
            error = "Password must not exceed 20 characters."
        else:
            try:
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM responders WHERE username = %s", (username,))
                existing_user = cursor.fetchone()

                if existing_user:
                    error = "Username already taken"
                else:
                    cursor.execute(
                        "INSERT INTO responders (name, username, password) VALUES (%s, %s, %s)",
                        (name, username, password)
                    )
                    conn.commit()
                    success = "Account created successfully!"
            except mysql.connector.Error as err:
                error = f"Database error: {err}"
            finally:
                cursor.close()
                conn.close()

    return render_template('signup.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'username' not in session:
        return redirect(url_for('login'))

    message = None

    if request.method == 'POST':
        name = request.form['name']
        grade_section = request.form['grade_section']
        age = request.form['age']
        date = request.form['date']
        time_of_incident = request.form['time_of_incident']

        loc = ', '.join(request.form.getlist('loc'))
        speech = ', '.join(request.form.getlist('speech'))
        skin = ', '.join(request.form.getlist('skin'))

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patient_reports 
                (name, grade_section, age, date, time_of_incident, loc, speech, skin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, grade_section, age, date, time_of_incident, loc, speech, skin))
            conn.commit()
            message = "Report submitted successfully!"
        except mysql.connector.Error as err:
            message = f"Database error: {err}"
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()

    return render_template('patient_report.html', success=message)

@app.route('/view_reports')
def view_reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patient_reports ORDER BY date DESC, time_of_incident DESC")
    reports = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_reports.html', reports=reports)

@app.route('/manage_users')
def manage_users():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM responders ORDER BY username ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_users.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
