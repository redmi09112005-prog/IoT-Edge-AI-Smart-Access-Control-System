import sqlite3
import os
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_path="attendance.db"):
        """
        Khởi tạo DatabaseHandler với đường dẫn cơ sở dữ liệu SQLite.
        Tự động tạo database và bảng nếu chưa tồn tại.
        """
        self.db_path = db_path
        self.init_db()

    def _get_connection(self):
        """
        Tạo kết nối mới đến SQLite hỗ trợ đa luồng (thích hợp cho Flask/SocketIO).
        """
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """
        Tạo bảng attendance nếu chưa tồn tại với các trường:
        - id: Khóa chính tự tăng
        - name: Tên người điểm danh
        - method: Phương thức điểm danh ('Vân tay' hoặc 'AI')
        - time: Thời gian điểm danh định dạng YYYY-MM-DD HH:MM:SS
        - image_path: Đường dẫn ảnh chụp bằng chứng (nếu có)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    method TEXT NOT NULL,
                    time TEXT NOT NULL,
                    image_path TEXT
                )
            """)
            conn.commit()

    def log_attendance(self, name: str, method: str, image_path: str = None, log_time: str = None) -> int:
        """
        Ghi nhận một bản ghi điểm danh mới vào cơ sở dữ liệu.
        
        :param name: Tên người điểm danh.
        :param method: Phương thức xác thực ('Vân tay' hoặc 'AI').
        :param image_path: Đường dẫn lưu ảnh chụp khuôn mặt (nếu dùng AI).
        :param log_time: Thời gian điểm danh (mặc định lấy thời điểm hiện tại).
        :return: ID của bản ghi vừa thêm.
        """
        if not log_time:
            log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO attendance (name, method, time, image_path)
                VALUES (?, ?, ?, ?)
            """, (name, method, log_time, image_path))
            conn.commit()
            return cursor.lastrowid

    def get_recent_logs(self, limit: int = 10) -> list:
        """
        Lấy danh sách các bản ghi điểm danh mới nhất.
        
        :param limit: Số lượng bản ghi tối đa cần lấy.
        :return: Danh sách các bản ghi dạng dictionary.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, method, time, image_path
                FROM attendance
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_today_on_time(self, target_date: str = None) -> list:
        """
        Lấy danh sách người điểm danh ĐÚNG GIỜ hôm nay (lần điểm danh đầu tiên trong ngày <= 08:00:00).
        """
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, MIN(time) as checkin_time, method, image_path
                FROM attendance
                WHERE date(time) = ?
                GROUP BY name
                HAVING time(MIN(time)) <= '08:00:00'
                ORDER BY checkin_time ASC
            """, (target_date,))
            return [dict(row) for row in cursor.fetchall()]

    def get_today_late(self, target_date: str = None) -> list:
        """
        Lấy danh sách người điểm danh MUỘN hôm nay (lần điểm danh đầu tiên trong ngày > 08:00:00).
        """
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, MIN(time) as checkin_time, method, image_path
                FROM attendance
                WHERE date(time) = ?
                GROUP BY name
                HAVING time(MIN(time)) > '08:00:00'
                ORDER BY checkin_time ASC
            """, (target_date,))
            return [dict(row) for row in cursor.fetchall()]

    def get_monthly_statistics(self, target_month: str = None) -> list:
        """
        Thống kê tần suất điểm danh của từng người trong tháng:
        - Tổng số ngày điểm danh
        - Số lần đúng giờ (<= 08:00)
        - Số lần đi muộn (> 08:00)
        - Tỷ lệ đúng giờ (%)
        """
        if not target_month:
            target_month = datetime.now().strftime("%Y-%m")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                WITH daily_first AS (
                    SELECT 
                        name,
                        date(time) as log_date,
                        MIN(time) as first_checkin
                    FROM attendance
                    WHERE strftime('%Y-%m', time) = ?
                    GROUP BY name, date(time)
                )
                SELECT 
                    name,
                    COUNT(*) as total_days,
                    SUM(CASE WHEN time(first_checkin) <= '08:00:00' THEN 1 ELSE 0 END) as on_time_count,
                    SUM(CASE WHEN time(first_checkin) > '08:00:00' THEN 1 ELSE 0 END) as late_count
                FROM daily_first
                GROUP BY name
                ORDER BY on_time_count DESC, late_count ASC
            """, (target_month,))
            
            results = []
            for row in cursor.fetchall():
                data = dict(row)
                total = data['total_days']
                on_time = data['on_time_count']
                data['on_time_rate'] = round((on_time / total * 100), 1) if total > 0 else 0.0
                results.append(data)
            return results
