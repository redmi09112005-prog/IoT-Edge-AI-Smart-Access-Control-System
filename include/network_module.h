#ifndef NETWORK_MODULE_H
#define NETWORK_MODULE_H

#include <Arduino.h>

/**
 * @brief Khởi tạo kết nối WiFi, in IP ra màn hình LCD và cấu hình WebServer cổng 80.
 */
void network_init();

/**
 * @brief Xử lý lắng nghe các yêu cầu HTTP gửi đến WebServer (gọi trong hàm loop()).
 */
void network_handle();

/**
 * @brief Gửi nhật ký điểm danh (attendance log) lên Server Backend qua giao thức HTTP POST.
 * 
 * @param finger_id ID vân tay được xác thực thành công.
 * @return true nếu gửi thành công (HTTP 200/201), false nếu thất bại hoặc mất kết nối.
 */
bool send_attendance_log(int finger_id);

#endif // NETWORK_MODULE_H
