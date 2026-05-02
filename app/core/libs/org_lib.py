import re


class OrgLib:

    @staticmethod
    def get_parsed_org_id(name: str) -> str:
        if not name:
            return ""

        # lowercase
        parsed = name.lower()

        # remove spaces
        parsed = parsed.replace(" ", "")

        # keep only alphanumeric characters
        parsed = re.sub(r"[^a-z0-9]", "", parsed)

        # limit to 15 chars
        return parsed[:15]
