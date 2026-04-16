import socket
import threading
import time
import json

# Cấu hình server
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

# Cấu hình bài test
NUM_CLIENTS = 1500  # Số lượng người chơi giả lập (bạn có thể tăng lên 1000, 2000 để xem giới hạn)
RAMP_UP_DELAY = 0.01 # Độ trễ giữa mỗi lần tạo client (giây)

# Biến thống kê
success_connections = 0
failed_connections = 0
lock = threading.Lock()

def simulate_player(player_id):
    global success_connections, failed_connections
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0) # Nếu server không phản hồi sau 5s thì coi như lỗi
        s.connect((SERVER_HOST, SERVER_PORT))
        
        # Gửi dữ liệu theo đúng định dạng mà word_chain_server.py yêu cầu
        name_payload = json.dumps({'type': 'name', 'name': f'BotStress_{player_id}'}) + '\n'
        s.sendall(name_payload.encode('utf-8'))
        
        # Đợi server phản hồi lại thông điệp ghép phòng hoặc chờ
        response = s.recv(1024)
        
        if response:
            with lock:
                success_connections += 1
        else:
            with lock:
                failed_connections += 1
        
        # Giữ kết nối một lúc để giả lập đang chơi, tạo tải cho bộ nhớ server
        time.sleep(10)
        s.close()
        
    except Exception as e:
        with lock:
            failed_connections += 1

def run_stress_test():
    print(f"🚀 Bắt đầu Stress Test với {NUM_CLIENTS} kết nối đồng thời...")
    start_time = time.time()
    threads = []
    
    for i in range(NUM_CLIENTS):
        t = threading.Thread(target=simulate_player, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(RAMP_UP_DELAY) # Tăng tải từ từ
        
    for t in threads:
        t.join()
        
    end_time = time.time()
    
    print("\n" + "="*40)
    print("📊 BÁO CÁO KẾT QUẢ STRESS TEST")
    print("="*40)
    print(f"- Tổng thời gian bắn request: {end_time - start_time:.2f} giây")
    print(f"- Tổng số client mô phỏng: {NUM_CLIENTS}")
    print(f"- ✅ Kết nối thành công: {success_connections}")
    print(f"- ❌ Kết nối thất bại / Timeout: {failed_connections}")
    print("="*40)

if __name__ == "__main__":
    run_stress_test()