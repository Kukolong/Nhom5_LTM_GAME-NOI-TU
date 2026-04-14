"""
Game nối từ - Module tiện ích kiểm tra từ
Xử lý chuẩn hóa ký tự tiếng Việt và các quy tắc của game nối từ.
"""

import unicodedata
import re


def normalize_vietnamese(text):
    """
    Chuẩn hóa văn bản tiếng Việt về dạng NFC (Composed).
    Đảm bảo xử lý nhất quán các ký tự tiếng Việt có dấu.
    
    Args:
        text: Chuỗi đầu vào (tiếng Việt hoặc bất kỳ văn bản Unicode nào)
    
    Returns:
        Chuỗi đã được chuẩn hóa ở dạng NFC
    """
    return unicodedata.normalize('NFC', text.strip().lower())


def remove_accents(text):
    """
    Loại bỏ dấu tiếng Việt khỏi văn bản.
    Hữu ích cho việc so sánh không phân biệt hoa thường và không phân biệt dấu.
    
    Args:
        text: Chuỗi đầu vào
    
    Returns:
        Chuỗi không chứa các dấu phụ (danh mục Mn)
    """
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def is_valid_chain_move(previous_word, new_word):
    """
    Kiểm tra xem từ mới có tuân theo luật game nối từ hay không:
    Chữ đầu tiên của từ mới phải trùng với chữ cuối cùng của từ trước đó.
    
    Args:
        previous_word: Cụm từ hợp lệ đã được đánh trước đó
        new_word: Cụm từ mới cần kiểm tra
    
    Returns:
        True nếu từ mới bắt đầu bằng chữ cuối của từ trước đó, False nếu ngược lại
    """
    if not previous_word or not new_word:
        return False
    
    # Chuẩn hóa cả hai cụm từ
    prev_normalized = normalize_vietnamese(previous_word)
    new_normalized = normalize_vietnamese(new_word)
    
    if not prev_normalized or not new_normalized:
        return False
    
    # Tách thành các chữ
    prev_words = prev_normalized.split()
    new_words = new_normalized.split()
    
    if not prev_words or not new_words:
        return False
    
    # Lấy chữ cuối cùng trong cụm từ trước
    prev_last_word = prev_words[-1]
    # Lấy chữ đầu tiên trong cụm từ mới
    new_first_word = new_words[0]
    
    return prev_last_word == new_first_word


def get_next_letter_constraint(word):
    """
    Lấy chữ bắt buộc mà cụm từ của người chơi tiếp theo phải dùng để bắt đầu.
    
    Args:
        word: Cụm từ hợp lệ cuối cùng trong chuỗi
    
    Returns:
        Chữ cuối cùng đã được chuẩn hóa trong cụm từ (chữ thường, chuẩn hóa NFC)
    """
    normalized = normalize_vietnamese(word)
    words = normalized.split()
    if words:
        return words[-1]
    return None


def load_dictionary(filepath):
    """
    Tải từ điển từ file vào một cấu trúc set để tra cứu nhanh với độ phức tạp O(1).

    Args:
        filepath (str): Đường dẫn đến file từ điển

    Returns:
        set: Tập hợp các từ đã được chuẩn hóa

    Raises:
        FileNotFoundError: nếu không tìm thấy file
    """
    words = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                normalized = normalize_vietnamese(word)
                if normalized:
                    words.add(normalized)
    return words


def is_valid_word(word, dictionary):
    """
    Kiểm tra xem một từ có tồn tại trong tập hợp từ điển đã cho hay không.

    Args:
        word (str): Từ cần kiểm tra
        dictionary (set): Tập hợp các từ đã chuẩn hóa

    Returns:
        bool: True nếu từ có trong từ điển
    """
    normalized = normalize_vietnamese(word)
    return normalized in dictionary


def validate_player_name(name):
    """
    Kiểm tra tính hợp lệ cơ bản cho tên người chơi.
    
    Args:
        name: Tên người chơi cần kiểm tra
    
    Returns:
        Tuple (is_valid, error_message) chứa trạng thái hợp lệ và thông báo lỗi
    """
    if not name:
        return False, "Player name cannot be empty"
    
    if len(name) > 30:
        return False, "Player name too long (max 30 characters)"
    
    return True, ""


if __name__ == "__main__":
    # Các test case đơn giản
    print("=== Word Chain Game - Validation Tests ===\n")
    
    # Test 1: Chuẩn hóa tiếng Việt
    print("Test 1: Vietnamese Normalization")
    test_words = ["Tiến", "TIẾN", "tiến"]
    for word in test_words:
        normalized = normalize_vietnamese(word)
        print(f"  '{word}' → '{normalized}'")
    
    # Test 2: Kiểm tra luật nối từ
    print("\nTest 2: Chain Validation")
    test_cases = [
        ("xe máy", "máy bay", True),
        ("máy bay", "bay lượn", True),
        ("xe máy", "xe đạp", False),
        ("bàn ghế", "ghế đẩu", True),
        ("thời gian", "gian khổ", True),
        ("con mèo", "con chó", False),
    ]
    for prev, new, expected in test_cases:
        result = is_valid_chain_move(prev, new)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{prev}' → '{new}': {result} (expected {expected})")
    
    # Test 3: Ràng buộc chữ tiếp theo
    print("\nTest 3: Next Word Constraint")
    test_words = ["xe máy", "máy bay", "bay lượn"]
    for word in test_words:
        next_letter = get_next_letter_constraint(word)
        print(f"  '{word}' → next word must start with: '{next_letter}'")
    
    # Test 4: Kiểm tra tên người chơi
    print("\nTest 4: Player Name Validation")
    test_names = ["Alice", "Player 123", "a", "a" * 25, "Alice@123"]
    for name in test_names:
        is_valid, msg = validate_player_name(name)
        status = "✓" if is_valid else "✗"
        print(f"  {status} '{name}': {is_valid} {msg if msg else ''}")
    
    print("\n=== Tests completed ===")
