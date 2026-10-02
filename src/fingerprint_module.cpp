#include "fingerprint_module.h"
#include "config.h"
#include "lcd_module.h"
#include "servo_module.h"
#include <Adafruit_Fingerprint.h>

// Sử dụng cổng HardwareSerial 2 của ESP32 để giao tiếp với AS608
static HardwareSerial fpSerial(2);
static Adafruit_Fingerprint finger(&fpSerial);

bool init_fingerprint() {
    // Cấu hình chân cảm ứng TCH làm ngõ vào
    pinMode(AS608_TCH_PIN, INPUT);

    // Khởi động HardwareSerial(2) với Baudrate và chân RX, TX từ config.h
    fpSerial.begin(AS608_BAUD_RATE, SERIAL_8N1, AS608_RX_PIN, AS608_TX_PIN);

    // Kiểm tra kết nối với cảm biến vân tay
    if (finger.verifyPassword()) {
        return true;
    } else {
        // Cảm biến không phản hồi hoặc sai mật khẩu giao tiếp
        LCDModule::printMessage("AS608 Error!", "Check Sensor");
        return false;
    }
}

int scan_fingerprint() {
    // TỐI ƯU HIỆU NĂNG:
    // CHỈ tiến hành giao tiếp UART với cảm biến nếu chân TCH đang ở mức HIGH (có ngón tay chạm)
    if (digitalRead(AS608_TCH_PIN) != HIGH) {
        return -1;
    }

    // 1. Chụp ảnh ngón tay
    uint8_t p = finger.getImage();
    if (p != FINGERPRINT_OK) {
        return -1;
    }

    // 2. Chuyển đổi hình ảnh sang file đặc trưng (Template)
    p = finger.image2Tz();
    if (p != FINGERPRINT_OK) {
        LCDModule::printMessage("Scan Error", "Please Try Again");
        delay(1500);
        return -1;
    }

    // 3. Tìm kiếm trong bộ nhớ vân tay của AS608
    p = finger.fingerSearch();
    if (p == FINGERPRINT_OK) {
        // Nhận diện thành công: Mở khóa và chào mừng
        String userName = "User #" + String(finger.fingerID);
        unlock_door(userName);
        return finger.fingerID;
    } else if (p == FINGERPRINT_NOTFOUND) {
        // Không tìm thấy vân tay trong dữ liệu lưu trữ
        LCDModule::printMessage("Access Denied", "Invalid Finger");
        delay(2000);
        return -1;
    } else {
        // Lỗi giao tiếp khác
        LCDModule::printMessage("Auth Error", "Please Retry");
        delay(1500);
        return -1;
    }
}
