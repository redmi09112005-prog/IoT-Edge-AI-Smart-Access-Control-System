# Hệ Thống Điểm Danh Thông Minh & Kiểm Soát Cửa Tự Động

Dự án xây dựng hệ thống kiểm soát ra vào và điểm danh tự động, kết hợp giữa phần cứng nhúng **ESP32**, thị giác máy tính **AI (YOLOv11)** và máy chủ **Flask Dashboard** quản trị theo thời gian thực.

---

## 1. Tổng Quan Hệ Thống

Hệ thống giải quyết bài toán kiểm soát an ninh cửa và chấm công tự động thông qua hai phương thức xác thực:
* **Nhận diện khuôn mặt qua Camera**: Sử dụng mô hình AI nhận diện người dùng từ xa, tự động ra lệnh mở cửa và lưu ảnh bằng chứng.
* **Xác thực vân tay tại chỗ**: Sử dụng cảm biến vân tay quang học kết nối trực tiếp với ESP32 để mở chốt cửa khi không đứng trước camera.
* **Quản trị trực quan**: Toàn bộ dữ liệu điểm danh được đồng bộ tức thì lên giao diện web thời gian thực, hỗ trợ phân loại đúng giờ, đi muộn và báo cáo tần suất trong tháng.

---

## 2. Kiến Trúc Hệ Thống & Các Module Chức Năng

Hệ thống được thiết kế theo mô hình phân tầng module hóa rõ ràng, gồm 4 khối chính:

```plaintext
[ CAMERA IP / WEBCAM ]          [ CẢM BIẾN VÂN TAY / SERVO / LCD ]
         │                                       │
         ▼                                       ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│   MODULE AI VISION      │             │   MODULE NHÚNG (ESP32)  │
│ - Đọc luồng video       │             │ - Quản lý cảm biến      │
│ - Nhận diện YOLOv11     │             │ - Điều khiển chốt servo │
│ - Lọc spam & Đổi tên    │             │ - Hiển thị LCD 1602     │
└────────────┬────────────┘             └────────────┬────────────┘
             │                                       │
             │ HTTP GET (Mở cửa)                     │ HTTP POST (Gửi log)
             ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MODULE MÁY CHỦ TRUNG TÂM (BACKEND)            │
│  - Xử lý API điều phối hệ thống                                 │
│  - Lưu trữ cơ sở dữ liệu SQLite & Ảnh bằng chứng                │
│  - Cầu nối truyền tin thời gian thực qua WebSocket              │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼ WebSocket (Cập nhật tức thì)
┌─────────────────────────────────────────────────────────────────┐
│                   MODULE GIAO DIỆN QUẢN TRỊ (DASHBOARD)         │
│  - Trang chủ: Xem camera trực tiếp & Nhật ký điểm danh          │
│  - Trang Đúng giờ: Lọc danh sách check-in trước hoặc đúng 8h00  │
│  - Trang Đi muộn: Cảnh báo các trường hợp check-in sau 8h00     │
│  - Trang Tần suất: Báo cáo số ngày làm việc & tỷ lệ chuyên cần  │
└─────────────────────────────────────────────────────────────────┘
```

### Chi tiết các module:

1. **Module Nhúng & Điều Khiển Cục Bộ (ESP32)**:
   * **Phân hệ điều khiển chốt khóa**: Điều khiển góc quay động cơ Servo để rút/đẩy chốt cửa an toàn.
   * **Phân hệ sinh trắc học vân tay**: Đọc và đối chiếu dữ liệu vân tay từ cảm biến AS608, sử dụng ngắt cảm ứng khi có ngón tay chạm vào để tối ưu tốc độ xử lý.
   * **Phân hệ hiển thị tại chỗ**: Điều khiển màn hình LCD 1602 thông báo trạng thái mạng, mã lỗi và hiển thị lời chào kèm tên người dùng.
   * **Phân hệ mạng cục bộ**: Thiết lập WebServer đón nhận lệnh mở cửa từ AI và làm HTTP Client gửi mã vân tay về máy chủ.

