"""Hash handling for cog output verification."""

import re
from .utils import md5


class HashHandler:
    """Handles checksum generation and verification for cog output."""

    def __init__(self, end_output_marker):
        """Initialize the hash handler with the end output marker pattern.

        Args:
            end_output_marker: The end output marker string (e.g., "[[[end]]]")
        """
        self.end_output_marker = end_output_marker
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up regex patterns for hash detection and formatting."""
        end_output = re.escape(self.end_output_marker)
        self.re_end_output_with_hash = re.compile(
            end_output + r"(?P<hashsect> *\(checksum: (?P<hash>[a-f0-9]{32})\))"
        )
        self.end_format = self.end_output_marker + " (checksum: %s)"

    def compute_hash(self, content):
        """Compute MD5 hash of the given content.

        Args:
            content: String content to hash

        Returns:
            str: Hexadecimal hash digest
        """
        hasher = md5()
        hasher.update(content.encode("utf-8"))
        return hasher.hexdigest()

    def compute_lines_hash(self, lines):
        """Compute MD5 hash of a list of lines.

        Args:
            lines: List of line strings

        Returns:
            str: Hexadecimal hash digest
        """
        hasher = md5()
        for line in lines:
            hasher.update(line.encode("utf-8"))
        return hasher.hexdigest()

    def extract_hash_from_line(self, line):
        """Extract hash from an end output line if present.

        Args:
            line: The end output line to check

        Returns:
            str or None: The extracted hash if found, None otherwise
        """
        hash_match = self.re_end_output_with_hash.search(line)
        if hash_match:
            return hash_match["hash"]
        return None

    def validate_hash(self, line, expected_hash):
        """Validate that the hash in the line matches the expected hash.

        Args:
            line: The end output line containing the hash
            expected_hash: The expected hash value

        Returns:
            bool: True if hash matches or no hash present, False if mismatch

        Raises:
            ValueError: If hash is present but doesn't match expected
        """
        hash_match = self.re_end_output_with_hash.search(line)
        if hash_match:
            old_hash = hash_match["hash"]
            if old_hash != expected_hash:
                raise ValueError(
                    "Output has been edited! Delete old checksum to unprotect."
                )
        return True

    def format_end_line_with_hash(self, line, new_hash, add_hash=True):
        """Format the end output line with or without hash.

        Args:
            line: The original end output line
            new_hash: The hash to add if add_hash is True
            add_hash: Whether to add hash to the output

        Returns:
            str: The formatted end output line
        """
        hash_match = self.re_end_output_with_hash.search(line)

        if add_hash:
            if hash_match:
                # Replace existing hash
                endpieces = line.split(hash_match.group(0), 1)
            else:
                # Add new hash
                endpieces = line.split(self.end_output_marker, 1)
            line = (self.end_format % new_hash).join(endpieces)
        else:
            # Remove hash if present
            if hash_match:
                line = line.replace(hash_match["hashsect"], "", 1)

        return line
