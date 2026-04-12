"""
Word Chain Game - Dictionary System
Handles loading and validating words against the dictionary.
"""

from word_validation import normalize_vietnamese


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