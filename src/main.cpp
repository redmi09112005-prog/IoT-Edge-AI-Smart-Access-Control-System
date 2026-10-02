#include <Arduino.h>
#include "config.h"
#include "lcd_module.h"
#include "servo_module.h"
#include "fingerprint_module.h"
#include "network_module.h"

void setup() {
    Serial.begin(115200);

    // 1. Khởi tạo LCD đầu tiên để có thể hiển thị thông báo/lỗi phần cứng sau đó
    LCDModule::init();
    LCDModule::printMessage("System Booting", "Please wait...");
    delay(1000);

    // 2. Khởi tạo Servo chốt cửa (đưa về vị trí khóa an toàn 0 độ)
    servo_init();

    // 3. Khởi tạo cảm biến vân tay AS608 (báo lỗi lên LCD nếu không tìm thấy cảm biến)
    init_fingerprint();

    // 4. Khởi tạo kết nối WiFi và WebServer nhận lệnh từ AI
    network_init();

    // Hệ thống hoàn tất khởi động và sẵn sàng hoạt động
    LCDModule::printMessage("Smart Door Ready", "Scan Fingerprint");
}

void loop() {
    // 1. Lắng nghe liên tục các lệnh mở cửa từ Camera AI qua WebServer
    network_handle();

    // 2. Kiểm tra cảm biến vân tay cục bộ
    int finger_id = scan_fingerprint();
    if (finger_id > 0) {
        // Gửi dữ liệu điểm danh lên máy chủ
        send_attendance_log(finger_id);

        // Khôi phục lại trạng thái màn hình chờ sau chu trình mở cửa
        LCDModule::printMessage("Smart Door Ready", "Scan Fingerprint");
    }
}
