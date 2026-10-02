#include "lcd_module.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// Khởi tạo đối tượng LCD với địa chỉ I2C và kích thước từ config.h
static LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);

void LCDModule::init() {
    // Khởi tạo bus I2C với chân SDA và SCL được cấu hình cho ESP32
    Wire.begin(LCD_SDA_PIN, LCD_SCL_PIN);
    
    // Khởi động màn hình LCD
    lcd.init();
    lcd.backlight();
    lcd.clear();
}

void LCDModule::printMessage(const String& line1, const String& line2) {
    // Đệm thêm khoảng trắng để ghi đè sạch các ký tự cũ mà không cần gọi lcd.clear() (tránh giật/nhấp nháy)
    String paddedLine1 = line1;
    while (paddedLine1.length() < LCD_COLS) {
        paddedLine1 += ' ';
    }
    lcd.setCursor(0, 0);
    lcd.print(paddedLine1.substring(0, LCD_COLS));

    String paddedLine2 = line2;
    while (paddedLine2.length() < LCD_COLS) {
        paddedLine2 += ' ';
    }
    lcd.setCursor(0, 1);
    lcd.print(paddedLine2.substring(0, LCD_COLS));
}

void LCDModule::clear() {
    lcd.clear();
}

void LCDModule::setBacklight(bool enable) {
    if (enable) {
        lcd.backlight();
    } else {
        lcd.noBacklight();
    }
}
