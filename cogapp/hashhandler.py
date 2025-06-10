"""Hash handling for cog output verification."""

import base64
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
        # Support both old format (checksum: 32-char hex) and new format (sum: 10-char base64)
        self.re_end_output_with_hash = re.compile(
            end_output
            + r"(?P<hashsect> *\((?:checksum: (?P<hash>[a-f0-9]{32})|sum: (?P<b64hash>[A-Za-z0-9+/]{10}))\))"
        )
        self.end_format = self.end_output_marker + " (sum: %s)"

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

    def hex_to_base64_hash(self, hex_hash):
        """Convert a 32-character hex hash to a 10-character base64 hash.

        Args:
            hex_hash: 32-character hexadecimal hash string

        Returns:
            str: 10-character base64 hash string
        """
        # Convert hex to bytes
        hash_bytes = bytes.fromhex(hex_hash)
        # Encode to base64 and take first 10 characters
        b64_hash = base64.b64encode(hash_bytes).decode("ascii")[:10]
        return b64_hash

    def extract_hash_from_line(self, line):
        """Extract hash from an end output line if present.

        Args:
            line: The end output line to check

        Returns:
            tuple: (hash_type, hash_value) where hash_type is 'hex' or 'base64'
                   and hash_value is the raw hash value, or (None, None) if not found
        """
        hash_match = self.re_end_output_with_hash.search(line)
        if hash_match:
            # Check which format was matched
            if hash_match.group("hash"):
                # Old format: checksum with hex
                return ("hex", hash_match.group("hash"))
            else:
                # New format: sum with base64
                assert hash_match.group("b64hash"), (
                    "Regex matched but no hash group found"
                )
                return ("base64", hash_match.group("b64hash"))
        return (None, None)

    def validate_hash(self, line, expected_hash):
        """Validate that the hash in the line matches the expected hash.

        Args:
            line: The end output line containing the hash
            expected_hash: The expected hash value (hex format)

        Returns:
            bool: True if hash matches or no hash present, False if mismatch

        Raises:
            ValueError: If hash is present but doesn't match expected
        """
        hash_type, old_hash = self.extract_hash_from_line(line)
        if hash_type is not None:
            if hash_type == "hex":
                # Compare hex directly
                if old_hash != expected_hash:
                    raise ValueError(
                        "Output has been edited! Delete old checksum to unprotect."
                    )
            else:
                # Convert expected hex to base64 and compare
                assert hash_type == "base64", f"Unknown hash type: {hash_type}"
                expected_b64 = self.hex_to_base64_hash(expected_hash)
                if old_hash != expected_b64:
                    raise ValueError(
                        "Output has been edited! Delete old checksum to unprotect."
                    )
        return True

    def format_end_line_with_hash(
        self, line, new_hash, add_hash=True, preserve_format=False
    ):
        """Format the end output line with or without hash.

        Args:
            line: The original end output line
            new_hash: The hash to add if add_hash is True (hex format)
            add_hash: Whether to add hash to the output
            preserve_format: If True and an existing hash is found, preserve its format

        Returns:
            str: The formatted end output line
        """
        hash_match = self.re_end_output_with_hash.search(line)

        if add_hash:
            if preserve_format and hash_match:
                # Preserve the original format
                hash_type, old_hash = self.extract_hash_from_line(line)
                if hash_type == "hex":
                    # Keep hex format
                    formatted_hash = f" (checksum: {new_hash})"
                else:
                    # Keep base64 format
                    assert hash_type == "base64", f"Unknown hash type: {hash_type}"
                    b64_hash = self.hex_to_base64_hash(new_hash)
                    formatted_hash = f" (sum: {b64_hash})"

                # Replace the hash section
                endpieces = line.split(hash_match.group(0), 1)
                line = (self.end_output_marker + formatted_hash).join(endpieces)
            else:
                # Use new format
                b64_hash = self.hex_to_base64_hash(new_hash)

                if hash_match:
                    # Replace existing hash
                    endpieces = line.split(hash_match.group(0), 1)
                else:
                    # Add new hash
                    endpieces = line.split(self.end_output_marker, 1)
                line = (self.end_format % b64_hash).join(endpieces)
        else:
            # Remove hash if present
            if hash_match:
                line = line.replace(hash_match["hashsect"], "", 1)

        return line
