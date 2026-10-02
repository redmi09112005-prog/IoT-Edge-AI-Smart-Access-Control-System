import os
import cv2
import time
import threading
import numpy as np
from ultralytics import YOLO

class AIVision:
    # Bảng ánh xạ nhãn nhận diện (class label) sang tên đầy đủ
    NAME_MAPPING = {
        "long": "Tran The Long",
        "quyen": "Tran Van Quyen",
        "hoang": "Pham Huy Hoang"
    }

    def __init__(self, rtsp_url, model_path="models/dacn.pt", on_face_detected=None):
        """
        Khởi tạo Module AI Vision cho mô hình YOLOv11n:
        :param rtsp_url: Đường dẫn luồng RTSP của Camera (hoặc 0 nếu dùng Webcam).
        :param model_path: Đường dẫn tới file trọng số model YOLO (.pt).
        :param on_face_detected: Hàm callback dạng on_face_detected(user_name, original_frame).
        """
        self.rtsp_url = rtsp_url
        self.model_path = model_path
        self.on_face_detected = on_face_detected
        
        # Cơ chế chống spam nhận diện (tính theo giây cho mỗi người)
        self.cooldown_seconds = 5
        self.last_detection_times = {}
        
        # Biến lưu trữ frame cho web streaming
        self.latest_annotated_frame = None
        self.lock = threading.Lock()
        
        # Cờ kiểm soát luồng hoạt động
        self.is_running = True

        print(f"[AI Vision] Đang tải mô hình YOLOv11 từ: {model_path}...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"[AI Vision] Lỗi: Không tìm thấy file '{model_path}'. Vui lòng kiểm tra lại thư mục models/.")
        
        self.model = YOLO(model_path)
        print(f"[AI Vision] Tải mô hình thành công. Danh sách lớp: {self.model.names}")

        # Quản lý luồng xử lý video ngầm
        self.worker_thread = None

    def get_display_name(self, raw_label: str) -> str:
        """
        Chuyển đổi nhãn lớp nhận diện sang họ và tên đầy đủ:
        - 'long'  -> 'Tran The Long'
        - 'quyen' -> 'Tran Van Quyen'
        - 'hoang' -> 'Pham Huy Hoang'
        """
        clean_key = str(raw_label).lower().strip()
        return self.NAME_MAPPING.get(clean_key, str(raw_label).title())

    def start(self):
        """
        Khởi động luồng đọc camera và suy luận AI ngầm.
        """
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_stream, daemon=True)
            self.worker_thread.start()
            print("[AI Vision] Luồng xử lý camera đã được kích hoạt.")

    def _process_stream(self):
        """
        Luồng đọc camera liên tục, nhận diện khuôn mặt YOLOv11, ánh xạ tên người dùng,
        vẽ bounding box và tự động kết nối lại khi mất mạng.
        """
        while self.is_running:
            source = 0 if (not self.rtsp_url or self.rtsp_url == "0") else self.rtsp_url
            print(f"[AI Vision] Đang kết nối tới Camera nguồn: {source}...")
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                print("[AI Vision] Không thể mở camera. Đang chờ kết nối...")
                retries = 0
                while self.is_running and retries < 5:
                    sim_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(sim_frame, "AI CAMERA // STANDBY", (140, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    cv2.putText(sim_frame, "DANG CHO TIN HIEU CAMERA...", (125, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 1)
                    cv2.putText(sim_frame, f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S')}", (165, 295), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
                    with self.lock:
                        self.latest_annotated_frame = sim_frame
                    time.sleep(1)
                    retries += 1
                continue

            print("[AI Vision] Kết nối luồng Camera thành công!")

            while self.is_running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print("[AI Vision] Mất tín hiệu Camera hoặc frame rỗng. Đang khởi tạo lại kết nối...")
                    break

                # Lưu bản sao ảnh gốc chưa vẽ để lưu làm bằng chứng điểm danh
                original_frame = frame.copy()
                annotated_frame = frame.copy()

                try:
                    # Dự đoán với mô hình YOLOv11 (ngưỡng tin cậy conf=0.7)
                    results = self.model.predict(frame, conf=0.7, verbose=False)
                    
                    if len(results) > 0 and len(results[0].boxes) > 0:
                        for box in results[0].boxes:
                            # Tọa độ khung nhận diện
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls_id = int(box.cls[0])
                            raw_name = self.model.names.get(cls_id, f"ID_{cls_id}")

                            # Ánh xạ tên nhãn sang tên đầy đủ
                            full_name = self.get_display_name(raw_name)

                            # 1. Vẽ khung chữ nhật 2D phẳng
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (40, 200, 100), 2)

                            # 2. Vẽ nhãn nền với tên đầy đủ và độ chính xác
                            label = f"{full_name} ({int(conf * 100)}%)"
                            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                            label_ymin = max(0, y1 - text_h - 10)
                            cv2.rectangle(annotated_frame, (x1, label_ymin), (x1 + text_w + 10, y1), (40, 200, 100), -1)
                            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                            # 3. Kiểm tra cooldown chống spam nhận diện cho từng người
                            current_time = time.time()
                            last_time = self.last_detection_times.get(full_name, 0)

                            if (current_time - last_time) >= self.cooldown_seconds:
                                self.last_detection_times[full_name] = current_time
                                print(f"[AI Vision] Nhận diện thành công: {full_name} ({conf:.2f})")

                                # Gọi callback trong một thread riêng để không làm nghẽn luồng đọc camera
                                if self.on_face_detected:
                                    threading.Thread(
                                        target=self.on_face_detected,
                                        args=(full_name, original_frame.copy()),
                                        daemon=True
                                    ).start()
                except Exception as e:
                    print(f"[AI Vision] Lỗi trong quá trình suy luận AI: {e}")
                    annotated_frame = frame

                # Cập nhật frame mới nhất cho luồng web
                with self.lock:
                    self.latest_annotated_frame = annotated_frame

                time.sleep(0.01)

            cap.release()
            time.sleep(2)

    def get_annotated_frame(self):
        """
        Trả về frame mới nhất đã vẽ tên đầy đủ (dạng numpy ndarray BGR).
        """
        with self.lock:
            if self.latest_annotated_frame is not None:
                return self.latest_annotated_frame.copy()
            return None

    def stop(self):
        """
        Dừng luồng xử lý video an toàn.
        """
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
