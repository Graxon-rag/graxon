class ModelCredentialLibs:

    @staticmethod
    def get_hash_api_key(api_key: str) -> str:
        hashed = api_key

        if len(hashed) <= 6:
            return hashed  # too short to mask

        return f"xxxxxxxxxxxxxx{hashed[-5:]}"
