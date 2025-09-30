import os
import cv2
import json
import sqlite3
import hashlib
import time
import hmac
import base64
import numpy as np
from collections import deque
from ultralytics import YOLO
from flask import Flask, Response, request, jsonify, render_template

app = Flask(__name__)
# model = YOLO('yolov8n.pt') # REMOVED from here to be loaded fresh in the stream

video_path = None
ALERT_THRESHOLD = 7
analytics_data = {"zone_occupancy": {}, "events": deque(maxlen=10), "alerts": [], "chart_data": {}}
object_last_zone = {}
DB_FILE = "users.db"
JWT_SECRET = os.environ.get('JWT_SECRET', 'please-change-this-secret')

try:
    import jwt  # PyJWT (optional dependency)
    _HAS_PYJWT = True
except Exception:
    jwt = None
    _HAS_PYJWT = False

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS zones (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, camera_id TEXT NOT NULL, label TEXT NOT NULL, coordinates TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id))")
    conn.commit()
    # Ensure jwt_token column exists without breaking existing deployments
    cursor.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'jwt_token' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN jwt_token TEXT")
        conn.commit()
    conn.close()
    print("Database and tables initialized successfully.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _b64url_encode(data_bytes: bytes) -> str:
    return base64.urlsafe_b64encode(data_bytes).rstrip(b'=').decode('ascii')

def _b64url_json(obj) -> str:
    return _b64url_encode(json.dumps(obj, separators=(',', ':')).encode('utf-8'))

def generate_jwt_token(username: str, expires_in_seconds: int = 60*60*24) -> str:
    issued_at = int(time.time())
    payload = {
        "sub": username,
        "iat": issued_at,
        "exp": issued_at + expires_in_seconds
    }
    if _HAS_PYJWT:
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    # Lightweight fallback if PyJWT isn't installed
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_json(header)
    payload_b64 = _b64url_json(payload)
    signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_jwt_token(token: str):
    if not token:
        return None, "missing token"
    try:
        if _HAS_PYJWT:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return decoded, None
        # Manual verification
        parts = token.split('.')
        if len(parts) != 3:
            return None, "invalid token format"
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
        if _b64url_encode(expected_sig) != signature_b64:
            return None, "invalid signature"
        # Decode payload and validate exp
        padded = payload_b64 + '==='  # add padding for b64 decode if needed
        payload_json = base64.urlsafe_b64decode(padded).decode('utf-8')
        payload = json.loads(payload_json)
        if 'exp' in payload and int(time.time()) > int(payload['exp']):
            return None, "token expired"
        return payload, None
    except Exception as e:
        return None, str(e)

@app.route('/')
def index(): return render_template('login.html')
@app.route('/register_page')
def register_page(): return render_template('register.html')
@app.route('/dashboard')
def dashboard(): return render_template('dashboard.html')

@app.route('/register', methods=['POST'])
def register_api():
    data = request.get_json()
    username, email, password = data.get('username'), data.get('email'), data.get('password')
    if not all([username, email, password]): return jsonify({"success": False, "message": "All fields are required."}), 400
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hash_password(password)))
        conn.commit()
        return jsonify({"success": True, "message": "Registration successful!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username or email already exists."}), 409
    finally: conn.close()

