import os
import cv2
import time
import requests
from datetime import datetime
from flask import Flask, Response, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO

from db_handler import DatabaseHandler
from ai_vision import AIVision

# Khởi tạo Flask App và SocketIO với CORS cho phép tất cả các nguồn
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_door_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Cấu hình đường dẫn và tham số hệ thống
ESP32_IP = os.getenv("ESP32_IP", "192.168.1.50")
RTSP_URL = os.getenv("RTSP_URL", "")  # URL RTSP hoặc 0 (nếu dùng webcam nội bộ để test)
MODEL_PATH = os.getenv("MODEL_PATH", "models/dacn.pt")
PROOF_DIR = "captured_proofs"
os.makedirs(PROOF_DIR, exist_ok=True)

# Khởi tạo Cơ sở dữ liệu SQLite
db = DatabaseHandler("attendance.db")
db.init_db()

def face_detected_callback(name: str, original_frame):
    """
    Callback được gọi từ AIVision khi nhận diện khuôn mặt thành công:
    1. Gửi HTTP GET mở cửa sang ESP32.
    2. Lưu ảnh gốc bằng chứng vào captured_proofs/.
    3. Ghi log vào cơ sở dữ liệu SQLite.
    4. Bắn sự kiện SocketIO 'new_attendance' lên Frontend theo thời gian thực.
    """
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Gửi lệnh mở cửa tới ESP32 (timeout ngắn 2s để tránh nghẽn)
    esp32_url = f"http://{ESP32_IP}/open_door"
    try:
        requests.get(esp32_url, params={"name": name}, timeout=2)
        print(f"[Bridge] Đã gửi lệnh mở cửa cho: {name} qua {esp32_url}")
    except requests.exceptions.RequestException as e:
        print(f"[Bridge] Không thể kết nối tới ESP32 ({esp32_url}): {e}")

    # 2. Lưu ảnh bằng chứng (ảnh gốc chưa vẽ khung)
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
    filename = f"{clean_name}_{file_timestamp}.jpg"
    filepath = os.path.join(PROOF_DIR, filename)
    cv2.imwrite(filepath, original_frame)
    image_url = f"/proofs/{filename}"

    # 3. Ghi vào database SQLite
    log_id = db.log_attendance(name=name, method="AI", image_path=filepath, log_time=timestamp_str)

    # 4. Phát sự kiện SocketIO tới giao diện Frontend
    attendance_data = {
        "id": log_id,
        "name": name,
        "method": "AI",
        "time": timestamp_str,
        "image_url": image_url
    }
    socketio.emit("new_attendance", attendance_data)
    print(f"[Bridge] Phát SocketIO new_attendance (AI): {attendance_data}")

# Khởi tạo module AI Vision và kích hoạt luồng đọc camera
ai_vision = AIVision(
    rtsp_url=RTSP_URL,
    model_path=MODEL_PATH,
    on_face_detected=face_detected_callback
)
ai_vision.start()

def generate_mjpeg_stream():
    """
    Generator tạo luồng video MJPEG từ frame của AI Vision để stream lên Web.
    """
    while True:
        frame = ai_vision.get_annotated_frame()
        if frame is None:
            time.sleep(0.04)
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@app.route('/')
def index():
    """Trang chủ hiển thị giao diện dashboard buồng lái Mecha."""
    logs = db.get_recent_logs(limit=15)
    return render_template('index.html', logs=logs, active_page='home')

@app.route('/on-time')
def on_time_page():
    """Trang danh sách điểm danh đúng giờ hôm nay (<= 8h00 sáng)."""
    records = db.get_today_on_time()
    today_str = datetime.now().strftime("%d/%m/%Y")
    return render_template('on_time.html', records=records, today=today_str, active_page='on_time')

@app.route('/late')
def late_page():
    """Trang danh sách điểm danh muộn hôm nay (> 8h00 sáng)."""
    records = db.get_today_late()
    today_str = datetime.now().strftime("%d/%m/%Y")
    return render_template('late.html', records=records, today=today_str, active_page='late')

@app.route('/statistics')
def statistics_page():
    """Trang thống kê tần suất điểm danh đúng giờ & muộn trong tháng."""
    stats = db.get_monthly_statistics()
    month_str = datetime.now().strftime("%m/%Y")
    return render_template('statistics.html', stats=stats, current_month=month_str, active_page='statistics')

@app.route('/video_feed')
def video_feed():
    """Route stream luồng camera kèm bounding box lên web browser."""
    return Response(
        generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/proofs/<path:filename>')
def serve_proof(filename):
    """Phục vụ ảnh bằng chứng điểm danh cho frontend."""
    return send_from_directory(PROOF_DIR, filename)

@app.route('/api/fingerprint', methods=['POST'])
@app.route('/api/attendance', methods=['POST'])
def api_fingerprint():
    """
    API tiếp nhận dữ liệu điểm danh từ ESP32 khi quét vân tay thành công:
    Payload JSON: {"finger_id": 1}
    """
    data = request.get_json(silent=True) or {}
    finger_id = data.get('finger_id')

    if finger_id is None:
        return jsonify({"status": "error", "message": "Missing finger_id"}), 400

    name = f"User #{finger_id}"
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Lưu bản ghi điểm danh phương thức Vân tay vào SQLite
    log_id = db.log_attendance(name=name, method="Vân tay", image_path=None, log_time=timestamp_str)

    # Bắn sự kiện SocketIO cho Frontend
    attendance_data = {
        "id": log_id,
        "name": name,
        "method": "Vân tay",
        "time": timestamp_str,
        "image_url": None
    }
    socketio.emit("new_attendance", attendance_data)
    print(f"[Bridge] Phát SocketIO new_attendance (Vân tay): {attendance_data}")

    return jsonify({
        "status": "success",
        "message": "Fingerprint attendance recorded",
        "id": log_id,
        "name": name
    }), 200

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """API lấy lịch sử điểm danh mới nhất."""
    limit = request.args.get('limit', default=20, type=int)
    return jsonify(db.get_recent_logs(limit=limit))

if __name__ == '__main__':
    print("[Server] Khởi động Server Flask-SocketIO tại cổng 5000...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
