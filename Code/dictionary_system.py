"""
Word Chain Game - Dictionary System

This module manages the full lifecycle of the dictionary:
- Load words from file
- Normalize Vietnamese text
- Store words efficiently using a set
- Provide fast lookup and utility APIs
"""

import random
from word_validation import normalize_vietnamese

class DictionarySystem:
    """
    DictionarySystem handles:
    - Data loading
    - Normalization
    - Fast lookup (O(1))
    """

    def __init__(self, filepath):
        """
        Initialize the dictionary system.

        Args:
            filepath (str): Path to dictionary file

        Behavior:
            - Save file path
            - Initialize internal storage
            - Automatically load dictionary
        """
        self._filepath = filepath      # Private: file path
        self._words = set()            # Private: store normalized words for O(1) lookup
        self.load()                    # Load data immediately

    def load(self, filepath=None):
        """
        Load or reload dictionary from file.

        Args:
            filepath (str, optional): New file path (if reloading)

        Process:
            - Clear old data
            - Read file line by line
            - Normalize each word
            - Store valid words in set

        Raises:
            FileNotFoundError: if file does not exist
            IOError: if file reading fails
        """
        if filepath:
            self._filepath = filepath

        try:
            self._words.clear()  # Reset dictionary

            with open(self._filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()

                    # Skip empty lines
                    if not word:
                        continue

                    # Normalize using external function (reuse existing logic)
                    normalized = normalize_vietnamese(word)

                    # Skip invalid or empty normalized results
                    if not normalized:
                        continue

                    # Add to set (ensures uniqueness + fast lookup)
                    self._words.add(normalized)

        except FileNotFoundError:
            raise FileNotFoundError(f"Dictionary file not found: {self._filepath}")
        except IOError as e:
            raise IOError(f"Error reading dictionary file: {e}")

    def lookup(self, word):
        """
        Check if a word exists in dictionary.

        Args:
            word (str): Input word/phrase

        Returns:
            bool: True if exists, False otherwise

        Complexity:
            O(1) average (set lookup)
        """
        normalized = normalize_vietnamese(word)
        return normalized in self._words

    def get_all(self):
        """
        Get a copy of all words.

        Returns:
            set: Copy of internal word set

        Note:
            Returning a copy prevents external modification
        """
        return self._words.copy()

    def size(self):
        """
        Get total number of words in dictionary.

        Returns:
            int: Number of words
        """
        return len(self._words)

    def get_random_word(self):
        """
        Get a random word from dictionary.

        Used for:
            - Starting a new game
            - Random test cases

        Returns:
            str or None: Random word, or None if empty
        """
        if not self._words:
            return None
        return random.choice(list(self._words))

    def __repr__(self):
        """
        Debug representation of the object.

        Example:
            <DictionarySystem size=1000>
        """
        return f"<DictionarySystem size={len(self._words)}>"