@app.route('/login', methods=['POST'])
def login_api():
    data = request.get_json()
    username, password = data.get('username'), data.get('password')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user[0] == hash_password(password):
        token = generate_jwt_token(username)
        conn2 = sqlite3.connect(DB_FILE)
        cur2 = conn2.cursor()
        try:
            cur2.execute("UPDATE users SET jwt_token = ? WHERE username = ?", (token, username))
            conn2.commit()
        finally:
            conn2.close()
        return jsonify({"success": True, "message": "Login successful!", "token": token}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

@app.route('/get_zones', methods=['GET'])
def get_zones_api():
    username, camera_id = request.args.get('username'), request.args.get('cameraId')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user: conn.close(); return jsonify({"success": False, "message": "User not found."}), 404
    user_id = user[0]
    cursor.execute("SELECT id, label, coordinates FROM zones WHERE user_id = ? AND camera_id = ?", (user_id, camera_id))
    zones_data = cursor.fetchall()
    conn.close()
    zones = [{"id": r[0], "label": r[1], "coordinates": json.loads(r[2])} for r in zones_data]
    return jsonify({"success": True, "zones": zones})

@app.route('/save_zone', methods=['POST'])
def save_zone_api():
    data = request.get_json()
    username, camera_id, label, coordinates = data.get('username'), data.get('cameraId'), data.get('label'), data.get('coordinates')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user: conn.close(); return jsonify({"success": False, "message": "User not found"}), 404
    user_id = user[0]
    cursor.execute("INSERT INTO zones (user_id, camera_id, label, coordinates) VALUES (?, ?, ?, ?)", (user_id, camera_id, label, json.dumps(coordinates)))
    conn.commit()
    new_zone_id = cursor.lastrowid
    conn.close()
    return jsonify({"success": True, "id": new_zone_id})

@app.route('/rename_zone', methods=['POST'])
def rename_zone_api():
    data = request.get_json()
    zone_id, new_label, username = data.get('id'), data.get('newLabel'), data.get('username')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user: conn.close(); return jsonify({"success": False, "message": "User not found"}), 404
    cursor.execute("UPDATE zones SET label = ? WHERE id = ? AND user_id = ?", (new_label, zone_id, user[0]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Zone renamed successfully"})

@app.route('/delete_zone', methods=['POST'])
def delete_zone_api():
    data = request.get_json()
    zone_id, username = data.get('id'), data.get('username')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user: conn.close(); return jsonify({"success": False, "message": "User not found"}), 404
    cursor.execute("DELETE FROM zones WHERE id = ? AND user_id = ?", (zone_id, user[0]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Zone deleted"})

@app.route('/upload_video', methods=['POST'])
def upload_video():
    global video_path
    if 'video' not in request.files:
        return jsonify({"success": False, "message": "No video file part"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
    if file:
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        video_path = os.path.join('uploads', file.filename)
        file.save(video_path)
        return jsonify({"success": True, "message": "Video uploaded successfully"})

def process_video_stream(mode='analytics'):
    global video_path, analytics_data, object_last_zone
    if not video_path or not os.path.exists(video_path): return

    # --- THIS IS THE FIX ---
    # Re-initialize the model here. This creates a fresh tracker for each stream.
    model = YOLO('yolov8n.pt')

    cap = cv2.VideoCapture(video_path)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT label, coordinates FROM zones WHERE camera_id='zm_video'")
    db_zones = cursor.fetchall()
    conn.close()
    
    zones = {label: json.loads(coords) for label, coords in db_zones if coords}
    
    if mode == 'analytics':
        analytics_data["zone_occupancy"] = {name: 0 for name in zones.keys()}
        analytics_data["chart_data"] = {name: deque(maxlen=30) for name in zones.keys()}
        analytics_data["events"].clear(); analytics_data["alerts"].clear(); object_last_zone.clear()
    
    heatmap = None

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
        
        frame_height, frame_width, _ = frame.shape
        if heatmap is None:
            heatmap = np.zeros((frame_height, frame_width), dtype=np.float32)

        results = model.track(frame, persist=True, classes=[0], verbose=False)
        current_occupancy = {name: 0 for name in zones.keys()}
        annotated_frame = frame.copy()

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()

            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                center_x, center_y = int(x), int(y)
                cv2.circle(heatmap, (center_x, center_y), 20, 1, -1)
                x1, y1, x2, y2 = int(x-w/2), int(y-h/2), int(x+w/2), int(y+h/2)
                
                person_in_zone = None
                for zone_name, coords in zones.items():
                    tl_x_abs = int(coords['topLeft']['x'] * frame_width)
                    tl_y_abs = int(coords['topLeft']['y'] * frame_height)
                    br_x_abs = int(coords['bottomRight']['x'] * frame_width)
                    br_y_abs = int(coords['bottomRight']['y'] * frame_height)

                    if tl_x_abs < center_x < br_x_abs and tl_y_abs < center_y < br_y_abs:
                        current_occupancy[zone_name] += 1
                        person_in_zone = zone_name
                        break
                
                if mode == 'tracking':
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                if mode == 'analytics':
                    last_known_zone = object_last_zone.get(track_id)
                    if person_in_zone != last_known_zone:
                        if person_in_zone: analytics_data["events"].appendleft(f"ID {track_id} entered '{person_in_zone}'")
                        if last_known_zone: analytics_data["events"].appendleft(f"ID {track_id} left '{last_known_zone}'")
                        object_last_zone[track_id] = person_in_zone

        if mode == 'analytics':
            heatmap_normalized = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
            heatmap_colored = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET)
            cv2.addWeighted(heatmap_colored, 0.5, annotated_frame, 0.5, 0, annotated_frame)
            heatmap *= 0.95
        
        for zone_name, coords in zones.items():
            pt1 = (int(coords['topLeft']['x'] * frame_width), int(coords['topLeft']['y'] * frame_height))
            pt2 = (int(coords['bottomRight']['x'] * frame_width), int(coords['bottomRight']['y'] * frame_height))
            cv2.rectangle(annotated_frame, pt1, pt2, (255, 0, 0), 2)
            cv2.putText(annotated_frame, f"{zone_name}", (pt1[0], pt1[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if mode == 'analytics':
            analytics_data["zone_occupancy"] = current_occupancy
            for name, count in current_occupancy.items():
                if name in analytics_data["chart_data"]: analytics_data["chart_data"][name].append(count)
            
            analytics_data["alerts"] = [
                f"ALERT: '{name}' has exceeded the threshold ({count}/{ALERT_THRESHOLD})!" 
                for name, count in current_occupancy.items() if count > ALERT_THRESHOLD
            ]
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    cap.release()

@app.route('/processed_video_feed')
def processed_video_feed():
    mode = request.args.get('mode', 'analytics')
    return Response(process_video_stream(mode=mode), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analytics_data')
def analytics_data_api():
    json_safe_data = {
        "zone_occupancy": analytics_data["zone_occupancy"],
        "events": list(analytics_data["events"]),
        "alerts": analytics_data["alerts"],
        "chart_data": {name: list(data) for name, data in analytics_data["chart_data"].items()}
    }
    return jsonify(json_safe_data)

@app.route('/verify_token', methods=['GET'])
def verify_token_api():
    auth_header = request.headers.get('Authorization', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1].strip()
    if not token:
        token = request.args.get('token')
    payload, error = verify_jwt_token(token)
    if error:
        return jsonify({"success": False, "message": error}), 401
    return jsonify({"success": True, "sub": payload.get('sub'), "iat": payload.get('iat'), "exp": payload.get('exp')})

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)