"""
Word Chain Game - Word Validation Utility Module
Handles Vietnamese character normalization, word chain rules, and dictionary validation.
"""

import unicodedata
import re


def normalize_vietnamese(text):
    """
    Normalize Vietnamese text to NFC (Composed) form.
    This ensures consistent handling of Vietnamese characters with tone marks and accents.
    
    Args:
        text: Input string (Vietnamese or any Unicode text)
    
    Returns:
        Normalized string in NFC form
    """
    return unicodedata.normalize('NFC', text.strip().lower())


def remove_accents(text):
    """
    Remove Vietnamese accents and tone marks from text.
    Useful for case-insensitive and accent-insensitive comparison.
    
    Args:
        text: Input string
    
    Returns:
        String without combining diacritical marks (Mn category)
    """
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def is_valid_chain_move(previous_word, new_word):
    """
    Validate that new_word follows the word chain rule:
    The first letter of the first word in new_word must match the last letter of the last word in previous_word.
    
    Args:
        previous_word: The previously submitted valid phrase
        new_word: The new phrase to validate
    
    Returns:
        True if new_word starts with the last letter of previous_word's last word, False otherwise
    """
    if not previous_word or not new_word:
        return False
    
    # Normalize both phrases
    prev_normalized = normalize_vietnamese(previous_word)
    new_normalized = normalize_vietnamese(new_word)
    
    if not prev_normalized or not new_normalized:
        return False
    
    # Split into words
    prev_words = prev_normalized.split()
    new_words = new_normalized.split()
    
    if not prev_words or not new_words:
        return False
    
    # Get last letter of last word in previous phrase
    prev_last_letter = prev_words[-1][-1]
    # Get first letter of first word in new phrase
    new_first_letter = new_words[0][0]
    
    return prev_last_letter == new_first_letter


def is_valid_word(word, dictionary_set):
    """
    Check if a phrase exists in the Vietnamese dictionary.
    
    Args:
        word: The phrase to validate
        dictionary_set: Set of valid phrases from the dictionary (pre-normalized to NFC, lowercase)
    
    Returns:
        True if word is in dictionary, False otherwise
    """
    normalized = normalize_vietnamese(word)
    return normalized in dictionary_set


def get_next_letter_constraint(word):
    """
    Get the constraint letter that the next player's phrase must start with.
    
    Args:
        word: The last accepted phrase in the chain
    
    Returns:
        The normalized last letter of the last word in the phrase (lowercase, NFC normalized)
    """
    normalized = normalize_vietnamese(word)
    words = normalized.split()
    if words:
        return words[-1][-1]
    return None


def load_dictionary(filepath):
    """
    Load Vietnamese dictionary from file.
    Each line should contain a valid Vietnamese phrase (two words separated by space).
    Phrases are normalized to NFC and lowercase.
    
    Args:
        filepath: Path to the dictionary file
    
    Returns:
        Set of normalized Vietnamese phrases
    
    Raises:
        FileNotFoundError: If dictionary file doesn't exist
        IOError: If there's an error reading the file
    """
    dictionary = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:  # Skip empty lines
                    normalized = normalize_vietnamese(word)
                    if normalized:  # Skip words that become empty after normalization
                        dictionary.add(normalized)
        return dictionary
    except FileNotFoundError:
        raise FileNotFoundError(f"Dictionary file not found: {filepath}")
    except IOError as e:
        raise IOError(f"Error reading dictionary file: {e}")


def validate_player_name(name):
    """
    Basic validation for player name.
    
    Args:
        name: Player name to validate
    
    Returns:
        Tuple (is_valid, error_message)
    """
    if not name:
        return False, "Player name cannot be empty"
    
    if len(name) > 30:
        return False, "Player name too long (max 30 characters)"
    
    return True, ""


if __name__ == "__main__":
    # Simple test cases
    print("=== Word Chain Game - Validation Tests ===\n")
    
    # Test 1: Vietnamese normalization
    print("Test 1: Vietnamese Normalization")
    test_words = ["Tiến", "TIẾN", "tiến"]
    for word in test_words:
        normalized = normalize_vietnamese(word)
        print(f"  '{word}' → '{normalized}'")
    
    # Test 2: Chain validation
    print("\nTest 2: Chain Validation")
    test_cases = [
        ("apple", "egg", True),
        ("dog", "dog", False),
        ("dog", "guitar", False),
        ("can", "nước", True),
        ("mèo", "ốc", True),
        ("mèo", "ốc", True),
    ]
    for prev, new, expected in test_cases:
        result = is_valid_chain_move(prev, new)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{prev}' → '{new}': {result} (expected {expected})")
    
    # Test 3: Next letter constraint
    print("\nTest 3: Next Letter Constraint")
    test_words = ["apple", "mèo", "tiến"]
    for word in test_words:
        next_letter = get_next_letter_constraint(word)
        print(f"  '{word}' → next word must start with: '{next_letter}'")
    
    # Test 4: Player name validation
    print("\nTest 4: Player Name Validation")
    test_names = ["Alice", "Player 123", "a", "a" * 25, "Alice@123"]
    for name in test_names:
        is_valid, msg = validate_player_name(name)
        status = "✓" if is_valid else "✗"
        print(f"  {status} '{name}': {is_valid} {msg if msg else ''}")
    
    print("\n=== Tests completed ===")
