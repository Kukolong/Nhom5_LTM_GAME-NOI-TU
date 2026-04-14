# 🔗 Word Chain Game — Game Nối Từ Tiếng Việt

Một trò chơi nối từ đa người chơi sử dụng kiến trúc **client-server TCP** với giao diện desktop GUI.

---

## 📋 Mục Lục

- [Tính Năng](#tính-năng)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
- [Kiểm Thử](#kiểm-thử)
- [Cấu Hình](#cấu-hình)

---

## ✨ Tính Năng

### Tính Năng Chung
- Kết nối TCP giữa client và server
- Xác thực người chơi (tên duy nhất)
- Ghép đôi tự động và chơi theo lượt
- Kiểm tra từ điển tiếng Việt theo thời gian thực
- Hỗ trợ nhiều client kết nối đồng thời

### Luật Chơi
- Mỗi người chơi nhập một **cụm từ tiếng Việt** gồm 2 từ trở lên
- Từ đầu tiên của cụm mới phải **trùng với từ cuối** của cụm trước
- Cụm từ nhập phải **tồn tại trong từ điển** tiếng Việt
- **Không được lặp lại** cụm từ đã dùng trong ván
- Mỗi lượt có **15 giây** để trả lời, hết giờ thua cuộc

> **Ví dụ chuỗi hợp lệ:**
> ```
> con vịt → vịt trời → trời đêm → đêm tối → tối đen
> ```

---

## 🖥️ Yêu Cầu Hệ Thống

- **Python** 3.6 trở lên
- **socket** — Module socket chuẩn của Python
- **threading** — Module threading chuẩn của Python
- **tkinter** — Thư viện GUI chuẩn của Python
- Chỉ sử dụng thư viện chuẩn, **không cần cài thêm dependencies**

---

## ⚙️ Cài Đặt

### 1. Clone hoặc tải về dự án

```bash
git clone <repo-url>
cd word-chain-game
```

### 2. Kiểm tra Python version

```bash
python --version
```

### 3. Không cần cài đặt dependencies bổ sung

Dự án sử dụng các module chuẩn của Python.

---

## 📁 Cấu Trúc Dự Án

```
word-chain-game/
├── main.py                    # Điểm vào chính
├── UI.py                      # Giao diện người dùng (Tkinter)
├── word_chain_server.py       # Server TCP xử lý game
├── word_chain_client.py       # Client kết nối server
├── word_validation.py         # Logic xác thực từ và chuỗi
├── dictionary_system.py       # Hệ thống quản lý từ điển
├── vietnamese_dictionary.txt  # File từ điển tiếng Việt
└── README.md
```

### Mô tả các thành phần

| File | Chức năng |
|------|-----------|
| `word_chain_server.py` | TCP Socket Server, xử lý nhiều client bằng threading |
| `word_chain_client.py` | Client kết nối server, nhận/gửi dữ liệu game |
| `word_validation.py` | Chuẩn hóa Unicode, kiểm tra luật nối từ |
| `dictionary_system.py` | Load từ điển, tra cứu O(1) bằng `set` |
| `UI.py` | Giao diện desktop Tkinter, hiển thị trạng thái game |

---

## 🚀 Hướng Dẫn Sử Dụng

### Bước 1 — Khởi động Server

```bash
python word_chain_server.py
```

Server khởi chạy trên `localhost:5000` và tải từ điển tiếng Việt.

### Bước 2 — Khởi động Client

Mở **terminal mới** và chạy:

```bash
python main.py
```

Hoặc chạy trực tiếp client (không GUI):

```bash
python word_chain_client.py
```

### Bước 3 — Chơi game

1. Nhập **tên người chơi** (tối đa 30 ký tự)
2. Chờ ghép đôi với người chơi khác
3. Nhập **cụm từ tiếng Việt** theo luật nối từ
4. Nhấn **Enter** hoặc nút **Gửi** để xác nhận
5. Nhấn **Bỏ qua** nếu muốn bỏ lượt

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────┐    TCP Socket    ┌──────────────────┐
│   Client 1  │◄────────────────►│                  │
│   (Tkinter) │                  │  Server           │
└─────────────┘                  │  (Threading)      │
                                 │                  │
┌─────────────┐                  │  ┌────────────┐  │
│   Client 2  │◄────────────────►│  │ Dictionary │  │
│   (Tkinter) │                  │  │ Validation │  │
└─────────────┘                  │  └────────────┘  │
                                 └──────────────────┘
```

**Server** (`word_chain_server.py`)
- TCP Socket Server chấp nhận nhiều client đồng thời
- Mô hình **Thread-per-Client**
- Thread-safe bằng `threading.Lock()`
- Ghép đôi người chơi tự động
- Kiểm tra luật nối từ và từ điển
- Timeout 15 giây mỗi lượt

**Client** (`word_chain_client.py` + `UI.py`)
- Giao diện desktop xây dựng bằng **Tkinter**
- Network I/O chạy trong thread riêng (không làm treo GUI)
- Sử dụng `Queue` để trao đổi dữ liệu an toàn giữa các thread
- Cập nhật trạng thái game theo thời gian thực

**Validation** (`word_validation.py`)
- Xử lý Unicode tiếng Việt bằng **NFC normalization**
- Kiểm tra quy tắc nối từ (so sánh **từ**, không phải ký tự)
- Tra cứu từ điển O(1) bằng cấu trúc `set`

---

## 🧪 Kiểm Thử

```bash
# Test xác thực từ và chuỗi
python word_validation.py
```

**Kết quả mẫu:**

```
=== Word Chain Game - Comprehensive Test ===

=== TEST 1: Single Player Word Chain ===
Player joined
Word 1: 'con vịt'   accepted  (next: vịt)
Word 2: 'vịt trời'  accepted  (next: trời)
Word 3: 'trời đêm'  accepted  (next: đêm)
Word 4: 'đêm tối'   accepted  (next: tối)
Word 5: 'tối đen'   accepted  (next: đen)

=== TEST 2: Invalid Word Chain Detection ===
First word 'ba' sent
Invalid chain rejected: Word must start with 'con'

=== TEST 3: Player Name Validation ===
Empty name rejected
Valid name accepted

All tests completed
```

---

## ⚠️ Xử Lý Lỗi

| Tình huống | Xử lý |
|------------|-------|
| Hết giờ (15s) | Người chơi thua ván |
| Từ không có trong từ điển | Báo lỗi, giữ lượt |
| Từ đã dùng rồi | Báo lỗi, giữ lượt |
| Sai luật nối từ | Báo lỗi kèm gợi ý từ cần bắt đầu |
| Đối thủ mất kết nối | Thông báo và kết thúc ván |
| Tên trùng | Yêu cầu chọn tên khác |

---

## ⚙️ Cấu Hình

Các tham số có thể chỉnh trong `word_chain_server.py`:

```python
HOST = 'localhost'   # Địa chỉ server
PORT = 5000          # Cổng kết nối
TURN_TIMEOUT = 15    # Thời gian mỗi lượt (giây)
```

---

## 📚 Kiến Thức Áp Dụng

- TCP socket programming và xử lý đa client
- Threading và đảm bảo thread-safety với `Lock`
- Lập trình GUI hướng sự kiện với Tkinter
- Xử lý Unicode tiếng Việt (NFC normalization)
- Thiết kế kiến trúc client-server
- Kiểm thử hệ thống với nhiều kịch bản

---

## 🔮 Có Thể Mở Rộng

- [ ] Hệ thống tính điểm và bảng xếp hạng
- [ ] Lưu lịch sử ván chơi
- [ ] Chat giữa người chơi
- [ ] Nhiều chế độ chơi (solo, team)
- [ ] Giao diện web thay thế Tkinter
