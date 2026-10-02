#ifndef FINGERPRINT_MODULE_H
#define FINGERPRINT_MODULE_H

#include <Arduino.h>

/**
 * @brief Khởi tạo module vân tay AS608 qua HardwareSerial(2) và kiểm tra kết nối cảm biến.
 * @return true nếu kết nối thành công, false nếu lỗi (kèm báo lỗi trên LCD).
 */
bool init_fingerprint();

/**
 * @brief Kiểm tra và quét vân tay người dùng.
 * Hàm CHỈ thực hiện giao tiếp UART với cảm biến khi chân TCH ở mức HIGH.
 * - Nhận diện thành công: Gọi unlock_door() và trả về ID vân tay.
 * - Nhận diện thất bại hoặc lỗi: Báo lỗi lên LCD và trả về -1.
 * 
 * @return int ID của vân tay nếu khớp (> 0), -1 nếu không có ngón tay hoặc xác thực thất bại.
 */
int scan_fingerprint();

#endif // FINGERPRINT_MODULE_H
