import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import os
import threading
from config import LANGUAGE_CODES, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_PROMPT_TEMPLATE

class InputFrame(ttk.Frame):
    def __init__(self, master, upload_callback):
        super().__init__(master)
        self.pack_propagate(False)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="文本输入")

        self.file_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.file_frame, text="文件上传")

        self.input_text = scrolledtext.ScrolledText(self.text_frame, height=10, width=50)
        self.input_text.pack(fill=tk.BOTH, expand=True)


        self.upload_button = tk.Button(self.file_frame, text="上传文件", command=upload_callback)
        self.upload_button.pack()
        self.file_label = tk.Label(self.file_frame, text="未选择文件")
        self.file_label.pack()

        self.file_path = None

    def upload_file(self):
        self.file_path = filedialog.askopenfilename()
        return self.file_path

    def set_file_label(self, text):
        self.file_label.config(text=text)

    def get_input(self):
        if self.is_file_input() and self.file_path:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return self.input_text.get('1.0', tk.END).strip()

    def is_file_input(self):
        return self.notebook.index(self.notebook.select()) == 1

    def save_translated_file(self, translated_text, lang):
        file_name, file_extension = os.path.splitext(self.file_path)
        base_name = os.path.basename(file_name)
        dir_name = os.path.dirname(file_name)
        
        # Remove existing language code if present
        parts = base_name.split('.')
        if len(parts) > 1 and parts[-1] in LANGUAGE_CODES.values():
            base_name = '.'.join(parts[:-1])
        
        # Add new language code
        new_lang_code = LANGUAGE_CODES[lang]
        if new_lang_code:
            output_file_name = f"{base_name}.{new_lang_code}{file_extension}"
        else:
            output_file_name = f"{base_name}{file_extension}"
        
        output_file_path = os.path.join(dir_name, output_file_name)
        
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(translated_text)
        
        return output_file_name

    def reset_file_input(self):
        self.file_path = None
        self.file_label.config(text="未选择文件")

class ConfigFrame(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="配置")
        self.columnconfigure(1, weight=1)

        self.model_label = tk.Label(self, text="模型:")
        self.model_label.grid(row=0, column=0, sticky="w", padx=(5,2), pady=2)
        self.model_entry = tk.Entry(self)
        self.model_entry.grid(row=0, column=1, sticky="ew", padx=(2,5), pady=2)
        self.model_entry.insert(0, DEFAULT_MODEL)

        self.prompt_label = tk.Label(self, text="系统提示词:")
        self.prompt_label.grid(row=1, column=0, sticky="w", padx=(5,2), pady=2)
        self.prompt_entry = tk.Entry(self)
        self.prompt_entry.grid(row=1, column=1, sticky="ew", padx=(2,5), pady=2)
        self.prompt_entry.insert(0, DEFAULT_PROMPT_TEMPLATE)

        self.temp_label = tk.Label(self, text="温度:")
        self.temp_label.grid(row=2, column=0, sticky="w", padx=(5,2), pady=2)
        self.temp_entry = tk.Entry(self)
        self.temp_entry.grid(row=2, column=1, sticky="ew", padx=(2,5), pady=2)
        self.temp_entry.insert(0, str(DEFAULT_TEMPERATURE))

        self.special_req_label = tk.Label(self, text="特殊要求:")
        self.special_req_label.grid(row=3, column=0, sticky="nw", padx=(5,2), pady=2)
        self.special_req_entry = tk.Text(self, height=4, width=40)
        self.special_req_entry.grid(row=3, column=1, sticky="nsew", padx=(2,5), pady=2)

        self.rowconfigure(3, weight=1)

    def get_config(self):
        return {
            "model": self.model_entry.get(),
            "prompt_template": self.prompt_entry.get(),
            "temperature": float(self.temp_entry.get()),
            "special_requirements": self.special_req_entry.get("1.0", tk.END).strip()
        }

