
class DocumentLibs:
    ALLOWED_EXTENSIONS = {".txt", ".pdf", ".md"}

    @staticmethod
    def allowed_file(filename: str) -> bool:
        if "." not in filename:
            return False

        ext = "." + filename.rsplit(".", 1)[-1].lower()
        return ext in DocumentLibs.ALLOWED_EXTENSIONS

    @staticmethod
    def get_allowed_extensions() -> list[str]:
        return list(DocumentLibs.ALLOWED_EXTENSIONS)
