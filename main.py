import tkinter as tk
from app_translator import TranslatorApp

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x800")  # 设置初始窗口大小为 800x600 像素
    app = TranslatorApp(root)
    root.mainloop()