2. **Module Thị Giác Máy Tính (AI Vision)**:
   * **Nhận diện khuôn mặt**: Ứng dụng mô hình YOLOv11n nhận diện khuôn mặt người dùng từ luồng camera.
   * **Bộ chuyển đổi định danh (Name Mapping)**: Chuyển đổi mã nhãn mô hình sang họ tên đầy đủ hiển thị trên hệ thống (ví dụ: `long` thành `Tran The Long`).
   * **Cơ chế chống spam (Cooldown)**: Tự động khóa nhịp nhận diện trong 5 giây cho mỗi đối tượng để tránh việc ghi nhận điểm danh liên tục.

3. **Module Máy Chủ Trung Tâm (Backend Server)**:
   * Cung cấp các cổng giao tiếp API hai chiều giữa phần cứng và máy chủ.
   * Lưu trữ nhật ký điểm danh vào cơ sở dữ liệu SQLite và tự động lưu ảnh chụp bằng chứng khi nhận diện bằng AI.
   * Sử dụng WebSocket để phát dữ liệu mới nhất tới trình duyệt ngay khi có sự kiện mở cửa.

4. **Module Giao Diện Giám Sát (Frontend Dashboard)**:
   * Thiết kế theo phong cách đồ họa phẳng 2D hiện đại, tối giản và thân thiện.
   * Hiển thị luồng video kèm khung nhận diện tên người dùng.
   * Tự động bổ sung lượt điểm danh mới vào bảng mà không cần tải lại trang.

---

## 3. Luồng Xử Lý Sự Kiện (Event Processing Workflow)

### Kịch bản 1: Mở cửa & Điểm danh qua Khuôn Mặt (AI Camera)
1. Người dùng đứng trước Camera.
2. Module AI Vision phát hiện khuôn mặt, nhận dạng thành công danh tính và độ tin cậy.
3. Bộ lọc kiểm tra thời gian cooldown: Nếu thỏa mãn, trích xuất họ tên đầy đủ và lưu ảnh chụp khuôn mặt làm bằng chứng.
4. Máy chủ gửi một lệnh mạng (HTTP GET) tới ESP32 yêu cầu mở cửa cho người này.
5. ESP32 nhận lệnh:
   * Hiển thị lời chào lên màn hình LCD.
   * Kích hoạt động cơ Servo xoay mở chốt cửa trong 3 giây rồi tự động đóng lại.
6. Máy chủ ghi bản ghi vào cơ sở dữ liệu SQLite và phát tín hiệu WebSocket để Dashboard tự động hiển thị dòng điểm danh mới trên đầu bảng.

### Kịch bản 2: Mở cửa & Điểm danh qua Cảm Biến Vân Tay
1. Người dùng đặt ngón tay lên cảm biến vân tay ở cửa.
2. Chân cảm ứng phát hiện ngón tay kích hoạt ngắt, ESP32 tiến hành quét và đối chiếu với bộ nhớ cảm biến.
3. Nếu vân tay hợp lệ:
   * ESP32 kích hoạt động cơ Servo mở chốt cửa và hiển thị lời chào trên LCD.
   * ESP32 gửi một gói tin mạng (HTTP POST) kèm ID vân tay lên máy chủ.
4. Máy chủ nhận dữ liệu, ghi nhật ký điểm danh vào cơ sở dữ liệu SQLite với phương thức "Vân tay".
5. Máy chủ phát tín hiệu WebSocket đẩy bản ghi mới lên Dashboard theo thời gian thực.

---

## 4. Sơ Đồ Đấu Nối Phần Cứng

| Thiết bị | Chân thiết bị | Chân ESP32 | Chức năng |
| :--- | :--- | :--- | :--- |
| **Cảm biến AS608** | TX / RX | GPIO16 / GPIO17 | Cổng giao tiếp nối tiếp UART2 |
| | TCH (Touch) | GPIO32 | Tín hiệu ngắt khi chạm ngón tay |
| **Màn hình LCD 1602** | SDA / SCL | GPIO21 / GPIO22 | Bus giao tiếp I2C |
| **Động cơ Servo** | Dây xung PWM | GPIO13 | Điều khiển góc chốt khóa |

---

## 5. Cấu Trúc Thư Mục Dự Án

