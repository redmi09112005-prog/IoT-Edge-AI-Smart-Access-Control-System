#include "network_module.h"
#include "config.h"
#include "lcd_module.h"
#include "servo_module.h"

#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// WebServer chạy tại cổng 80 chuẩn HTTP
static WebServer server(80);

void network_init() {
    // 1. Kết nối WiFi
    LCDModule::printMessage("Connecting WiFi", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    unsigned long startAttemptTime = millis();

    // Chờ kết nối WiFi với cơ chế timeout cấu hình từ config.h
    while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_TIMEOUT_MS) {
        delay(500);
    }

    if (WiFi.status() == WL_CONNECTED) {
        // Kết nối thành công: In địa chỉ IP cục bộ lên LCD
        String ipStr = WiFi.localIP().toString();
        LCDModule::printMessage("WiFi Connected!", ipStr);
        delay(2000);
    } else {
        // Báo lỗi kết nối nếu quá thời gian chờ
        LCDModule::printMessage("WiFi Failed!", "Check AP/Router");
        delay(2000);
    }

    // 2. Cấu hình định tuyến (Route) WebServer
    // Route: GET /open_door?name=...
    server.on("/open_door", HTTP_GET, []() {
        String userName = "AI User";
        if (server.hasArg("name") && server.arg("name").length() > 0) {
            userName = server.arg("name");
        }

        // Tạo chuỗi JSON phản hồi
        String jsonResponse = "{\"status\":\"success\",\"message\":\"Door unlocked\",\"user\":\"" + userName + "\"}";
        
        // Phản hồi HTTP 200 JSON cho client trước để tránh timeout kết nối mạng
        server.send(200, "application/json", jsonResponse);

        // Kích hoạt chu trình mở cửa, hiển thị lời chào trên LCD và xoay servo
        unlock_door(userName);
    });

    // Bắt đầu lắng nghe request
    server.begin();
}

void network_handle() {
    // Luôn xử lý các kết nối HTTP đến trong vòng lặp chính
    server.handleClient();
}

bool send_attendance_log(int finger_id) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[Network] WiFi not connected. Cannot send log.");
        return false;
    }

    HTTPClient http;
    // Endpoint gửi log điểm danh: <SERVER_URL>/api/attendance
    String endpoint = String(SERVER_URL) + "/api/attendance";
    
    http.begin(endpoint);
    http.addHeader("Content-Type", "application/json");

    // Chuẩn bị payload JSON
    String jsonPayload = "{\"finger_id\":" + String(finger_id) + "}";

    int httpResponseCode = http.POST(jsonPayload);
    bool isSuccess = false;

    if (httpResponseCode > 0) {
        Serial.printf("[Network] Attendance log sent, HTTP code: %d\n", httpResponseCode);
        if (httpResponseCode == HTTP_CODE_OK || httpResponseCode == HTTP_CODE_CREATED) {
            isSuccess = true;
        }
    } else {
        Serial.printf("[Network] POST failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    return isSuccess;
}
