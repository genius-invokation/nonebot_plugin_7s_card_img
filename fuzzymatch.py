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
    result = { 
        "query": input_text, 
        "matched": False, 
        "fallback": [], 
    } 


    # 1. ID 
    if normalized_input.isdigit(): 
        for item in database: 
            if normalized_input == str(item["id"]): 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 


    # 2. 名称 
    for item in database: 
        if normalized_input == normalize(item["name"]): 
            result["query"] = str(item["id"]) 
            result["matched"] = True 
            result["fallback"].append(item["name"]) 
            return result 


    # 3. 别名 
    for item in database: 
        if normalized_input in item["aliases"]: 
            result["query"] = str(item["id"]) 
            result["matched"] = True 
            result["fallback"].append(item["name"]) 
            return result 


    # 4. 名称子串 
    for item in database: 
        if normalized_input in normalize(item["name"]): 
            result["query"] = str(item["id"]) 
            result["matched"] = True 
            result["fallback"].append(item["name"]) 
            return result 


    # 5. 拼音 
    if is_pure_alpha(normalized_input): 
        for item in database: 
            if normalized_input == normalize(item["pinyin"]): 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 


    pinyin_variants = get_all_pinyin_combinations(normalized_input) 
    for item in database: 
        target_pinyin = normalize(item["pinyin"]) 
        for variant in pinyin_variants: 
            if normalize(variant) == target_pinyin: 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 


    # 6. 英文名称 
    if is_pure_alpha(normalized_input) and len(input_text) > 3: 
        for item in database: 
            if normalized_input in normalize(item["englishName"]): 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 


    # 7. child 
    for item in database: 
        for child in item["child"]: 
            if normalized_input == str(child["id"]): 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 
            if normalized_input == normalize(child["name"]): 
                result["query"] = str(item["id"]) 
                result["matched"] = True 
                result["fallback"].append(item["name"]) 
                return result 


    for item in database: 
        # 1. 包含名称 
        if normalize(item["name"]) in normalized_input: 
            result["fallback"].append(item["name"]) 
        # 2. 别名拼音 
        for alias in item["aliases"]: 
            if len(list(set(pinyin_variants) & set(get_all_pinyin_combinations(alias)))) > 0: 
                result["fallback"].append(item["name"]) 
                break 
        # 3. child拼音 
        for child in item["child"]: 
            if len(list(set(pinyin_variants) & set(get_all_pinyin_combinations(child["name"])))) > 0: 
                result["fallback"].append(item["name"]) 
                break 
        # 4. 拼音字串 
        for variant in pinyin_variants: 
            if variant in item["pinyin"] and (len(variant) * len(variant) / len(item["pinyin"]) >= 1.8): 
                result["fallback"].append(item["name"]) 
                break 

    result["fallback"] = list(set(result["fallback"])) 

    return result 
