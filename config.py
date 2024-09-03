# config.py
LANGUAGE_CODES = {
    "简体中文": "zh",
    "繁体中文": "zh-TW",
    "英语": "",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "意大利语": "it",
    "波兰语": "pl",
    "荷兰语": "nl",
    "土耳其语": "tr",
    "俄语": "ru",
    "保加利亚语": "bg",
    "西班牙语": "es",
    "葡萄牙语": "pt",
    "越南语": "vi",
    "阿拉伯语": "ar"
}

LANGUAGES = list(LANGUAGE_CODES.keys())

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0
DEFAULT_PROMPT_TEMPLATE = "You are a translator, translate the following content into {lang}, only translating the content, paying attention to code formatting."
