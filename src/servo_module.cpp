#include "servo_module.h"
#include "config.h"
#include "lcd_module.h"
#include <ESP32Servo.h>

// Đối tượng điều khiển động cơ Servo
static Servo doorServo;

void servo_init() {
    // Phân bổ các bộ định thời (Hardware Timers) chuẩn cho ESP32 PWM
    // Giúp tránh xung đột timer giữa Servo với các tác vụ PWM khác
    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    ESP32PWM::allocateTimer(2);
    ESP32PWM::allocateTimer(3);

    // Cài đặt tần số tiêu chuẩn cho Servo (50Hz)
    doorServo.setPeriodHertz(50);

    // Gắn chân PWM từ config.h (GPIO13) với độ rộng xung chuẩn (500us - 2400us)
    doorServo.attach(SERVO_PIN, 500, 2400);

    // Mặc định ban đầu đưa servo về góc khóa (0 độ)
    doorServo.write(SERVO_LOCK_ANGLE);
}

void unlock_door(String user_name) {
    // 1. Hiển thị thông báo trên LCD: Dòng 1 "Welcome", Dòng 2: tên người dùng
    LCDModule::printMessage("Welcome", user_name);

    // 2. Quay servo tới góc 90 độ (Mở cửa)
    doorServo.write(SERVO_UNLOCK_ANGLE);

    // 3. Chờ 3 giây rồi quay về góc 0 độ (Đóng cửa)
    delay(3000);
    doorServo.write(SERVO_LOCK_ANGLE);
}
