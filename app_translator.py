import tkinter as tk
from tkinter import messagebox, ttk
from ui_components import InputFrame, ConfigFrame, LanguageFrame, OutputFrame, ProgressFrame
from service_translation import TranslationService
from config import LANGUAGES
import threading
import queue

class TranslatorApp:
    def __init__(self, master):
        self.master = master
        master.title("多语言翻译器")

        self.token_counts = {}

        self.translation_service = TranslationService()

        # 创建左右分隔的 PanedWindow
        self.paned_window = tk.PanedWindow(master, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 左侧框架
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame)

        # 右侧框架
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame)

        # 在左侧框架中添加输入和设置组件
        self.input_frame = InputFrame(self.left_frame, self.upload_file)
        self.config_frame = ConfigFrame(self.left_frame)
        self.language_frame = LanguageFrame(self.left_frame, LANGUAGES)
        self.translate_button = tk.Button(self.left_frame, text="翻译", command=self.translate)

        # 在右侧框架中添加输出组件
        self.progress_frame = ProgressFrame(self.right_frame)
        self.output_frame = OutputFrame(self.right_frame)

        # 使用 grid 布局管理器来排列左侧组件
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.config_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.language_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.translate_button.grid(row=3, column=0, pady=10)

        # 配置左侧框架的行权重
        self.left_frame.grid_rowconfigure(0, weight=3)
        self.left_frame.grid_rowconfigure(1, weight=2)
        self.left_frame.grid_rowconfigure(2, weight=2)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # 使用 pack 布局管理器来排列右侧组件
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.progress_queue = queue.Queue()

        # 设置 PanedWindow 的初始位置
        self.paned_window.paneconfigure(self.left_frame, width=400)

        self.progress_frame = ProgressFrame(master)
        self.progress_frame.stop_button.config(command=self.stop_translation)

    def reset_token_counts(self):
        self.token_counts.clear()

    def upload_file(self):
        file_path = self.input_frame.upload_file()
        if file_path:
            self.input_frame.set_file_label(f"已选择文件: {file_path}")

    def translate(self):
        config = self.config_frame.get_config()
        input_content = self.input_frame.get_input()
        target_languages = self.language_frame.get_selected_languages()

        if not input_content:
            messagebox.showerror("错误", "请输入文本或选择文件")
            return

        if not target_languages:
            messagebox.showerror("错误", "请至少选择一种目标语言")
            return

        self.should_stop = False
        self.reset_token_counts()
        self.output_frame.clear_output()
        self.progress_frame.update_progress(0)
        self.progress_frame.start_translation()
        

        # 启动一个新线程来执行翻译
        threading.Thread(target=self.translate_thread, args=(config, input_content, target_languages)).start()
        # 启动进度更新
        self.master.after(100, self.update_progress)
    
    def add_log(self, log_text):
        self.output_frame.add_log(log_text)

    def translate_thread(self, config, input_content, target_languages):
        total_languages = len(target_languages)
        for i, lang in enumerate(target_languages):
            if self.should_stop:
                self.progress_queue.put(("DONE", None))
                return
            try:
                translated_text, tokens_used = self.translation_service.translate(input_content, lang, config)
                self.token_counts[lang] = tokens_used

                if self.input_frame.is_file_input():
                    saved_file_name = self.input_frame.save_translated_file(translated_text, lang)
                    log_message = f"{lang}翻译完成，已存为: {saved_file_name}"
                    self.progress_queue.put(("LOG", log_message))
                else:
                    self.output_frame.add_translation(lang, translated_text)
                
                progress = (i + 1) / total_languages * 100
                self.progress_queue.put(("PROGRESS", progress))
            except Exception as e:
                self.progress_queue.put(("ERROR", f"{lang}翻译过程中出现错误: {str(e)}"))

        total_tokens = sum(self.token_counts.values())
        self.progress_queue.put(("TOTAL_TOKEN_COUNT", self.token_counts, total_tokens))
        self.progress_queue.put(("DONE", None))

    def stop_translation(self):
        self.should_stop = True
        self.translation_service.set_stop_flag(True)
        self.progress_frame.stop_translation()

    def update_progress(self):
        try:
            while True:
                message_type, *data = self.progress_queue.get_nowait()
                if message_type == "PROGRESS":
                    self.progress_frame.update_progress(data[0])
                elif message_type == "LOG":
                    self.output_frame.add_log(data[0])
                elif message_type == "ERROR":
                    messagebox.showerror("错误", data[0])
                elif message_type == "TRANSLATION":
                    self.output_frame.add_translation(data[0], data[1])
                elif message_type == "TOKEN_STATS":
                    self.output_frame.add_token_stats(data[0], data[1])
                elif message_type == "DONE":
                    self.progress_frame.update_progress(100)
                    self.progress_frame.stop_translation()
                    self.input_frame.reset_file_input()
                    return  # 翻译完成，停止更新
        except queue.Empty:
            pass
        
        # 继续动画
        self.progress_frame.animate_loading()
        # 总是继续更新，直到翻译结束
        self.master.after(100, self.update_progress)
