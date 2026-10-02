#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// =============================================================================
// CẤU HÌNH PHẦN CỨNG & SƠ ĐỒ CHÂN (PINOUT)
// =============================================================================

// 1. Cảm biến vân tay quang học AS608 (Giao tiếp UART2)
// Sơ đồ kết nối chéo:
// ESP32 RX2 (GPIO 16) <--- AS608 TX
// ESP32 TX2 (GPIO 17) ---> AS608 RX
#define AS608_RX_PIN        16      // Chân RX2 của ESP32 kết nối với chân TX của AS608
#define AS608_TX_PIN        17      // Chân TX2 của ESP32 kết nối với chân RX của AS608
#define AS608_TCH_PIN       32      // Chân cảm ứng phát hiện ngón tay (Touch / Interrupt)
#define AS608_BAUD_RATE     57600   // Tốc độ Baud mặc định của AS608

// 2. Màn hình LCD 1602 giao tiếp I2C
#define LCD_SDA_PIN         21      // Chân dữ liệu I2C SDA
#define LCD_SCL_PIN         22      // Chân xung nhịp I2C SCL
#define LCD_I2C_ADDR        0x27    // Địa chỉ I2C mặc định (thường là 0x27 hoặc 0x3F)
#define LCD_COLS            16      // Số cột của LCD
#define LCD_ROWS            2       // Số dòng của LCD

// 3. Động cơ Servo chốt khóa cửa (Điều khiển PWM)
#define SERVO_PIN           13      // Chân phát xung PWM điều khiển Servo
#define SERVO_LOCK_ANGLE    0       // Góc đóng chốt cửa (độ)
#define SERVO_UNLOCK_ANGLE  90      // Góc mở chốt cửa (độ)
#define DOOR_UNLOCK_TIME_MS 5000    // Thời gian giữ mở khóa trước khi tự động đóng (ms)

// =============================================================================
// CẤU HÌNH KẾT NỐI MẠNG & SERVER BACKEND
// =============================================================================

// Cấu hình mạng WiFi
#define WIFI_SSID           "YOUR_WIFI_SSID"
#define WIFI_PASS           "YOUR_WIFI_PASSWORD"
#define WIFI_TIMEOUT_MS     10000   // Thời gian timeout khi kết nối WiFi (ms)

// Cấu hình URL Server Backend / API
#define SERVER_URL          "http://192.168.1.100:5000"

#endif // CONFIG_H
