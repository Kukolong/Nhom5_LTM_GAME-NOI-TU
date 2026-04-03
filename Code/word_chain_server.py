"""
Word Chain Game - Server v3
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
        self.game_active = True
        self.game_lock = threading.Lock()
        
        # Game state
        self.current_word = random.choice(list(dictionary))
        self.current_player_socket = None
        self.current_player_name = None
        self.word_history = [(self.current_word, "System")]
        self.used_words = {self.current_word}
        
        # Randomly pick who starts
        if random.random() < 0.5:
            self.current_player_socket = player1_socket
            self.current_player_name = player1_name
        else:
            self.current_player_socket = player2_socket
            self.current_player_name = player2_name
        
        # Timing
        self.turn_start_time = time.time()
        self.turn_timeout = 10  # seconds per turn
        
        print(f"[MATCH] Started: {player1_name} vs {player2_name} | Starting word: {self.current_word} | {self.current_player_name}'s turn")
    
    def get_next_player_socket(self):
        """Get the socket of the player who's not current."""
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
    
    def switch_turn(self):
        """Switch to next player's turn."""
        self.current_player_socket = self.get_next_player_socket()
        self.current_player_name = self.get_next_player_name()
        self.turn_start_time = time.time()


class WordChainServerV3:
    """
    Simple TCP server - immediate match-found system.
    2 players connect -> game starts.
    """
    
    def __init__(self, host='localhost', port=5000, dictionary_file='vietnamese_dictionary.txt'):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # Waiting queue
        self.waiting_queue = []  # List of (socket, name)
        self.queue_lock = threading.Lock()
        
        # Active matches
        self.matches = {}  # {player_socket: Match}
        self.matches_lock = threading.Lock()
        
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
            
            print(f"[SERVER] Player '{player_name}' from {client_addr} waiting for match...")
            
            # Add to waiting queue
            match = None
            with self.queue_lock:
                self.waiting_queue.append((client_socket, player_name))
                
                # Check if we have 2 players - if so, start a match
                if len(self.waiting_queue) >= 2:
                    # Pop 2 players from queue
                    player1_socket, player1_name = self.waiting_queue.pop(0)
                    player2_socket, player2_name = self.waiting_queue.pop(0)
                    
                    # Create match
                    match = Match(player1_socket, player1_name, player2_socket, player2_name, self.dictionary)
                    
                    with self.matches_lock:
                        self.matches[player1_socket] = match
                        self.matches[player2_socket] = match
                    
                    # Send start message to player 1
                    start_msg_p1 = {
                        'type': 'game_start',
                        'opponent_name': player2_name,
                        'current_word': match.current_word,
                        'next_letter': get_next_letter_constraint(match.current_word),
                        'your_turn': match.current_player_name == player1_name
                    }
                    self.send_message(player1_socket, start_msg_p1)
                    
                    # Send start message to player 2
                    start_msg_p2 = {
                        'type': 'game_start',
                        'opponent_name': player1_name,
                        'current_word': match.current_word,
                        'next_letter': get_next_letter_constraint(match.current_word),
                        'your_turn': match.current_player_name == player2_name
                    }
                    self.send_message(player2_socket, start_msg_p2)
            
            # If not in a match yet, wait for match
            if match is None:
                while match is None and self.running:
                    with self.matches_lock:
                        if client_socket in self.matches:
                            match = self.matches[client_socket]
                    time.sleep(0.1)
            
            # Main game loop - handle word submissions
            buffer = ""
            while self.running and client_socket in self.matches:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                msg_data = json.loads(line)
                                if msg_data.get('type') == 'word':
                                    word = msg_data.get('value', '').strip().lower()
                                    self.process_word_submission(client_socket, player_name, word)
                            except json.JSONDecodeError:
                                pass
                
                except Exception as e:
                    print(f"[SERVER] Error in game loop: {e}")
                    break
        
        except Exception as e:
            print(f"[SERVER] Error handling player {client_addr}: {e}")
            if player_name:
                print(f"[SERVER] Player '{player_name}' error: {e}")
        
        finally:
            # Remove from queue if still there
            with self.queue_lock:
                self.waiting_queue = [(s, n) for s, n in self.waiting_queue if s != client_socket]
            
            # Remove from active matches
            with self.matches_lock:
                if client_socket in self.matches:
                    match = self.matches.pop(client_socket)
                    opponent_socket = match.player2_socket if match.player1_socket == client_socket else match.player1_socket
                    
                    if opponent_socket in self.matches:
                        del self.matches[opponent_socket]
                    
                    # Notify opponent
                    if opponent_socket:
                        try:
                            self.send_message(opponent_socket, {
                                'type': 'opponent_disconnected',
                                'message': f"{player_name} disconnected"
                            })
                        except:
                            pass
            
            # Close socket
            try:
                client_socket.close()
            except:
                pass
            
            if player_name:
                print(f"[SERVER] Player '{player_name}' disconnected")
    
    def process_word_submission(self, player_socket, player_name, word):
        """Process a word submission from a player."""
        with self.matches_lock:
            if player_socket not in self.matches:
                return
            
            match = self.matches[player_socket]
        
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
            if len(word) < 2:
                self.send_message(player_socket, {
                    'type': 'error',
                    'message': 'Word must be at least 2 characters',
                    'your_turn': True
                })
                return
            
            # Check if word starts with correct letter
            required_letter = get_next_letter_constraint(match.current_word)
            if not is_valid_chain_move(word, match.current_word):
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
            
            # Word is valid - accept it
            match.current_word = word
            match.used_words.add(word)
            match.word_history.append((word, player_name))
            next_letter = get_next_letter_constraint(word)
            
            match.switch_turn()
            
            # Get opponent socket
            opponent_socket = match.get_next_player_socket()
            
            # Message to current player
            msg_current = {
                'type': 'word_accepted',
                'word': word,
                'player': player_name,
                'next_letter': next_letter,
                'your_turn': False
            }
            self.send_message(player_socket, msg_current)
            
            # Message to opponent
            msg_opponent = {
                'type': 'word_accepted',
                'word': word,
                'player': player_name,
                'next_letter': next_letter,
                'your_turn': True
            }
            self.send_message(opponent_socket, msg_opponent)
            
            print(f"[GAME] {player_name}: {word} -> next: {next_letter}")
    
    def send_message(self, client_socket, data):
        """Send JSON message to client."""
        try:
            message = json.dumps(data, ensure_ascii=False)
            client_socket.sendall((message + '\n').encode('utf-8'))
        except Exception as e:
            print(f"[SERVER] Error sending message: {e}")
    
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
    server = WordChainServerV3()
    server.start()
