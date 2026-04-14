Word Chain Game - Game nối từ tiếng Việt

Một trò chơi nối từ đa người chơi sử dụng kiến trúc client-server TCP với giao diện desktop GUI.

Mục tiêu

Dự án nhằm áp dụng các khái niệm mạng máy tính cơ bản:

Giao tiếp socket TCP
Xử lý kết nối đa client
Truyền tải dữ liệu thời gian thực
Xác thực dữ liệu phía server
Luật chơi
Mỗi người chơi nhập một từ tiếng Việt.
Từ tiếp theo phải bắt đầu bằng chữ cuối của từ trước đó.
Từ nhập phải tồn tại trong từ điển tiếng Việt.
Server kiểm tra tính hợp lệ và gửi kết quả đến tất cả người chơi.

Ví dụ chuỗi hợp lệ:

a → an → ng → ga → an
Kiến trúc hệ thống
┌─────────────┐    TCP Socket    ┌─────────────┐
│   Client 1  │◄────────────────►│             │
│   (Tkinter) │                  │   Server    │
└─────────────┘                  │ (Threading) │
                                 └─────────────┘
┌─────────────┐                  ┌─────────────┐
│   Client 2  │◄────────────────►│ Dictionary  │
│   (Tkinter) │                  │ Validation  │
└─────────────┘                  └─────────────┘
Server (word_chain_server.py)
TCP Socket Server chấp nhận nhiều client đồng thời
Mô hình Thread-per-Client
Đảm bảo thread-safe bằng threading.Lock()
Kiểm tra quy tắc nối từ và từ điển
Broadcast thông tin tới tất cả client
Client (word_chain_client.py)
Giao diện desktop xây dựng bằng Tkinter
Network I/O chạy trong thread riêng để không làm treo GUI
Sử dụng Queue để trao đổi dữ liệu giữa network thread và GUI thread
Cập nhật trạng thái trò chơi theo thời gian thực
Validation (word_validation.py)
Xử lý Unicode tiếng Việt bằng NFC normalization
Kiểm tra quy tắc nối từ
Tra cứu từ điển với độ phức tạp O(1) bằng cấu trúc set
Cấu trúc thư mục
word-chain-game/
├── word_chain_server.py
├── word_chain_client.py
├── word_validation.py
├── dictionary_system.py
├── vietnamese_dictionary.txt
├── Ui.py
├── main.py
└── README.md
Cách chạy chương trình
Bước 1: Khởi động Server
python word_chain_server.py

Server chạy trên địa chỉ localhost:5000 và tải từ điển.

Bước 2: Khởi động Client

Mở terminal mới:

python word_chain_client.py
Bước 3: Chơi game
Nhập tên người chơi
Nhập từ tiếng Việt theo quy tắc nối từ
Quan sát tin nhắn được broadcast từ server
Kiểm thử
Test tổng hợp
python test_comprehensive.py
Test đa client
python test_multi_client.py
Test validation
python word_validation.py
Yêu cầu kỹ thuật
Python 3.6 trở lên
Chỉ sử dụng thư viện chuẩn: socket, threading, tkinter, json, unicodedata
TCP socket chạy trên localhost:5000
Encoding UTF-8 cho dữ liệu JSON
Tính năng
Đã hoàn thành
Server TCP socket đa client sử dụng threading
Client GUI Tkinter với threading và queue
Kiểm tra quy tắc nối từ
Kiểm tra từ điển tiếng Việt
Broadcast thời gian thực cho tất cả client
Quản lý người chơi (tham gia, rời, tên duy nhất)
Xử lý Unicode tiếng Việt (NFC normalization)
Xử lý lỗi và ngắt kết nối
Có thể mở rộng
Hệ thống tính điểm người chơi
Lưu lịch sử game
Chat giữa người chơi
Bộ đếm thời gian cho mỗi lượt
Các chế độ chơi khác nhau
Xử lý lỗi
Server
Timeout kết nối 60 giây
Đồng bộ dữ liệu bằng threading.Lock()
Hỗ trợ tắt server an toàn bằng Ctrl+C
Client
Network thread dạng daemon tự kết thúc
Giao tiếp giữa thread thông qua queue
Xử lý lỗi khi mất kết nối server
Validation
Chuẩn hóa Unicode tiếng Việt
So sánh không phân biệt chữ hoa chữ thường
Kiểm tra và làm sạch dữ liệu đầu vào
Kết quả kiểm thử
=== Word Chain Game - Comprehensive Test ===

=== TEST 1: Single Player Word Chain ===
Player joined
Word 1: 'a' accepted (next: a)
Word 2: 'an' accepted (next: n)
Word 3: 'ng' accepted (next: g)
Word 4: 'ga' accepted (next: a)
Word 5: 'an' accepted (next: n)

=== TEST 2: Invalid Word Chain Detection ===
First word 'ba' sent
Invalid chain rejected: Word must start with 'n'

=== TEST 3: Player Name Validation ===
Empty name rejected
Valid name accepted

All tests completed
Kiến thức đạt được
TCP socket programming và xử lý đa client
Threading và đảm bảo thread-safety
Lập trình GUI hướng sự kiện với Tkinter
Xử lý Unicode tiếng Việt
Thiết kế kiến trúc client-server
Kiểm thử hệ thống với nhiều kịch bản
