from langchain_text_splitters import Language
from typing import Optional
import os

# Maps file extensions to LangChain Language enum
EXTENSION_TO_LANGUAGE: dict[str, Language] = {
    # Python
    ".py": Language.PYTHON,
    # JavaScript / TypeScript
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    # Golang
    ".go": Language.GO,
    # Rust
    ".rs": Language.RUST,
    # C / C++
    ".c": Language.C,
    ".h": Language.C,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    # C#
    ".cs": Language.CSHARP,
    # HTML
    ".html": Language.HTML,
    ".htm": Language.HTML,
    # Ruby
    ".rb": Language.RUBY,
    # Java
    ".java": Language.JAVA,
    # Kotlin
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    # Swift
    ".swift": Language.SWIFT,
    # Scala
    ".scala": Language.SCALA,
    # Markdown (treat as code-like for structured splitting)
    ".md": Language.MARKDOWN,
    # Latex
    ".tex": Language.LATEX,
    # Sol (Solidity)
    ".sol": Language.SOL,
    # Proto
    ".proto": Language.PROTO,
    # Lua
    ".lua": Language.LUA,
    # Perl
    ".pl": Language.PERL,
    ".pm": Language.PERL,
    # bash/shell
    ".sh": Language.POWERSHELL,
    ".ps1": Language.POWERSHELL,
}


def get_language_from_extension(file_path: str) -> Optional[Language]:
    """
    Returns the LangChain Language enum for a given file path based on its extension.
    Returns None if the extension is not recognized as a code file.

    Usage:
        language = get_language_from_extension("main.py")   # Language.PYTHON
        language = get_language_from_extension("index.ts")  # Language.TS
        language = get_language_from_extension("notes.txt") # None
    """
    ext = os.path.splitext(file_path)[-1].lower()
    return EXTENSION_TO_LANGUAGE.get(ext, None)


def is_code_file(file_path: str) -> bool:
    """
    Returns True if the file extension is a recognized code file.

    Usage:
        is_code_file("main.py")    # True
        is_code_file("notes.txt")  # False
        is_code_file("index.tsx")  # True
    """
    return get_language_from_extension(file_path) is not None
