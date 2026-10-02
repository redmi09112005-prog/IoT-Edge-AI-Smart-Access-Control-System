#ifndef SERVO_MODULE_H
#define SERVO_MODULE_H

#include <Arduino.h>

/**
 * @brief Khởi tạo module Servo và cấu hình timer PWM cho ESP32.
 */
void servo_init();

/**
 * @brief Mở khóa cửa:
 * 1. Gọi hàm hiển thị LCD để báo "Welcome" / user_name.
 * 2. Quay servo tới góc 90 độ (mở cửa).
 * 3. Chờ 3 giây rồi quay về góc 0 độ (đóng cửa).
 * 
 * @param user_name Tên người dùng cần hiển thị chào mừng.
 */
void unlock_door(String user_name);

#endif // SERVO_MODULE_H
