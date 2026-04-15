"""
Word Chain Game - Server 
Simple TCP server with immediate match-found system (no rooms).
2 players accepted -> game starts automatically.
"""

import socket
import threading
import json
import time
import random
from word_validation import (
    normalize_vietnamese,
    is_valid_chain_move,
    is_valid_word,
    get_next_letter_constraint,
    load_dictionary,
    validate_player_name
)


class Match:
    """Represents an active game match between 2 players."""
    
    def __init__(self, player1_socket, player1_name, player2_socket, player2_name, dictionary):
        self.player1_socket = player1_socket
        self.player1_name = player1_name
        self.player2_socket = player2_socket
        self.player2_name = player2_name
        
        self.dictionary = dictionary
        
        # Threading primitives
        self.game_lock  = threading.Lock()
        self.turn_event = threading.Event()

        # Trạng thái ván
        self.game_active           = True
        self.current_word          = random.choice(list(dictionary))
        self.current_player_socket = None
        self.current_player_name   = None
        self.word_history          = [(self.current_word, "System")]
        self.used_words            = {self.current_word}
        
        # Timing
        self.turn_start_time = time.time()
        self.turn_timeout = 30   # seconds per turn

        # turn count để tính điểm
        self.score = {
            self.player1_name: 0,
            self.player2_name: 0
        }
        
        # Randomly pick who starts
        if random.random() < 0.5:
            self.current_player_socket = player1_socket
            self.current_player_name = player1_name
        else:
            self.current_player_socket = player2_socket
            self.current_player_name = player2_name
        
        print(f"[MATCH] Started: {player1_name} vs {player2_name} | Starting word: {self.current_word} | {self.current_player_name}'s turn")
    
    
    def get_next_player_socket(self):
    
        if self.current_player_socket == self.player1_socket: 
            return self.player2_socket 
        else: 
            return self.player1_socket 
    
    def get_next_player_name(self):
        """Get the name of the player who's not current."""
        if self.current_player_socket == self.player1_socket:
            return self.player2_name
        else:
            return self.player1_name
    
    #trả về socket của đối thủ  
    def get_opponent_socket(self, my_socket):
        if my_socket == self.player1_socket:
            return self.player2_socket
        else:
            return self.player1_socket
 
    #trả về tên của đối thủ
    def get_opponent_name(self, my_socket):
        if my_socket == self.player1_socket:
            return self.player2_name
        else:
            return self.player1_name
    
    def start_timeout_watcher(self, server):
        def watcher():
            while self.game_active:
                # đợi cho tới khi có turn mới hoặc timeout
                is_set = self.turn_event.wait(timeout=self.turn_timeout)
                self.turn_event.clear()

                if not is_set:  # hết giờ
                    with self.game_lock:
                        if not self.game_active:
                            return

                        loser_socket = self.current_player_socket
                        loser_name = self.current_player_name

                    # gọi server để end game
                    server._end_match(self, loser_socket, loser_name, 'timeout')
                    return

        threading.Thread(target=watcher, daemon=True).start()
    
    def switch_turn(self):

        self.current_player_socket = self.get_next_player_socket()
        self.current_player_name   = self.get_next_player_name()
        self.turn_start_time = time.time()
        self.turn_event.set()
        
