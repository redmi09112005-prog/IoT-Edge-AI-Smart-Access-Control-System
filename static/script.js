// Khởi tạo kết nối Socket.IO thời gian thực
const socket = io();

// Hàm phát âm thanh thông báo nhẹ nhàng
function playNotificationChime() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.08); // A5

        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.25);

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + 0.25);
    } catch (e) {
        // Trình duyệt có thể hạn chế autoplay khi chưa click
    }
}

// Lắng nghe sự kiện điểm danh mới từ máy chủ
socket.on('new_attendance', function(data) {
    console.log('[Socket] Nhận bản ghi điểm danh mới:', data);
    
    const tbody = document.getElementById('attendance-tbody');
    if (!tbody) return;

    // Phát chuông nhẹ nhàng
    playNotificationChime();

    // Xóa hàng thông báo trống nếu có
    const emptyRow = document.getElementById('empty-row');
    if (emptyRow) emptyRow.remove();

    // Tạo hàng mới
    const tr = document.createElement('tr');
    tr.className = 'row-new';

    const isAI = (data.method && data.method.toUpperCase().includes('AI'));
    const methodBadge = isAI 
        ? `<span class="badge-pill badge-ai">Khuôn mặt AI</span>` 
        : `<span class="badge-pill badge-fingerprint">Vân tay</span>`;

    let actionBtnHtml = '';
    if (data.image_url) {
        actionBtnHtml = `<button class="btn-view" onclick="openProofModal('${data.image_url}', '${data.name}')"><span>🖼️</span> Xem ảnh</button>`;
    } else {
        actionBtnHtml = `<span class="btn-empty">—</span>`;
    }

    tr.innerHTML = `
        <td style="color: var(--text-secondary); font-size: 12px;">${data.time || 'Vừa xong'}</td>
        <td class="person-name">${data.name || 'Không xác định'}</td>
        <td>${methodBadge}</td>
        <td>${actionBtnHtml}</td>
    `;

    // Chèn lên đầu bảng
    tbody.prepend(tr);

    // Gỡ class hiệu ứng sau 2 giây
    setTimeout(() => {
        tr.classList.remove('row-new');
    }, 2000);
});

// Điều khiển Modal xem ảnh bằng chứng
function openProofModal(imageUrl, userName) {
    const modal = document.getElementById('proof-modal');
    const modalImg = document.getElementById('modal-img');
    const modalTitle = document.getElementById('modal-title');

    if (modal && modalImg) {
        modalImg.src = imageUrl;
        if (modalTitle) modalTitle.innerText = `Bằng Chứng Điểm Danh: ${userName}`;
        modal.classList.add('show');
    }
}

function closeProofModal() {
    const modal = document.getElementById('proof-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// Đóng modal khi bấm ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeProofModal();
});
