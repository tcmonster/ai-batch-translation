from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from config import LANGUAGE_CODES, LANGUAGES, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_PROMPT_TEMPLATE
from service_translation import TranslationService
import os
from dotenv import load_dotenv

class TerminalUI:
    def __init__(self):
        self.console = Console()
        self.translation_service = TranslationService()
        self.token_counts = {}

    def display_title(self):
        self.console.print(Panel.fit("[bold cyan]多语言翻译器[/bold cyan]", border_style="cyan"))

    def get_input_file(self):
        while True:
            file_path = Prompt.ask("请输入文件路径")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return file.read(), file_path
                except Exception as e:
                    self.console.print(f"[red]读取文件失败: {str(e)}[/red]")
            else:
                self.console.print("[red]文件不存在，请重新输入[/red]")

    def get_config(self):
        self.console.print("\n[bold]翻译配置[/bold]")
        model = Prompt.ask("模型", default=DEFAULT_MODEL)
        temperature = float(Prompt.ask("温度", default=str(DEFAULT_TEMPERATURE)))
        prompt_template = Prompt.ask("提示词模板", default=DEFAULT_PROMPT_TEMPLATE)
        special_requirements = Prompt.ask("特殊要求（可选）", default="")

        return {
            "model": model,
            "temperature": temperature,
            "prompt_template": prompt_template,
            "special_requirements": special_requirements
        }

    def select_languages(self):
        while True:
            self.console.print("\n[bold]目标语言选择[/bold]")
            # Show available languages with numbers
            for i, lang in enumerate(LANGUAGES, 1):
                self.console.print(f"{i}. {lang}")
                
            selected = Prompt.ask(
                "请选择目标语言（多选请用逗号分隔，如：1,2,3）",
                show_choices=False  # Remove choices parameter to allow multiple inputs
            )
            
            # 解析选择的序号
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in selected.split(',')]
                # 验证所有输入的序号是否有效
                if any(i < 0 or i >= len(LANGUAGES) for i in selected_indices):
                    raise ValueError("序号超出范围")
                selected_languages = [LANGUAGES[i] for i in selected_indices]
                
                # 显示选择结果
                table = Table(show_header=True, header_style="bold")
                table.add_column("序号", style="dim")
                table.add_column("语言")
                table.add_column("选择状态")

                for i, lang in enumerate(LANGUAGES, 1):
                    status = "[green]✓[/green]" if lang in selected_languages else "[red]✗[/red]"
                    table.add_row(str(i), lang, status)

                self.console.print(table)
                
                if selected_languages:
                    return selected_languages
                else:
                    self.console.print("[yellow]警告：未选择任何语言，请重新选择[/yellow]")
            except (ValueError, IndexError) as e:
                self.console.print(f"[red]输入格式错误：{str(e)}，请重新输入有效的序号[/red]")


    def save_translation(self, translated_text, original_file_path, lang):
        # Split the path into components
        file_parts = original_file_path.split('.')
        file_extension = file_parts[-1]  # Get the file extension
        
        # Remove the language code and extension
        # Join all parts except the last two (language and extension)
        base_file_name = '.'.join(file_parts[:-2])
        
        # Get language code from config
        lang_code = LANGUAGE_CODES[lang]
        
        # Handle empty language code (like English)
        suffix = f".{lang_code}" if lang_code else ""
        
        # Construct new filename with target language code
        output_file_name = f"{base_file_name}{suffix}.{file_extension}"
        
        with open(output_file_name, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
        return output_file_name

    def run(self):
        self.display_title()

        # 获取输入
        input_result = self.get_input_file()
        input_content = input_result[0]
        original_file_path = input_result[1]

        # 获取配置
        config = self.get_config()

        # 选择目标语言
        target_languages = self.select_languages()
        if not target_languages:
            self.console.print("[red]请至少选择一种目标语言[/red]")
            return

        # 开始翻译
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            translate_task = progress.add_task("[cyan]翻译进行中...", total=len(target_languages))

            for lang in target_languages:
                progress.update(translate_task, description=f"[cyan]正在翻译 {lang}...")
                try:
                    translated_text, tokens_used = self.translation_service.translate(input_content, lang, config)
                    self.token_counts[lang] = tokens_used

                    saved_file = self.save_translation(translated_text, original_file_path, lang)
                    self.console.print(f"\n[green]{lang} 翻译完成，已保存至: {saved_file}[/green]")

                    progress.advance(translate_task)
                except Exception as e:
                    self.console.print(f"\n[red]{lang} 翻译失败: {str(e)}[/red]")

        # 显示 token 统计
        total_tokens = sum(self.token_counts.values())
        self.console.print("\n[bold]Token 统计[/bold]")
        token_table = Table(show_header=True, header_style="bold magenta")
        token_table.add_column("语言")
        token_table.add_column("Token 数量")
        
        for lang, count in self.token_counts.items():
            token_table.add_row(lang, str(count))
        token_table.add_row("总计", str(total_tokens), style="bold")
        
        self.console.print(token_table)