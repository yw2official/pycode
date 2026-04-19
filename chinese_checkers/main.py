import tkinter as tk
from gui import ChineseCheckersGUI

def main():
    root = tk.Tk()
    root.configure(bg='#0f1923')
    app = ChineseCheckersGUI(root)
    root.mainloop()
if __name__ == '__main__':
    main()