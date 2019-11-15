ENCODING_DICT = {
    '/': '_slash_',
    '?': '_qmark_',
}


def encode_url(url):
    new_url = url
    for char in ENCODING_DICT.keys():
        new_url = new_url.replace(char, ENCODING_DICT[char])
    return new_url


def decode_url(url):
    new_url = url
    for char in ENCODING_DICT.keys():
        new_url = new_url.replace(ENCODING_DICT[char], char)
    new_url = new_url.replace(' ', '%20')
    return new_url
