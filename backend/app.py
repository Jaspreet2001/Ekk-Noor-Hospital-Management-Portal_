import sys
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from datetime import datetime, date

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ── Database config ──
DB_CONFIG = {
    "host":     "localhost",
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "kakkar3010",
    "port":     5432
}

def get_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None

def init_db():
    conn = get_db()
    if conn is None:
        print("Could not connect to database. Check your PostgreSQL settings.")
        return
    try:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id          SERIAL PRIMARY KEY,
                full_name   TEXT NOT NULL,
                phone       TEXT NOT NULL,
                email       TEXT,
                department  TEXT NOT NULL,
                doctor      TEXT,
                date        TEXT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id          SERIAL PRIMARY KEY,
                name        VARCHAR(255) NOT NULL,
                phone       VARCHAR(10)  NOT NULL,
                age         INTEGER      NOT NULL,
                gender      VARCHAR(20)  NOT NULL,
                relation    VARCHAR(50)  NOT NULL,
                condition   TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        print("All tables ready.")

    except Exception as e:
        print("Error creating tables:", e)
    finally:
        conn.close()

# ── Serve pages ──
@app.route('/')
def home(): 
    return app.send_static_file('home.html')

@app.route('/patient')
def patient():
    return app.send_static_file('patient.html')

@app.route('/patients-table')
def patients_table():
    return app.send_static_file('patients_dashboard.html')

# ── Book appointment ──
@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.get_json()

        full_name  = data.get('full_name')
        phone      = data.get('phone')
        email      = data.get('email', '')
        department = data.get('department')
        doctor     = data.get('doctor', '')
        appt_date  = data.get('date')

        if not full_name or not phone or not department or not appt_date:
            return jsonify({'success': False, 'message': 'Please fill all required fields.'}), 400

        try:
            selected_date = datetime.strptime(appt_date, '%Y-%m-%d').date()
            today         = datetime.today().date()
            if selected_date < today:
                return jsonify({'success': False, 'message': 'Past dates are not allowed.'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

        if not phone.isdigit() or len(phone) != 10:
            return jsonify({'success': False, 'message': 'Phone number must be exactly 10 digits.'}), 400

        conn = get_db()
        if conn is None:
            return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

        c = conn.cursor()
        c.execute('''
            INSERT INTO appointments (full_name, phone, email, department, doctor, date)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (full_name, phone, email, department, doctor, appt_date))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Appointment booked successfully!'})

    except Exception as e:
        print("Error booking appointment:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

# ── View all appointments ──
@app.route('/appointments', methods=['GET'])
def get_appointments():
    try:
        conn = get_db()
        if conn is None:
            return jsonify({'error': 'Database connection failed.'}), 500

        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute('SELECT * FROM appointments ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()

        return jsonify([dict(row) for row in rows])

    except Exception as e:
        print("Error fetching appointments:", e)
        return jsonify({'error': str(e)}), 500

# ── Register patient ──
@app.route('/register-patient', methods=['POST'])
def register_patient():
    try:
        data      = request.get_json()
        name      = data.get('name')
        phone     = data.get('phone')
        age       = data.get('age')
        gender    = data.get('gender')
        relation  = data.get('relation')
        condition = data.get('condition', '')

        if not name or not phone or not age or not gender or not relation:
            return jsonify({'success': False, 'message': 'Please fill all required fields.'}), 400

        if not str(phone).isdigit() or len(str(phone)) != 10:
            return jsonify({'success': False, 'message': 'Phone number must be exactly 10 digits.'}), 400

        conn = get_db()
        if conn is None:
            return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

        c = conn.cursor()
        c.execute('''
            INSERT INTO patients (name, phone, age, gender, relation, condition)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (name, phone, int(age), gender, relation, condition))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Patient registered successfully!'})

    except Exception as e:
        print("Error registering patient:", e)
        return jsonify({'success': False, 'message': str(e)}), 500

# ── Get all patients ──
@app.route('/get-all-patients', methods=['GET'])
def get_all_patients():
    try:
        conn = get_db()
        if conn is None:
            return jsonify({'error': 'Database connection failed.'}), 500

        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute('SELECT * FROM patients ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()

        return jsonify([dict(row) for row in rows])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Search patient by name ──
# ✅ BUG FIX (frontend): The HTML was calling /get-patient + name (path concat).
#    Fixed in patient.html to use /get-patient?name=... (query param).
#    This route already correctly reads from request.args — no change needed here.
@app.route('/get-patient', methods=['GET'])
def get_patient():
    try:
        name = request.args.get('name', '').strip()
        if not name:
            return jsonify({'found': False, 'error': 'No name provided.'})

        conn = get_db()
        if conn is None:
            return jsonify({'found': False, 'error': 'Database connection failed.'})

        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute('''
            SELECT * FROM patients
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY created_at DESC
            LIMIT 1
        ''', (f'%{name}%',))
        row = c.fetchone()
        conn.close()

        if row:
            return jsonify({'found': True, 'patient': dict(row)})
        else:
            return jsonify({'found': False})

    except Exception as e:
        return jsonify({'found': False, 'error': str(e)}), 500

# ── Run server ──
if __name__ == '__main__':
    init_db()
    print("----------------------------------")
    print("Server  : http://localhost:5000")
    print("Database: PostgreSQL (postgres)")
    print("Status  : Running...")
    print("----------------------------------")
    app.run(debug=True, port=5000)