class LanguageFrame(ttk.LabelFrame):
    def __init__(self, master, languages):
        super().__init__(master, text="选择目标语言")

        self.languages = languages
        self.language_vars = [tk.IntVar() for _ in self.languages]
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建语言选择框架
        language_frame = ttk.Frame(main_frame)
        language_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建滚动条
        scrollbar = ttk.Scrollbar(language_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建画布
        canvas = tk.Canvas(language_frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=canvas.yview)

        # 创建内部框架来放置复选框
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        # 计算每行应该显示的选项数量
        frame_width = language_frame.winfo_reqwidth()
        checkbox_width = 100  # 估计每个复选框的宽度
        columns = max(3, frame_width // checkbox_width)  # 至少3列，但会根据框架宽度增加

        # 创建横竖混排的复选框
        for i, (lang, var) in enumerate(zip(self.languages, self.language_vars)):
            row = i // columns
            col = i % columns
            cb = ttk.Checkbutton(inner_frame, text=lang, variable=var)
            cb.grid(row=row, column=col, sticky="nsew", padx=5, pady=2)

        # 配置内部框架的列权重，使复选框均匀分布
        for i in range(columns):
            inner_frame.columnconfigure(i, weight=1)

        # 绑定画布大小变化事件
        def on_canvas_configure(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)

        canvas.bind('<Configure>', on_canvas_configure)
        


        # 更新画布的滚动区域
        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # 创建按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 添加全选和取消全选按钮
        select_all_button = ttk.Button(button_frame, text="全选", command=self.select_all)
        select_all_button.pack(side=tk.LEFT, padx=2)

        deselect_all_button = ttk.Button(button_frame, text="取消全选", command=self.deselect_all)
        deselect_all_button.pack(side=tk.LEFT, padx=2)

    def get_selected_languages(self):
        return [lang for lang, var in zip(self.languages, self.language_vars) if var.get()]

    def select_all(self):
        for var in self.language_vars:
            var.set(1)

    def deselect_all(self):
        for var in self.language_vars:
            var.set(0)

class OutputFrame(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="输出")

        self.output_text = scrolledtext.ScrolledText(self, height=10, width=50)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.tag_configure("bold", font=("TkDefaultFont", 14, "bold"), foreground="yellow")

    def clear_output(self):
        self.output_text.delete('1.0', tk.END)

    def add_translation(self, lang, translated_text):
        self.output_text.insert(tk.END, f"{lang} 翻译结果:\n", "bold")
        self.output_text.insert(tk.END, f"{translated_text}\n\n")
        copy_button = tk.Button(self.output_text, text="复制", 
                                command=lambda t=translated_text: self.copy_text(t))
        self.output_text.window_create(tk.END, window=copy_button)
        self.output_text.insert(tk.END, "\n\n")

    def add_log(self, log_text):
        self.output_text.insert(tk.END, f"{log_text}\n")

    def copy_text(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
    
    def add_token_stats(self, token_counts, total_tokens):
        self.output_text.insert(tk.END, "\n--- 总 Token 统计 ---\n", "bold")
        for lang, count in token_counts.items():
            self.output_text.insert(tk.END, f"{lang}: {count} tokens\n")
        self.output_text.insert(tk.END, f"\n总计: {total_tokens} tokens\n")

class ProgressFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.progress = ttk.Progressbar(self, length=300, mode='determinate')
        self.progress.pack(side=tk.LEFT, expand=True)

        self.percent_label = tk.Label(self, text="0%")
        self.percent_label.pack(side=tk.LEFT)

        # 添加 loading 动画
        self.loading_label = tk.Label(self, text="●")
        self.loading_label.pack(side=tk.LEFT)

        # 添加终止按钮
        self.stop_button = tk.Button(self, text="终止", command=self.stop_translation)
        self.stop_button.pack(side=tk.RIGHT)

        self.is_translating = False

    def update_progress(self, value):
        self.progress['value'] = value
        self.percent_label.config(text=f"{value:.1f}%")
        self.master.update_idletasks()

    def start_translation(self):
        self.is_translating = True
        self.stop_button.config(state=tk.NORMAL)
        self.animate_loading()

    def stop_translation(self):
        self.is_translating = False
        self.stop_button.config(state=tk.DISABLED)
        self.loading_label.config(text="●")

    def animate_loading(self):
        if self.is_translating:
            current_text = self.loading_label.cget("text")
            new_text = "●●●" if current_text == "●●" else "●" if current_text == "●●●" else "●●"
            self.loading_label.config(text=new_text)
            self.after(500, self.animate_loading)  # 每500毫秒调用一次
