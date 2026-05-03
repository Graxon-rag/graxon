from pydantic import BaseModel
import re
import secrets
import string


class ParseId(BaseModel):
    project_id: str
    document_id: str
    chunk_id: str


class IDLibs:

    # --- Core helpers ---
    @staticmethod
    def slugify_name(name: str, length: int = 10) -> str:
        """Normalize a name to lowercase alphanumeric, max `length` chars."""
        cleaned = re.sub(r'[^a-z0-9]', '', name.lower())
        return cleaned[:length]

    @staticmethod
    def short_id(length: int = 4) -> str:
        """Generate a short random alphanumeric ID (no ambiguous chars)."""
        alphabet = string.ascii_lowercase + string.digits
        # Remove ambiguous chars: 0, o, 1, l, i
        alphabet = re.sub(r'[01oil]', '', alphabet)
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    # --- ID generators ---

    @staticmethod
    def generate_project_id(name: str) -> str:
        """
        Format: <10-char-slug>_<4-char-random>
        Example: ecommercep_x4k2
        """
        slug = IDLibs.slugify_name(name, length=10)
        if not slug:
            raise ValueError(f"Project name '{name}' produces an empty slug.")
        return f"{slug}_{IDLibs.short_id(4)}"

    @staticmethod
    def generate_document_id(project_id: str) -> str:
        """
        Format: <project_id>_doc_<4-char-random>
        Example: ecommercep_x4k2_doc_m9p3
        """
        return f"{project_id}_doc_{IDLibs.short_id(4)}"

    @staticmethod
    def generate_chunk_id(document_id: str) -> str:
        """
        Format: <document_id>_chunk_<4-char-random>
        Example: ecommercep_x4k2_doc_m9p3_chk_r7w1
        """
        return f"{document_id}_chunk_{IDLibs.short_id(4)}"

    # --- Validators ---

    @staticmethod
    def validate_document_id(document_id: str, project_id: str) -> bool:
        """Check that document_id is correctly prefixed with project_id."""
        return document_id.startswith(f"{project_id}_doc_")

    @staticmethod
    def validate_chunk_id(chunk_id: str, document_id: str) -> bool:
        """Check that chunk_id is correctly prefixed with document_id."""
        return chunk_id.startswith(f"{document_id}_chk_")

    # --- Parsers (extract parent IDs from a child ID) ---

    @staticmethod
    def parse_project_id(document_id: str) -> str:
        """Extract the project_id embedded in a document_id."""
        parts = document_id.split("_doc_")
        if len(parts) != 2:
            raise ValueError(f"Not a valid document_id: '{document_id}'")
        return parts[0]

    @staticmethod
    def parse_document_id(chunk_id: str) -> str:
        """Extract the document_id embedded in a chunk_id."""
        parts = chunk_id.split("_chunk_")
        if len(parts) != 2:
            raise ValueError(f"Not a valid chunk_id: '{chunk_id}'")
        return parts[0]

    @staticmethod
    def parse_all(chunk_id: str) -> ParseId:
        """Extract all parent IDs from a chunk_id in one call."""
        document_id = IDLibs.parse_document_id(chunk_id)
        project_id = IDLibs.parse_project_id(document_id)
        return ParseId(project_id=project_id, document_id=document_id, chunk_id=chunk_id)
