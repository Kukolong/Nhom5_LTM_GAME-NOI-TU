"""
Word Chain Game
"""

import socket
import json
import time
import threading
from queue import Queue


class WordChainClientV3:
    """Simple client for word chain game."""
    
    def __init__(self, host='localhost', port=5000, player_name='Player'):
        self.host = host
        self.port = port
        self.player_name = player_name
        
        self.socket = None
        self.connected = False
        self.message_queue = Queue()
        self.stop_event = threading.Event()
        
        self.opponent_name = None
        self.current_word = None
        self.next_letter = None
        self.your_turn = False
        self.word_history = []
        self.used_words = set()
        self.game_active = False
    
    def connect(self):
        """Connect to server and send player name."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(None)  # No timeout
            self.socket.connect((self.host, self.port))
            
            # Send player name
            name_msg = json.dumps({'type': 'name', 'value': self.player_name}, ensure_ascii=False)
            self.socket.sendall((name_msg + '\n').encode('utf-8'))
            
            self.connected = True
            print(f"[CLIENT] Connected to server, waiting for match...")
            
            # Start receiver thread
            receiver_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receiver_thread.start()
            
            return True
        except Exception as e:
            print(f"[CLIENT] Connection failed: {e}")
            return False
    
    def receive_messages(self):
        """Receive messages from server."""
        buffer = ""
        try:
            while self.connected and not self.stop_event.is_set():
                try:
                    print("[RECV] Waiting for data...", flush=True)
                    data = self.socket.recv(1024).decode('utf-8')
                    print(f"[RECV] Got: {repr(data[:50])}", flush=True)
                    if not data:
                        print("[RECV] Empty - disconnected", flush=True)
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line)
                                print(f"[RECV] Message: {message.get('type')}", flush=True)
                                self.message_queue.put(message)
                            except json.JSONDecodeError:
                                pass
                except Exception as e:
                    print(f"[RECV] Error: {e}", flush=True)
                    break
        except Exception as e:
            print(f"[RECV] Thread error: {e}", flush=True)
        finally:
            self.connected = False
            print("[RECV] Exited", flush=True)
    
    def process_messages(self):
        """Process all messages in queue."""
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                self.handle_message(message)
            except:
                break
    
    def handle_message(self, message):
        """Handle server message."""
        msg_type = message.get('type')
        
        if msg_type == 'game_start':
            self.opponent_name = message.get('opponent_name')
            self.current_word = message.get('current_word')
            self.next_letter = message.get('next_letter')
            self.your_turn = message.get('your_turn', False)
            self.game_active = True
            self.word_history = [self.current_word]
            self.used_words = {self.current_word}
            
            print(f"\n{'='*50}")
            print(f"[GAME START] vs {self.opponent_name}")
            print(f"Starting word: {self.current_word}")
            print(f"Your turn: {self.your_turn}")
            print(f"{'='*50}\n")
        
        elif msg_type == 'word_accepted':
            word = message.get('word')
            player = message.get('player')
            next_letter = message.get('next_letter')
            
            self.current_word = word
            self.next_letter = next_letter
            self.word_history.append(word)
            self.used_words.add(word)
            self.your_turn = message.get('your_turn', False)
            
            print(f"\n[GAME] {player}: {word}")
            print(f"Next letter: {next_letter}")
            print(f"Your turn: {self.your_turn}")
        
        elif msg_type == 'error':
            print(f"\n[ERROR] {message.get('message')}")
            self.your_turn = message.get('your_turn', False)
        
        elif msg_type == 'opponent_eliminated':
            print(f"\n[GAME OVER] {message.get('opponent')} eliminated!")
            print(f"Reason: {message.get('reason')}")
            self.game_active = False
        
        elif msg_type == 'opponent_disconnected':
            print(f"\n[GAME OVER] Opponent disconnected")
            self.game_active = False
    
    def send_word(self, word):
        """Send a word to server."""
        if not self.connected:
            print("[CLIENT] Not connected")
            return False
        
        try:
            word = word.strip().lower()
            msg = json.dumps({'type': 'word', 'value': word}, ensure_ascii=False)
            self.socket.sendall((msg + '\n').encode('utf-8'))
            return True
        except Exception as e:
            print(f"[CLIENT] Error sending word: {e}")
            return False
    
    def play(self):
        """Main game loop."""
        print(f"Waiting for opponent...\n", flush=True)
        
        # Wait for game start
        counter = 0
        while not self.game_active and self.connected:
            counter += 1
            if counter % 10 == 0:
                print(f"[MAIN] Still waiting... connected={self.connected}, game_active={self.game_active}", flush=True)
            self.process_messages()
            time.sleep(0.1)
        
        if not self.connected:
            print("[CLIENT] Disconnected", flush=True)
            return
        
        # Game loop
        while self.game_active and self.connected:
            self.process_messages()
            
            if self.your_turn:
                print(f"\n[YOUR TURN] Next letter: {self.next_letter}")
                word = input("Enter word: ")
                if word.lower() == 'quit':
                    break
                self.send_word(word)
                self.your_turn = False
            
            time.sleep(0.1)
    
    def disconnect(self):
        """Disconnect from server."""
        self.stop_event.set()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False


def main():
    """Main entry point."""
    player_name = input("Enter player name: ").strip() or "Player"
    
    client = WordChainClientV3(player_name=player_name)
    
    if client.connect():
        client.play()
    
    client.disconnect()


if __name__ == '__main__':
    main()
