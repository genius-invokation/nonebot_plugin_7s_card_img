import re
from pypinyin import pinyin, Style
import unicodedata
from itertools import product


def is_pure_alpha(s):
    return re.fullmatch(r'[a-zA-Z]+', s) is not None


def get_all_pinyin_combinations(text):
    pinyin_list = pinyin(text, style=Style.NORMAL, heteronym=True)
    all_combinations = [''.join(item) for item in product(*pinyin_list)]
    return all_combinations


def normalize(text):
    if not isinstance(text, str):
        return ""
    return ''.join(c for c in text if unicodedata.category(c).startswith(('L', 'N'))).lower()


def match_id(input_text, database):
    normalized_input = normalize(input_text)

    # 1. ID
    for item in database:
        if normalized_input == str(item["id"]):
            return str(item["id"])

    # 2. 名称
    for item in database:
        if normalized_input == normalize(item["name"]):
            return str(item["id"])

    # 3. 别名
    for item in database:
        if normalized_input in item["aliases"]:
            return str(item["id"])

    # 4. 拼音
    if is_pure_alpha(normalized_input):
        for item in database:
            if normalized_input == normalize(item["pinyin"]):
                return str(item["id"])

    pinyin_variants = get_all_pinyin_combinations(normalized_input)
    for item in database:
        target_pinyin = normalize(item["pinyin"])
        for variant in pinyin_variants:
            if normalize(variant) == target_pinyin:
                return str(item["id"])

    # 5. 英文名称
    if is_pure_alpha(normalized_input) and len(input_text) > 3:
        for item in database:
            if normalized_input in normalize(item["englishName"]):
                return str(item["id"])

    # 6. child
    for item in database:
        for child in item["child"]:
            if normalized_input == str(child["id"]):
                return str(item["id"])
            if normalized_input == child["name"]:
                return str(item["id"])

    # 7. 匹配失败
    return input_text
