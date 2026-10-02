#ifndef LCD_MODULE_H
#define LCD_MODULE_H

#include <Arduino.h>
#include "config.h"

/**
 * @brief Module điều khiển màn hình LCD 1602 giao tiếp I2C.
 */
class LCDModule {
public:
    /**
     * @brief Khởi tạo giao tiếp I2C trên ESP32 (SDA, SCL) và cấu hình màn hình LCD.
     */
    static void init();

    /**
     * @brief In thông báo hiển thị trên 2 dòng của LCD.
     * @param line1 Nội dung dòng 1 (tối đa 16 ký tự).
     * @param line2 Nội dung dòng 2 (tối đa 16 ký tự, mặc định để trống).
     */
    static void printMessage(const String& line1, const String& line2 = "");

    /**
     * @brief Xóa toàn bộ nội dung hiển thị trên màn hình LCD.
     */
    static void clear();

    /**
     * @brief Bật hoặc tắt đèn nền (backlight) của màn hình LCD.
     * @param enable true để bật, false để tắt.
     */
    static void setBacklight(bool enable);
};

#endif // LCD_MODULE_H
