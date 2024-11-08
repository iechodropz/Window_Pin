import tkinter as tk


class PinWindowApp:
    # TODO
    def __init__(self, tk_window):
        self.tk_window = tk_window
        self.tk_window.title("Window Pin")

        # List to keep track of all pinned windows.
        self.pinned_windows = []

        self.pin_button = tk.Button(tk_window, text="Pin Window", command=self.toggle_pin_process)
        # pack() automatically places the widget (pin_button) inside the tk_window, stacking it from top to bottom.
        # pady adds padding to the top, and bottom of the widget.
        self.pin_button.pack(pady=10)

        self.unpin_button = tk.Button(tk_window, text="Unpin Window", command=self.unpin_window)
        self.unpin_button.pack(pady=10)

    # TODO
    def pin_window(self):
        pass

    #TODO
    def toggle_pin_process(self):
        pass

    # TODO
    def unpin_window(self):
        pass


if __name__ == "__main__":
    # Initializes a blank window where you can add widgets (like buttons, labels, etc.).
    root = tk.Tk()
    app = PinWindowApp(root)
    # Keeps the application running and continuously checks for events (button clicks, mouse movements, keyboard input, etc.) to respond to them.
    root.mainloop()
