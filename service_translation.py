from openai import OpenAI
import os
from dotenv import load_dotenv
import tiktoken

class TranslationService: 
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_API_BASE")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def count_tokens(self, text, model):
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))

    def translate(self, input_content, target_language, config):
        special_requirements = config.get('special_requirements', '')
        prompt = config['prompt_template'].format(lang=target_language)
        if special_requirements:
            prompt += f"\n特殊要求：{special_requirements}"
        
        model = config['model']
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_content}
        ]

        # 计算输入的token数
        input_tokens = sum(self.count_tokens(msg["content"], model) for msg in messages)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=config['temperature'],
                timeout=30,  # 设置30秒超时
            )
        except Exception as e:
            print(f"OpenAI API 调用出错: {str(e)}")
            return None, 0
        
        translated_text = response.choices[0].message.content

        # 计算输出的token数
        output_tokens = self.count_tokens(translated_text, model)

        # 总token数 = 输入token数 + 输出token数
        total_tokens = input_tokens + output_tokens

        return translated_text, total_tokens
