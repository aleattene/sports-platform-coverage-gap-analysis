import re
import unicodedata


def slugify(value: str) -> str:
    """
    Converts a string into a filesystem-safe slug using only ASCII letters,
    digits and underscores.

    :param value: the input string to be slugified
    :return: a slugified version of the input string
    """
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value
