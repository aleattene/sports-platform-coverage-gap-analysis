import re

def slugify(value: str) -> str:
    """
    Converts a string into a slug format suitable for filenames or URLs.
    :param value: the input string to be slugified
    :return: a slugified version of the input string, where:
    - leading and trailing whitespace is removed
    - single quotes are removed
    - forward slashes are replaced with hyphens
    - sequences of whitespace are replaced with a single underscore
    - all characters that are not letters, numbers, underscores, hyphens, or accented characters are removed
    """
    value = value.strip()
    value = value.replace("'", "")
    value = value.replace("/", "-")
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^A-Za-z0-9_\-À-ÿ]", "", value)
    return value
