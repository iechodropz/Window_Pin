import ctypes
import ctypes.wintypes
import win32con
import threading
import tkinter as tk


class PinWindowApp:
    # TODO
    def __init__(self, tk_window):
        self.is_pinning = False
        self.hook_thread = None

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

    # TODO
    def run_mouse_hook(self):
        # CMPFUNC sets up a bridge for Windows to talk to Python using low_level_mouse_handler() whenever a mouse event occurs.
        # nCode: Is an integer that indicates the type or status of the hook event, if non-negative, it means the hook should process the event. Negative value is for a mouse event that doesn't fit the conditions interested it.
        # wParam: Specifies the type of mouse event that triggered the hook.
        # lParam: A pointer to additional information about the mouse event, it can point to a structure containing details like the X and Y coordinates of the mouse events.
        def low_level_mouse_handler(nCode, wParam, lParam=None):
            if nCode >= 0 and wParam == win32con.WM_LBUTTONDOWN:
                # If milliseconds is 0 in after(), the callback function will be scheduled to run as soon as possible, but it will still be placed in the Tkinter event queue.
                self.tk_window.after(0, self.pin_window)
            # low_level_mouse_handler processes the event, does its own work (calls self.root.after()), and then lets the system continue processing the event, passing it to the next handler in the hook chain.
            # First Parameter: Indicates the next hook to call, by passing None, you're indicating that no specific hook is being referenced and the mouse click should continue its default job.
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        # WINFUNCTYPE must match the low_level_mouse_handler function's signature precisely, this matching is essential because CMPFUNC tells Windows how the callback function is structured in terms of the parameter types and return type.
        # First Argument: Specifies the return type of the function.
        # Second, Third, Fourth Argument: Correspond to nCode, wParam, and lParam in low_level_mouse_handler().
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
        # pointer is now a function pointer that will be passed to SetWindowsHookExA. The system expects a function pointer when setting up a hook procedure, which will be called whenever the specified event happens.
        pointer = CMPFUNC(low_level_mouse_handler)

        # First Parameter: The value 14 corresponds to WH_MOUSE_LL, which stands for a low-level mouse hook.
        # Third Parameter: This is the module handle, None means the hook procedure is in the current module, meaning the python program itself is handling the events.
        # Fourth Parameter: This is the thread ID, a value of 0 means the hook is installed globally for all threads. It ensures that the mouse events are captured system-wide, not just in the current thread.
        self.hook = ctypes.windll.user32.SetWindowsHookExA(14, pointer, None, 0)

    # TODO
    def start_mouse_hook(self):
        # if statement is intedned to ensure that only one thread is running the run_mouse_hook() at any given time.
        if self.hook_thread is None or not self.hook_thread.is_alive():
            # Creates new thread and tells the thread to execute run_mouse_hook() when it starts.
            self.hook_thread = threading.Thread(target=self.run_mouse_hook)
            # Starts thread, which will begin executing concurrently with the main program.
            self.hook_thread.start()

    # TODO
    def start_pin_process(self):
        self.is_pinning = True
        self.pin_button.config(text="Cancel Pinning")
        self.start_mouse_hook()

    # TODO
    def stop_pin_process(self):
        pass

    #TODO
    def toggle_pin_process(self):
        if not self.is_pinning:
            self.start_pin_process()
        else:
            self.stop_pin_process()

    # TODO
    def unpin_window(self):
        pass


if __name__ == "__main__":
    # Initializes a blank window where you can add widgets (like buttons, labels, etc.).
    root = tk.Tk()
    app = PinWindowApp(root)
    # Keeps the application running and continuously checks for events (button clicks, mouse movements, keyboard input, etc.) to respond to them.
    root.mainloop()
