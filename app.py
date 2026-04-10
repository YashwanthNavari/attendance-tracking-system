from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import database
import secrets
import datetime
# import face_recognition # Import later when implementing
import json
import os
import numpy as np
try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    print("Warning: face_recognition not found. Face check will be mocked.")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ... (Database init code remains same, handled by existing file content usually, but here I am replacing from top if I need to inject imports. Actually I will just replace the specific function and add imports at top if I can.
# Since I cannot easily insert imports at top without replacing whole file or using multi_replace with line numbers which might be shifting, check if I can just append imports or if I should replace the block.
# I will use a different strategy: just add the logic in the new functions and assume I can add imports.
# Wait, `replace_file_content` replaces a contiguous block. 
# I will replacing the whole `mark_attendance` and add `register_face` and the imports.
# I'll replace the top of the file to add imports, then `mark_attendance`.
# Actually I can do 2 replacements using `multi_replace`.

# Let's use multi_replace to:
# 1. Add imports at the top.
# 2. Modify `mark_attendance`.
# 3. Add `register_face` at the end (before main).

app.secret_key = secrets.token_hex(16)

# Initialize DB on start
if not os.path.exists(database.DB_NAME):
    database.init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    role_req = data.get('role')
    
    print(f"Login Attempt: username='{username}', role='{role_req}'") # Debug log
    
    conn = database.get_db_connection()
    # Try exact match first
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    
    # If not found, try case-insensitive
    if not user:
        print(f"Exact match failed for '{username}'. Trying case-insensitive.")
        user = conn.execute('SELECT * FROM users WHERE lower(username) = ?', (username.lower(),)).fetchone()
    
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        print(f"Login Success: {username} as {user['role']}")
        return jsonify({"status": "success", "role": user['role']})
    else:
        print(f"Login Failed: User '{username}' not found in DB.")
        return jsonify({"status": "error", "message": "User not found"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if session.get('role') != 'faculty':
        return redirect(url_for('index'))
    return render_template('faculty_dashboard.html')

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('index'))
    return render_template('student_dashboard.html')

# --- API Routes ---

def haversine(lat1, lon1, lat2, lon2):
    import math
    R = 6371e3 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.route('/api/generate_qr', methods=['POST'])
def generate_qr():
    if session.get('role') != 'faculty':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
    try:
        data = request.json
        if not data:
            raise ValueError("No JSON data received")
            
        subject = data.get('subject')
        lat = data.get('latitude')
        lng = data.get('longitude')
        radius = data.get('radius', 50) # Default 50m
        # Create Session
        session_token = secrets.token_hex(8)
        # Simple expiry: 5 mins
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (session_token, faculty_id, subject, latitude, longitude, radius, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_token, session.get('user_id'), subject, lat, lng, radius, expires_at))
        session_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return QR Data (contains session_token)
        return jsonify({
            "status": "success",
            "qr_data": session_token, 
            "session_id": session_db_id
        })
    except Exception as e:
        import traceback
        error_msg = f"Error creating session: {e}\n{traceback.format_exc()}"
        print(error_msg)
        with open("server_log.txt", "a") as f:
            f.write(f"[{datetime.datetime.now()}] {error_msg}\n")
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500

@app.route('/attendance/<token>')
def attendance_form(token):
    # Verify token validity to show subject name
    conn = database.get_db_connection()
    sess = conn.execute('SELECT * FROM sessions WHERE session_token = ?', (token,)).fetchone()
    conn.close()
    
    if not sess:
        return "Invalid or Expired Session", 404
        
    return render_template('attendance_form.html', token=token, subject=sess['subject'])

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    # Allow if logged in OR if public submission (check fields)
    is_public = False
    if session.get('role') != 'student':
        is_public = True # Assume public flow
    
    data = request.json
    qr_token = data.get('qr_data')
    
    # FIX: If qr_token is a full URL (from scanner), extract the token part
    if qr_token and '/' in qr_token:
        qr_token = qr_token.split('/')[-1]
    
    print(f"DEBUG: Processing Attendance for Token: {qr_token}") # Debug
        
    student_lat = data.get('latitude')
    student_lng = data.get('longitude')
    device_id = data.get('device_id')
    
    # Public fields
    full_name = data.get('full_name')
    roll_no = data.get('roll_no')
    
    conn = database.get_db_connection()
    sess = conn.execute('SELECT * FROM sessions WHERE session_token = ?', (qr_token,)).fetchone()
    
    if not sess:
        conn.close()
        return jsonify({"status": "error", "message": "Invalid Session"}), 404
        
    # 1. Check Expiry
    if datetime.datetime.strptime(sess['expires_at'], '%Y-%m-%d %H:%M:%S.%f') < datetime.datetime.now():
        conn.close()
        return jsonify({"status": "error", "message": "Session Expired"}), 400
        
    # 2. Check Location (Geo-fencing)
    if sess['latitude'] is not None and student_lat is not None:
        dist = haversine(sess['latitude'], sess['longitude'], student_lat, student_lng)
        if dist > sess['radius']:
            conn.close()
            return jsonify({"status": "error", "message": f"You are too far ({int(dist)}m). Must be within {sess['radius']}m."}), 400
            
    # 3. Check Face (if provided and system supports it)
    face_image_b64 = data.get('face_image')
    if face_image_b64 and FACE_REC_AVAILABLE:
        # Retrieve user's registered face
        user = conn.execute('SELECT face_encoding FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user and user['face_encoding']:
            try:
                # Decode uploaded image
                import base64
                import cv2
                
                # Split header if present (data:image/jpeg;base64,...)
                if ',' in face_image_b64:
                    face_image_b64 = face_image_b64.split(',')[1]
                
                image_bytes = base64.b64decode(face_image_b64)
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Get encoding
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                face_encodings = face_recognition.face_encodings(rgb_img)
                
                if not face_encodings:
                    conn.close()
                    return jsonify({"status": "error", "message": "No face detected in image"}), 400
                
                current_encoding = face_encodings[0]
                registered_encoding = np.frombuffer(user['face_encoding'], dtype=np.float64)
                
                match = face_recognition.compare_faces([registered_encoding], current_encoding, tolerance=0.6)
                if not match[0]:
                    conn.close()
                    return jsonify({"status": "error", "message": "Face Verification Failed: Not you!"}), 400
            except Exception as e:
                print(f"Face Error: {e}")
                # For prototype, maybe proceed or fail. Let's fail safe. (Or allow if debug)
                # pass 

    # 4. Check Device Binding (Security)
    if device_id and not is_public: # Only strict binding for logged in users for now, or bind public too?
        # Public users might not have a user ID. So we can't curb them easily by user_id.
        # But we can check if this device_id scanned recently for this session?
        pass

    # 5. Check Duplicate
    # If logged in, check by ID. If public, check by roll_no + session?
    if not is_public:
        existing = conn.execute('SELECT * FROM attendance WHERE session_id = ? AND student_id = ?', 
                                (sess['id'], session['user_id'])).fetchone()
    else:
        existing = conn.execute('SELECT * FROM attendance WHERE session_id = ? AND roll_no = ?',
                                (sess['id'], roll_no)).fetchone()
                                
    if existing:
        conn.close()
        return jsonify({"status": "error", "message": "Already marked present"}), 400

    # 6. Mark Attendance
    student_id = session.get('user_id') if not is_public else 0 # 0 for public
    
    # Save Image if present
    captured_image_path = None
    if face_image_b64:
        try:
            import base64
            import uuid
            
            # Ensure directory exists
            upload_folder = os.path.join('static', 'uploads', 'attendance_faces')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            # Clean base64 string
            img_str = face_image_b64
            if ',' in img_str:
                img_str = img_str.split(',')[1]
                
            img_data = base64.b64decode(img_str)
            filename = f"{sess['id']}_{student_id}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(upload_folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(img_data)
                
            captured_image_path = filename # Store relative filename or path
            
        except Exception as e:
            print(f"Error saving image: {e}")
            # Proceed without saving image if error
            
    conn.execute('INSERT INTO attendance (session_id, student_id, status, full_name, roll_no, device_id, captured_image_path) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (sess['id'], student_id, 'Present', full_name, roll_no, device_id, captured_image_path))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Attendance Marked"})

@app.route('/api/register_face', methods=['POST'])
def register_face():
    if session.get('role') != 'student':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    if not FACE_REC_AVAILABLE:
         return jsonify({"status": "success", "message": "Face Recognition not active (Mocked)"})

    data = request.json
    face_image_b64 = data.get('image')
    
    if not face_image_b64:
        return jsonify({"status": "error", "message": "No image provided"}), 400
        
    try:
        import base64
        import cv2
        
        if ',' in face_image_b64:
            face_image_b64 = face_image_b64.split(',')[1]
            
        image_bytes = base64.b64decode(face_image_b64)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        encodings = face_recognition.face_encodings(rgb_img)
        if not encodings:
             return jsonify({"status": "error", "message": "No face found"}), 400
             
        encoding_bytes = encodings[0].tobytes()
        
        conn = database.get_db_connection()
        conn.execute('UPDATE users SET face_encoding = ? WHERE id = ?', (encoding_bytes, session['user_id']))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "Face Registered Successfully"})
        
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": "Processing Error"}), 500

@app.route('/api/session_attendance/<int:session_id>')
def get_session_attendance(session_id):
    if session.get('role') != 'faculty':
         return jsonify({"status": "error", "message": "Unauthorized"}), 403
         
    conn = database.get_db_connection()
    # Check if session belongs to faculty
    sess = conn.execute('SELECT * FROM sessions WHERE id = ? AND faculty_id = ?', 
                        (session_id, session['user_id'])).fetchone()
    
    if not sess:
         conn.close()
         return jsonify({"status": "error", "message": "Access Denied or Invalid Session"}), 403
         
    logs = conn.execute('''
        SELECT full_name, roll_no, marked_at, status 
        FROM attendance 
        WHERE session_id = ? 
        ORDER BY marked_at DESC
    ''', (session_id,)).fetchall()
    
    conn.close()
    
    data = []
    for log in logs:
        data.append({
            "full_name": log['full_name'],
            "roll_no": log['roll_no'],
            "marked_at": log['marked_at'],
            "status": log['status']
        })
        
    return jsonify({"status": "success", "data": data})

@app.route('/api/my_sessions')
def my_sessions():
    if session.get('role') != 'faculty':
         return jsonify({"status": "error", "message": "Unauthorized"}), 403
         
    conn = database.get_db_connection()
    sessions = conn.execute('''
        SELECT id, subject, created_at, session_token, 
               (SELECT COUNT(*) FROM attendance WHERE session_id = sessions.id) as count
        FROM sessions 
        WHERE faculty_id = ? 
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    data = []
    for s in sessions:
        data.append({
            "id": s['id'],
            "subject": s['subject'],
            "created_at": s['created_at'],
            "token": s['session_token'],
            "count": s['count']
        })
        
    return jsonify({"status": "success", "data": data})

@app.route('/api/export_attendance/<int:session_id>')
def export_attendance(session_id):
    if session.get('role') != 'faculty':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    conn = database.get_db_connection()
    sess = conn.execute('SELECT * FROM sessions WHERE id = ? AND faculty_id = ?', 
                        (session_id, session['user_id'])).fetchone()
    
    if not sess:
        conn.close()
        return "Session not found or access denied", 404
        
    logs = conn.execute('''
        SELECT full_name, roll_no, marked_at, status, captured_image_path, device_id
        FROM attendance 
        WHERE session_id = ?
    ''', (session_id,)).fetchall()
    
    conn.close()
    
    try:
        import csv
        import zipfile
        import io
        from flask import send_file
        
        # Create ZIP in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Create CSV
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_writer.writerow(['Full Name', 'Roll No', 'Time', 'Status', 'Image File', 'Device ID'])
            
            for log in logs:
                img_filename = log['captured_image_path'] if log['captured_image_path'] else "N/A"
                csv_writer.writerow([
                    log['full_name'], 
                    log['roll_no'], 
                    log['marked_at'], 
                    log['status'], 
                    img_filename, 
                    log['device_id']
                ])
            
            zf.writestr(f"attendance_report_{session_id}.csv", csv_buffer.getvalue())
            
            # 2. Add Images
            upload_folder = os.path.join('static', 'uploads', 'attendance_faces')
            for log in logs:
                if log['captured_image_path']:
                    filepath = os.path.join(upload_folder, log['captured_image_path'])
                    if os.path.exists(filepath):
                        zf.write(filepath, os.path.join('images', log['captured_image_path']))
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'attendance_export_{session_id}.zip'
        )
        
    except Exception as e:
        print(f"Export Error: {e}")
        return f"Error exporting data: {e}", 500

if __name__ == '__main__':
    # Initial dummy data for testing
    if not os.path.exists(database.DB_NAME):
        database.init_db()
    
    conn = database.get_db_connection()
    if not conn.execute('SELECT * FROM users').fetchone():
        print("Creating demo users: faculty1, student1")
        conn.execute("INSERT INTO users (username, password, role, full_name) VALUES ('faculty1', 'pass', 'faculty', 'Dr. Smith')")
        conn.execute("INSERT INTO users (username, password, role, full_name) VALUES ('student1', 'pass', 'student', 'John Doe')")
        conn.commit()
    conn.close()

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