```plaintext
DACN/
├── include/                     # Khai báo cấu hình phần cứng và các module nhúng
│   ├── config.h                 # Định nghĩa chân cắm, thông số WiFi, địa chỉ Server
│   ├── lcd_module.h             # Module điều khiển màn hình LCD 1602
│   ├── servo_module.h           # Module điều khiển động cơ servo chốt cửa
│   ├── fingerprint_module.h     # Module cảm biến vân tay AS608
│   └── network_module.h         # Module kết nối mạng và WebServer trên ESP32
├── src/                         # Triển khai mã nguồn C++ cho ESP32
│   ├── main.cpp                 # Điểm khởi chạy chính của vi điều khiển
│   ├── lcd_module.cpp
│   ├── servo_module.cpp
│   ├── fingerprint_module.cpp
│   └── network_module.cpp
├── platformio.ini               # Cấu hình dự án PlatformIO
│
├── models/
│   └── dacn.pt                  # File mô hình YOLOv11n nhận diện khuôn mặt
├── captured_proofs/             # Thư mục chứa ảnh bằng chứng chụp khi nhận diện
├── templates/                   # Giao diện web HTML
│   ├── index.html               # Trang chủ: Camera trực tiếp & Nhật ký thời gian thực
│   ├── on_time.html             # Danh sách điểm danh đúng giờ hôm nay
│   ├── late.html                # Báo cáo điểm danh muộn hôm nay
│   └── statistics.html          # Bảng thống kê tần suất trong tháng
├── static/
│   ├── style.css                # Định kiểu giao diện đồ họa phẳng 2D
│   └── script.js                # Xử lý kết nối WebSocket và hiển thị dữ liệu
├── app.py                       # Máy chủ Flask trung tâm điều phối hệ thống
├── ai_vision.py                 # Module đọc camera và nhận diện khuôn mặt
├── db_handler.py                # Module thao tác cơ sở dữ liệu SQLite
└── requirements.txt             # Danh sách thư viện Python cần dùng
```

---

## 6. Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Nạp chương trình cho ESP32
1. Mở thư mục dự án bằng VS Code (đã cài tiện ích PlatformIO).
2. Vào file `include/config.h`, chỉnh lại tên Wi-Fi, mật khẩu và IP của máy tính chạy server:
   ```cpp
   #define WIFI_SSID   "TEN_WIFI"
   #define WIFI_PASS   "MAT_KHAU"
   #define SERVER_URL  "http://IP_MAY_TINH:5000"
   ```
3. Cắm cáp USB nối ESP32 với máy tính, bấm nút **Upload** trên PlatformIO để nạp code.
4. Màn hình LCD hoặc Serial Monitor sẽ hiển thị địa chỉ IP của ESP32 sau khi kết nối thành công (ví dụ: `192.168.1.50`).

### 2. Khởi chạy Máy chủ AI & Dashboard
1. Cài đặt các thư viện Python:
   ```bash
   pip install -r requirements.txt
   ```
2. Cấu hình IP của ESP32 trong file `app.py`:
   ```python
   ESP32_IP = "192.168.1.50"   # Điền địa chỉ IP của ESP32
   ```
3. Khởi chạy máy chủ:
   ```bash
   python app.py
   ```
4. Mở trình duyệt web và truy cập vào:
   * **Trang chủ & Camera**: `http://localhost:5000/`
   * **Xem danh sách đúng giờ**: `http://localhost:5000/on-time`
   * **Xem danh sách đi muộn**: `http://localhost:5000/late`
   * **Báo cáo tần suất tháng**: `http://localhost:5000/statistics`

---

## 7. Quy Chuẩn Đánh Giá Chuyên Cần

Hệ thống tự động tính toán dựa trên lần điểm danh đầu tiên trong ngày của từng nhân sự:
* **Đúng giờ**: Thời điểm check-in lần đầu diễn ra lúc **08:00:00 sáng hoặc sớm hơn**.
* **Đi muộn**: Thời điểm check-in lần đầu diễn ra **sau 08:00:00 sáng**.
* **Tỷ lệ đúng giờ trong tháng**:
  `Tỷ lệ đúng giờ (%) = (Số ngày đi làm đúng giờ / Tổng số ngày có mặt) * 100%`
