"""
Word Chain Game - Terminal Client
Phiên bản hoàn chỉnh: màu sắc, timer, validate cục bộ, UX mượt.
"""
 
import socket
import json
import time
import threading
import sys
import os
import unicodedata
from queue import Queue, Empty
 
 
# ══════════════════════════════════════════
#  ANSI COLORS
# ══════════════════════════════════════════
 
class C:
    RESET  = '\033[0m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    RED    = '\033[91m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    MAGENTA= '\033[95m'
    CYAN   = '\033[96m'
    WHITE  = '\033[97m'
 
USE_COLOR = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
 
def col(color, text):
    return f"{color}{text}{C.RESET}" if USE_COLOR else text
 
 
# ══════════════════════════════════════════
#  VIETNAMESE UTILS
# ══════════════════════════════════════════
 
def normalize_vn(text):
    """Chuẩn hóa NFC + lowercase — khớp logic server."""
    return unicodedata.normalize('NFC', text.strip().lower())
 
def get_first_word(phrase):
    parts = normalize_vn(phrase).split()
    return parts[0] if parts else ''
 
def get_last_word(phrase):
    parts = normalize_vn(phrase).split()
    return parts[-1] if parts else ''
 
 
# ══════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════
 
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
 
def banner():
    print(col(C.CYAN, "═" * 58))
    print(col(C.BOLD + C.WHITE, "        🔗  WORD CHAIN GAME — NỐI TỪ TIẾNG VIỆT"))
    print(col(C.CYAN, "═" * 58))
 
def divider(char="─", n=58):
    print(col(C.DIM, char * n))
 
def print_info(msg):
    print(f"  {col(C.CYAN, 'ℹ')}  {msg}")
 
def print_success(msg):
    print(col(C.GREEN, f"  ✅ {msg}"))
 
def print_error(msg):
    print(col(C.RED, f"  ❌ {msg}"))
 
def print_warn(msg):
    print(col(C.YELLOW, f"  ⚠️  {msg}"))
 
def prompt_input(msg):
    try:
        return input(col(C.BOLD, f"\n  ➤  {msg}: ")).strip()
    except (EOFError, KeyboardInterrupt):
        return 'quit'
 
 
# ══════════════════════════════════════════
#  SCREEN SECTIONS
# ══════════════════════════════════════════
 
def ask_name():
    clear()
    banner()
    print()
    while True:
        name = prompt_input("Nhập tên của bạn (tối đa 30 ký tự)")
        if not name:
            print_error("Tên không được để trống!")
        elif len(name) > 30:
            print_error("Tên quá dài, tối đa 30 ký tự!")
        else:
            return name
 
def ask_rematch():
    print()
    divider()
    while True:
        choice = prompt_input("Chơi lại? [y / n]").lower()
        if choice in ('y', 'yes', 'có', 'co'):
            return True
        if choice in ('n', 'no', 'không', 'khong', 'q', ''):
            return False
        print_error("Nhập 'y' để chơi lại hoặc 'n' để thoát.")
 
def show_game_start(opponent, starting_word, next_word, your_turn):
    print()
    divider("═")
    print(col(C.BOLD, "  🎮  VÁN MỚI BẮT ĐẦU!"))
    print(f"  👤  Đối thủ   : {col(C.MAGENTA, opponent)}")
    print(f"  📌  Từ đầu    : {col(C.BOLD + C.YELLOW, starting_word)}")
    print(f"  ➡️   Tiếp theo : [{col(C.CYAN, next_word)}]")
    divider("═")
    if your_turn:
        print_success("Bạn đi trước!")
    else:
        print_info(f"{col(C.MAGENTA, opponent)} đi trước, hãy chờ...")
    print()
 
def show_word_accepted(player, word, next_word, your_turn, turn_count, history):
    divider()
    print(f"  🟢  {col(C.BOLD, player)}: {col(C.GREEN + C.BOLD, f'«{word}»')}  "
          f"{col(C.DIM, f'(lượt #{turn_count})')}")
    print(f"  ➡️   Tiếp theo phải bắt đầu bằng: {col(C.CYAN + C.BOLD, f'[{next_word}]')}")
 
    # Hiển thị chuỗi từ gần nhất
    if len(history) > 1:
        shown = history[-5:]
        chain = col(C.DIM, " → ").join(
            col(C.YELLOW, w) if i == len(shown) - 1 else col(C.DIM, w)
            for i, w in enumerate(shown)
        )
        print(f"  📜  Chuỗi   : {chain}")
    divider()
 
    if your_turn:
        print_success("Đến lượt bạn!")
    else:
        print_info("Đang chờ đối thủ...")
    print()
 
def show_game_over(you_win, winner, loser, reason, score, history):
    print()
    divider("═")
    if you_win is True:
        print(col(C.GREEN + C.BOLD, "  🏆  BẠN THẮNG! Chúc mừng!"))
    elif you_win is False:
        print(col(C.RED + C.BOLD,   "  💀  BẠN THUA! Cố lên lần sau!"))
    else:
        print(col(C.YELLOW, "  🤝  VÁN ĐẤU KẾT THÚC"))
 
    if winner and loser:
        print(f"  📋  Kết quả : {col(C.GREEN, winner)} thắng | {col(C.RED, loser)} thua")
    if reason:
        print(f"  📝  Lý do   : {reason}")
    if score:
        scores = "  |  ".join(f"{k}: {col(C.YELLOW, str(v))}" for k, v in score.items())
        print(f"  🏅  Điểm    : {scores}")
    if history:
        total = len(history)
        shown = history[-8:]
        chain = " → ".join(shown)
        print(f"  📜  Chuỗi ({total} từ): {col(C.DIM, chain)}")
    divider("═")
 
 
# ══════════════════════════════════════════
#  COUNTDOWN TIMER (chạy trong thread)
# ══════════════════════════════════════════
 
class TurnTimer:
    """Hiển thị countdown timer trên cùng 1 dòng."""
 
    def __init__(self, seconds=10):
        self.seconds = seconds
        self._stop = threading.Event()
        self._thread = None
 
    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
 
    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        # Xóa dòng timer
        print(f"\r{' ' * 40}\r", end='', flush=True)
 
    def _run(self):
        t = self.seconds
        while t >= 0 and not self._stop.is_set():
            bar_len = 20
            filled = int(bar_len * t / self.seconds)
            bar = '█' * filled + '░' * (bar_len - filled)
            color = C.GREEN if t > 5 else C.YELLOW if t > 2 else C.RED
            display = f"\r  ⏱  [{col(color, bar)}] {col(C.BOLD, str(t))}s   "
            print(display, end='', flush=True)
            time.sleep(1)
            t -= 1
        if not self._stop.is_set():
            print(f"\r  ⏱  {col(C.RED, '[HẾT GIỜ!]')}                    ", flush=True)
 
 
# ══════════════════════════════════════════
#  CLIENT CLASS
# ══════════════════════════════════════════
 
class WordChainClient:
 
    TURN_TIMEOUT = 30   # giây — khớp server
 
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.player_name = None
 
        self.socket        = None
        self.connected     = False
        self.stop_event    = threading.Event()
        self.message_queue = Queue()
 
        self._reset_state()
 
    # ── reset ──────────────────────────────
 
    def _reset_state(self):
        self.opponent_name  = None
        self.current_word   = None
        self.next_word      = None   # từ bắt buộc bắt đầu tiếp theo
        self.your_turn      = False
        self.word_history   = []
        self.used_words     = set()
        self.game_active    = False
        self.game_over_info = None
        self.turn_count     = 0
        self._in_turn       = False
 
    # ── network ────────────────────────────
 
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(None)
            self._send_raw({'type': 'name', 'value': self.player_name})
            self.connected = True
            self.stop_event.clear()
            threading.Thread(target=self._receiver, daemon=True).start()
            return True
        except ConnectionRefusedError:
            print_error(f"Không kết nối được tới {self.host}:{self.port}. Server đã chạy chưa?")
            return False
        except Exception as e:
            print_error(f"Lỗi kết nối: {e}")
            return False
 
    def disconnect(self):
        self.stop_event.set()
        self.connected = False
        if self.socket:
            try: self.socket.close()
            except Exception: pass
            self.socket = None
 
    def reconnect(self):
        self.disconnect()
        time.sleep(0.5)
        self._reset_state()
        while not self.message_queue.empty():
            try: self.message_queue.get_nowait()
            except Empty: break
        return self.connect()
 
    def _send_raw(self, data):
        msg = json.dumps(data, ensure_ascii=False) + '\n'
        self.socket.sendall(msg.encode('utf-8'))
 
    def send_word(self, word):
        if not self.connected:
            print_error("Mất kết nối tới server!")
            return False
        try:
            self._send_raw({'type': 'word', 'value': word})
            return True
        except Exception as e:
            print_error(f"Gửi từ thất bại: {e}")
            return False
 
    def send_giveup(self):
        if self.connected:
            try: self._send_raw({'type': 'giveup'})
            except Exception: pass
 
    # ── receiver thread ────────────────────
 
    def _receiver(self):
        buffer = ""
        try:
            while self.connected and not self.stop_event.is_set():
                data = self.socket.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            self.message_queue.put(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception:
            pass
        finally:
            self.connected = False
            self.message_queue.put({'type': '_disconnected'})
 
    # ── message handler ────────────────────
 
    def _handle(self, msg):
        t = msg.get('type')
 
        if t == 'game_start':
            self.opponent_name = msg.get('opponent_name', '???')
            self.current_word  = msg.get('current_word', '')
            self.next_word     = msg.get('next_letter', '')
            self.your_turn     = msg.get('your_turn', False)
            self.game_active   = True
            self.word_history  = [self.current_word]
            self.used_words    = {normalize_vn(self.current_word)}
            self.turn_count    = 0
            show_game_start(self.opponent_name, self.current_word,
                            self.next_word, self.your_turn)
 
        elif t == 'word_accepted':
            self.turn_count  += 1
            self.current_word = msg.get('word', '')
            self.next_word    = msg.get('next_letter', '')
            self.your_turn    = msg.get('your_turn', False)
            self.word_history.append(self.current_word)
            self.used_words.add(normalize_vn(self.current_word))
            show_word_accepted(
                msg.get('player', '?'), self.current_word,
                self.next_word, self.your_turn,
                self.turn_count, self.word_history
            )
 
        elif t == 'error':
            err_msg = msg.get('message', 'Lỗi không xác định')
            print_error(err_msg)
            # Nếu server cho giữ lượt và không đang trong _take_turn loop
            if not self._in_turn:
                self.your_turn = msg.get('your_turn', self.your_turn)
 
        elif t == 'game_over':
            self.game_active    = False
            self.game_over_info = msg
            show_game_over(
                you_win = msg.get('you_win'),
                winner  = msg.get('winner'),
                loser   = msg.get('loser'),
                reason  = msg.get('reason', ''),
                score   = msg.get('score'),
                history = msg.get('word_history', self.word_history)
            )
 
        elif t in ('opponent_eliminated', 'opponent_disconnected'):
            self.game_active = False
            print_warn(f"Ván kết thúc: {msg.get('message', 'Đối thủ đã rời trận')}")
 
        elif t == '_disconnected':
            self.game_active = False
            self.connected   = False
 
    # ── wait for server response ────────────
 
    def _wait_server_response(self):
        """
        Chờ server phản hồi sau khi gửi từ.
        Trả về: 'accepted' | 'error' | 'game_over'
        """
        while self.game_active and self.connected:
            try:
                msg = self.message_queue.get(timeout=0.1)
                t   = msg.get('type')
                self._handle(msg)
                if t == 'word_accepted':
                    return 'accepted'
                if t == 'error':
                    return 'error'
                if t in ('game_over', 'opponent_disconnected',
                         'opponent_eliminated', '_disconnected'):
                    return 'game_over'
            except Empty:
                pass
        return 'game_over'
 
    # ── game phases ────────────────────────
 
    def wait_for_match(self):
        print()
        print_info("Đang chờ ghép đôi với người chơi khác...")
        dots = 0
        while not self.game_active and self.connected:
            try:
                msg = self.message_queue.get(timeout=0.4)
                print()
                self._handle(msg)
            except Empty:
                dots = (dots + 1) % 4
                print(f"\r  ⏳ Chờ{'.' * dots}   ", end='', flush=True)
        print()
        return self.game_active
 
    def play_one_match(self):
        while self.game_active and self.connected:
            # drain queue
            while True:
                try:
                    msg = self.message_queue.get_nowait()
                    self._handle(msg)
                except Empty:
                    break
 
            if not self.game_active:
                break
 
            if self.your_turn and not self._in_turn:
                self._in_turn  = True
                self.your_turn = False
                self._take_turn()
                self._in_turn  = False
 
            time.sleep(0.05)
 
        # drain message đến muộn
        time.sleep(0.3)
        while True:
            try:
                msg = self.message_queue.get_nowait()
                self._handle(msg)
            except Empty:
                break
 
        return self.connected
 
    # ── turn handler ───────────────────────
 
    def _take_turn(self):
        """
        Xử lý 1 lượt của người chơi.
        Loop nội bộ cho đến khi từ được chấp nhận, bỏ qua, hoặc game kết thúc.
        """
        turn_start = time.time()   # ghi thời điểm bắt đầu lượt, KHÔNG reset khi loop
 
        while self.game_active:
            # Hiển thị trạng thái lượt
            print()
            print(f"  🎯  Từ hiện tại   : {col(C.BOLD + C.YELLOW, f'«{self.current_word}»')}")
            print(f"  📌  Bắt đầu bằng  : {col(C.CYAN + C.BOLD, f'[{self.next_word}]')}")
            print(f"  📜  Đã chơi       : {col(C.DIM, str(self.turn_count))} từ")
            print(col(C.DIM, "      (boqua = bỏ qua lượt | quit = thoát)"))
            print()
 
            # Tính thời gian còn lại thực tế (đồng bộ với server)
            elapsed   = time.time() - turn_start
            remaining = max(1, int(self.TURN_TIMEOUT - elapsed))
            # Tạo timer mới với số giây còn lại
            timer = TurnTimer(remaining)
            timer.start()
 
            # Nhận input trong thread riêng
            result   = [None]
            done_evt = threading.Event()
 
            def read_input():
                try:
                    result[0] = input(col(C.BOLD, "  ➤  Nhập từ của bạn: ")).strip()
                except (EOFError, KeyboardInterrupt):
                    result[0] = 'quit'
                finally:
                    done_evt.set()
 
            inp_thread = threading.Thread(target=read_input, daemon=True)
            inp_thread.start()
 
            # Chờ input, vẫn drain queue để nhận game_over kịp
            while not done_evt.is_set():
                while True:
                    try:
                        msg = self.message_queue.get_nowait()
                        self._handle(msg)
                    except Empty:
                        break
                if not self.game_active:
                    timer.stop()
                    return
                done_evt.wait(timeout=0.1)
 
            timer.stop()
 
            word = (result[0] or '').strip()
 
            # ── xử lý lệnh đặc biệt ──
            if not word:
                print_warn("Bạn chưa nhập từ!")
                continue
 
            cmd = normalize_vn(word)
            if cmd == 'quit':
                print_warn("Bạn đã bỏ cuộc!")
                self.send_giveup()
                self.game_active = False
                return
 
            if cmd in ('boqua', 'bỏ qua', 'skip', 'bo qua'):
                print_warn("Bạn bỏ qua lượt này!")
                self.send_giveup()
                return
 
            # ── validate cục bộ trước khi gửi ──
            normalized = normalize_vn(word)
 
            # Kiểm tra độ dài
            if len(normalized.split()) < 1 or len(normalized) < 2:
                print_error("Từ quá ngắn! Nhập lại.")
                continue
 
            # Kiểm tra prefix
            if get_first_word(normalized) != self.next_word:
                print_error(
                    f"Từ phải bắt đầu bằng '{col(C.CYAN, self.next_word)}'! "
                    f"(bạn nhập: '{get_first_word(normalized)}')"
                )
                continue
 
            # Kiểm tra đã dùng chưa
            if normalized in self.used_words:
                print_error(f"'{word}' đã được dùng rồi! Chọn từ khác.")
                continue
 
            # ── gửi lên server ──
            if not self.send_word(word):
                return
 
            # Chờ server xác nhận
            outcome = self._wait_server_response()
            if outcome == 'accepted':
                return   # lượt kết thúc thành công
            if outcome == 'game_over':
                return
            # outcome == 'error' → loop lại, cho nhập từ khác
 
 
# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════
 
def main():
    clear()
    banner()
 
    host = 'localhost'
    port = 5000
 
    player_name = ask_name()
 
    client = WordChainClient(host=host, port=port)
    client.player_name = player_name
 
    print()
    print_info(f"Xin chào, {col(C.BOLD, player_name)}! Đang kết nối tới {host}:{port}...")
 
    if not client.connect():
        sys.exit(1)
 
    print_success("Kết nối thành công!")
 
    # ── vòng lặp nhiều ván ──────────────────
    while True:
        client._reset_state()
 
        matched = client.wait_for_match()
        if not matched:
            print_error("Không ghép được đôi hoặc mất kết nối.")
            break
 
        still_connected = client.play_one_match()
 
        if not still_connected:
            print_warn("Mất kết nối tới server.")
            break
 
        want_rematch = ask_rematch()
        if not want_rematch:
            client.send_giveup()
            print()
            print_info(f"Cảm ơn {col(C.BOLD, player_name)} đã chơi! Hẹn gặp lại 👋")
            break
        client._send_raw({'type': 'rematch'})
        print_info("Đang kết nối lại để chơi ván mới...")
        if not client.reconnect():
            print_error("Không thể kết nối lại. Thoát.")
            break
        print_success("Kết nối lại thành công!")
 
    client.disconnect()
 
 
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warn("Người chơi thoát (Ctrl+C).")
        sys.exit(0)