class WordChainServer:

    def __init__(self, host='localhost', port=5000, dictionary_file='vietnamese_dictionary.txt'): 
        self.host           = host
        self.port           = port
        self.server_socket  = None
        self.running        = False

        # xếp cho hàng đợi
        self.waiting_queue = []   # List of (socket, name)
        self.queue_lock =threading.Lock()

        # Active matches 
        self.matches = {}    # {player_socket: Match}
        self.matches_lock =threading.Lock()
        
        self.active_names = set()
        self.names_lock   = threading.Lock()
        
        
        
        # Load dictionary
        try:
            self.dictionary = load_dictionary(dictionary_file)
            print(f"[SERVER] Loaded {len(self.dictionary)} words from dictionary")
        except Exception as e:
            print(f"[SERVER] Error loading dictionary: {e}")
            self.dictionary = set()


    
    def start(self):
        """Start the server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            print(f"[SERVER] Started on {self.host}:{self.port}")
            print("[SERVER] Waiting for player connections...")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    print(f"[SERVER] New connection from {client_addr}")
                    
                    # Spawn thread to handle this player
                    client_thread = threading.Thread(
                        target=self.handle_player,
                        args=(client_socket, client_addr),
                        daemon=True
                    )
                    client_thread.start()
                except OSError:
                    break   # server_socket đã đóng → thoát vòng lặp
                except Exception as e:
                    if self.running:
                        print(f"[SERVER] Error accepting connection: {e}")
                    
        except Exception as e:
            print(f"[SERVER] Error starting server: {e}")
            
        finally:
            self.stop()
    
    def handle_player(self, client_socket, client_addr):
        """Handle a single player connection."""
        player_name = None
        match = None
        try:
            # Set socket timeout
            client_socket.settimeout(None)
            
            # Step 1: Receive player name
            name_msg = client_socket.recv(1024).decode('utf-8')
            if not name_msg:
                return
            
            try:
                data = json.loads(name_msg)
                if data.get('type') == 'name':
                    player_name = data.get('value', '').strip()
            except json.JSONDecodeError:
                self.send_message(client_socket, {'type': 'error', 'message': 'Invalid message format'})
                return
            
            # Validate name
            is_valid, error_msg = validate_player_name(player_name)
            if not is_valid:
                self.send_message(client_socket, {'type': 'error', 'message': f'Invalid player name: {error_msg}'})
                return
            
            with self.names_lock:
                if player_name in self.active_names:
                    print(f"[NAME] '{player_name}' is already active → forcing cleanup for rematch")

                    # Kiểm tra xem tên này có thật sự đang trong trận không
                    still_in_match = False
                    with self.matches_lock:
                        for m in list(self.matches.values()):
                            if m.player1_name == player_name or m.player2_name == player_name:
                                still_in_match = True
                                break
                    
                    if not still_in_match:
                        self.active_names.discard(player_name)   # Xóa tên cũ để cho reconnect

                self.active_names.add(player_name)
            
            # Add to waiting queue
            with self.queue_lock:
                self.waiting_queue.append((client_socket, player_name))
                
                # Check if we can start a match
                # note dùng while để xử lý trg hợp có nhiều hơn 2 người đang chờ, tránh chỉ start 1 ván rồi thôi
            self._try_match_players()   
            
            # If not in a match yet, wait for match
            while self.running:
                with self.matches_lock:
                    if client_socket in self.matches:
                        match = self.matches[client_socket]
                        break
                time.sleep(0.1)
            
            # Main game loop - handle word submissions
            buffer = ""
            while self.running:
                try:
                    
                    with self.matches_lock:
                        match = self.matches.get(client_socket)

                    if not match:
                        time.sleep(0.1)
                        continue

                    #  chỉ recv khi đã có match
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        print(f"[DISCONNECT] {player_name}")
                        break

                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if not line.strip():
                            continue
                        try:
                            msg_data = json.loads(line)
                            with self.matches_lock:
                                match = self.matches.get(client_socket)
                            if not match:
                                continue
                            self._dispatch(client_socket, player_name, msg_data, match)

                        except json.JSONDecodeError:
                            self.send_message(client_socket, {
                                'type': 'error',
                                'message': 'message unvalid'
                            })

                except (ConnectionResetError, BrokenPipeError, OSError):
                    break
                except Exception as e:
                    print(f"[SERVER] Error in game loop: {e}")
                    break
        finally:
            self._cleanup(client_socket, player_name, match)
    def process_word_submission(self, player_socket, player_name, word):
        """Process a word submission from a player."""
        with self.matches_lock:
            if player_socket not in self.matches:
                return
            
            match = self.matches[player_socket]
                       
        word = normalize_vietnamese(word).lower()
        with match.game_lock:
            # Check if it's this player's turn
            if match.current_player_socket != player_socket:
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': "Not your turn!",
                    'your_turn': False
                })
                return
            
            # Check word length
            if len(word.split()) < 2:
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': 'Word must be at least 2 characters',
                    'your_turn': True
                })
                return
            
            # Check if word starts with correct letter
            required_letter = get_next_letter_constraint(match.current_word)
            if not is_valid_chain_move(match.current_word, word):
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': f"Word must start with '{required_letter}'",
                    'your_turn': True
                })
                return
            
            # Check if word is in dictionary
            if not is_valid_word(word, match.dictionary):
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': f"'{word}' is not in dictionary",
                    'your_turn': True
                })
                return
            
            # Check if word already used
            if word in match.used_words:
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': f"'{word}' already used",
                    'your_turn': True
                })
                return
            
            # Get opponent socket
            opponent_socket = match.get_next_player_socket()
            
            # Word is valid - accept it
            match.current_word = word         
            match.used_words.add(word)
            match.word_history.append((word, player_name))
            match.score[player_name] += 1      # cộng điểm cho người vừa chơi thành công
            next_letter = get_next_letter_constraint(word)
            match.switch_turn()

            
            # Message to current player
            msg_current = {
                'type': 'word_accepted',
                'word': word,
                'player': player_name,
                'next_letter': next_letter,
                'your_turn': False,
                'score':       self.matches[player_socket].score,
                
            }
            self.send_message(player_socket, msg_current)
            
            # Message to opponent
            msg_opponent = {
                'type': 'word_accepted',
                'word': word,
                'player': player_name,
                'next_letter': next_letter,
                'your_turn': True,
                'score': match.score
            }
            self.send_message(opponent_socket, msg_opponent)
            
            print(f"[GAME] {player_name}: {word} -> next: {next_letter}")
    
    def send_message(self, client_socket, data):
        """Gửi JSON + newline. Không ném exception ra ngoài."""
        try:
            msg = json.dumps(data, ensure_ascii=False) + '\n'
            client_socket.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[SEND ERROR] {e}")

    # ─── Router lệnh ──────────────────────────────────────────────
    def _dispatch(self, sock, player_name, msg, match):
        """Phân phối message tới handler tương ứng."""
        msg_type = msg.get('type')

        if msg_type == 'word':
            rword = msg.get('value', '').strip()
            word = normalize_vietnamese(rword).lower()
            self.process_word_submission(sock, player_name, word)

        elif msg_type == 'giveup':
            self._end_match(match, loser_socket=sock,
                            loser_name=player_name, reason='giveup')

        elif msg_type == 'ping':
            self.send_message(sock, {'type': 'pong'})
           
        # ghép trận 
        elif msg_type == 'rematch':
            self._handle_rematch_request(sock, player_name)
        
        
    def _handle_rematch_request(self, sock, player_name):
        print(f"[REMATCH] {player_name} wants to play again")

        with self.queue_lock:
            self.waiting_queue.append((sock, player_name))

        # thử ghép trận
        self._try_match_players()

    def _try_match_players(self):
        #Thử ghép đôi người chơi đang chờ. Chạy lại nhiều lần nếu cần.
        with self.queue_lock:
            while len(self.waiting_queue) >= 2:
                p1_sock, p1_name = self.waiting_queue.pop(0)
                p2_sock, p2_name = self.waiting_queue.pop(0)

                print(f"[MATCHMAKING] Ghép đôi: {p1_name} vs {p2_name}")

                try:
                    new_match = Match(p1_sock, p1_name, p2_sock, p2_name, self.dictionary)
                    new_match.start_timeout_watcher(self)

                    with self.matches_lock:
                        self.matches[p1_sock] = new_match
                        self.matches[p2_sock] = new_match

                    # Gửi thông báo game_start cho cả hai
                    for sock, name, opponent in [
                        (p1_sock, p1_name, p2_name),
                        (p2_sock, p2_name, p1_name)
                    ]:
                        self.send_message(sock, {
                            'type': 'game_start',
                            'opponent_name': opponent,
                            'current_word': new_match.current_word,
                            'next_letter': get_next_letter_constraint(new_match.current_word),
                            'your_turn': new_match.current_player_name == name,
                            'score': {p1_name: 0, p2_name: 0}
                        })

                    print(f"[MATCH] Game started successfully: {p1_name} vs {p2_name}")

                except Exception as e:
                    print(f"[MATCH ERROR] Không thể tạo match {p1_name} vs {p2_name}: {e}")
                    # Đẩy lại vào queue nếu lỗi
                    with self.queue_lock:
                        self.waiting_queue.insert(0, (p2_sock, p2_name))
                        self.waiting_queue.insert(0, (p1_sock, p1_name))
                    # Đóng socket nếu không cứu được
                    try:
                        self.send_message(p1_sock, {'type': 'error', 'message': 'Lỗi tạo trận, thử lại sau'})
                        self.send_message(p2_sock, {'type': 'error', 'message': 'Lỗi tạo trận, thử lại sau'})
                    except:
                        pass

    def _end_match(self, match, loser_socket, loser_name, reason):
        """
        Kết thúc ván, gửi game_over cho cả 2.
        An toàn khi gọi từ nhiều nơi: kiểm tra game_active trong lock.
        """
        with match.game_lock:
            if not match.game_active:
                return   # đã kết thúc rồi
            match.game_active = False
            match.turn_event.set()   # unblock timeout watcher

        winner_sock = match.get_opponent_socket(loser_socket)
        winner_name = match.get_opponent_name(loser_socket)

        reason_text = {
            'timeout':    f"{loser_name} ran out of time ({match.turn_timeout}s)",
            'giveup':     f"{loser_name} gave up",
            'disconnect': f"{loser_name} disconnected",
        }.get(reason, reason)

        payload = {
            'type':         'game_over',
            'reason':       reason_text,
            'winner':       winner_name,
            'loser':        loser_name,
            'score':        match.score,
            'word_history': [w for w, _ in match.word_history],
        }
        self.send_message(loser_socket, {**payload, 'you_win': False})
        self.send_message(winner_sock,  {**payload, 'you_win': True})

        print(f"[OVER] {winner_name} wins | {reason_text} | Score: {match.score}")
        
        
        with self.matches_lock:
            self.matches.pop(loser_socket, None)
            self.matches.pop(winner_sock, None)
        
        if self.running:
            time.sleep(0.15)
            self._try_match_players()

        

    #  clean khi player disconnect hoặc ván kết thúc, luôn chạy trong finally của handle_player
    def _cleanup(self, sock, player_name, match):
        """Dọn dẹp khi player disconnect hoặc handle_player kết thúc"""
        # 1. Kết thúc trận nếu đang chơi
        if match and match.game_active:
            self._end_match(match, loser_socket=sock, loser_name=player_name or 'Unknown', reason='disconnect')

        # 2. Xóa khỏi waiting queue
        with self.queue_lock:
            self.waiting_queue = [(s, n) for s, n in self.waiting_queue if s != sock]

        # 3. Xóa khỏi matches
        with self.matches_lock:
            self.matches.pop(sock, None)

        # 4. Giải phóng tên (quan trọng nhất)
        if player_name:
            with self.names_lock:
                self.active_names.discard(player_name)

        # 5. Đóng socket an toàn
        def delayed_close(s):
            try:
                s.shutdown(socket.SHUT_WR)
            except:
                pass
            time.sleep(0.3)
            try:
                s.close()
            except:
                pass

        threading.Thread(target=delayed_close, args=(sock,), daemon=True).start()

        if player_name:
            print(f"[SERVER] '{player_name}' cleaned up | Online now: {len(self.active_names)} | Waiting: {len(self.waiting_queue)}")

        # Thử ghép đôi lại những người đang chờ
        if self.running:
            time.sleep(0.25)
            self._try_match_players()


    def stop(self):
        """Stop the server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("[SERVER] Stopped")
        

if __name__ == '__main__':
    server = WordChainServer()
    server.start()