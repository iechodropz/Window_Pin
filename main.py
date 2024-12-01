"""
This module provides a GUI-based utility for pinning and unpinning windows
on top of other windows in a Windows environment. It utilizes Windows API
to manage window handles and their positioning.

The application uses the `tkinter` library to build the GUI and `ctypes`
to interact with low-level Windows hooks for mouse events.
"""

import ctypes
import ctypes.wintypes
import threading
import tkinter as tk
from tkinter import messagebox
import atexit
import win32con
import win32gui
from PIL import Image, ImageTk


class PushPinIcon:
    def __init__(self, window_to_pin_handle):
        self.window_to_pin_handle = window_to_pin_handle
        # Creates a new, independent window separate from the main Tk window.
        self.pushpin_window = tk.Toplevel()
        # Set window to always stay on top of all other windows.
        self.pushpin_window.attributes("-topmost", True)
        # Make the color white transparent in the window
        self.pushpin_window.attributes("-transparentcolor", "white")
        self.pushpin_window.overrideredirect(True)

        # Image provides classes and methods for manipulating images.
        image = Image.open("pushpin.png")
        image = image.resize((40, 40))
        # PhotoImage class converts a pillow image into a format that tkinter can use.
        self.pushpin_icon = ImageTk.PhotoImage(image)
        # Widget to display text or images.
        self.label = tk.Label(self.pushpin_window, image=self.pushpin_icon, bg="white")
        self.label.pack()

        self.update_pushpin_position()

    def update_pushpin_position(self):
        try:
            # Rect refers to a rectangle that defines the position and size of a window.
            rect = win32gui.GetWindowRect(self.window_to_pin_handle)
            x = rect[0]
            y = rect[1]

            # The geometry() method is used to set the size and position of a window, the argument passed to it is a string in the format "{width}x{height}+{x}+{y}"
            self.pushpin_window.geometry(f"+{x}+{y}")

            PinWindow.window_z_index(self.pushpin_window, win32con.HWND_TOPMOST)

            # Schedule the nex position update
            self.pushpin_window.after(30, self.update_pushpin_position)
        except Exception:
            # If any issues destroy the pushicon window
            self.pushpin_window.destroy()


class PinWindow:
    """
    A GUI application to pin and unpin windows in a Windows environment.

    Attributes:
        tk_window (Tk): The main Tkinter window for the application.
        is_pinning (bool): Flag to indicate if the app is in the process of pinning a window.
        hook_thread (Thread): A thread for running the mouse hook for window selection.
        hook (function): The callback hook for mouse events.
        pinned_windows (list): List of window handles that are pinned on top.
        pin_button (Button): Button widget to start or cancel the pinning process.
        unpin_button (Button): Button widget to unpin the most recently pinned window.
    """

    def __init__(self, tk_window):
        self.is_pinning = False
        self.hook_thread = None
        self.hook = None
        self.tk_window = tk_window
        self.tk_window.title("Window Pin")
        self.pinned_windows = []
        self.pushpin_root_window_handle = {}

        self.pin_button = tk.Button(
            tk_window, text="Pin Window", command=self.toggle_pin_process
        )
        # pack() automatically places the widget (pin_button) inside the tk_window, stacking it from top to bottom.
        # pady adds padding to the top, and bottom of the widget.
        self.pin_button.pack(pady=10)

        self.unpin_button = tk.Button(
            tk_window, text="Unpin Window", command=self.unpin_window
        )
        self.unpin_button.pack(pady=10)

        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Ensures all pinned windows are unpinned when the application exits.
        """

        # Unpin all pinned windows
        for window_handle in self.pinned_windows:
            try:
                self.remove_pin(window_handle)
                self.window_z_index(window_handle, win32con.HWND_NOTOPMOST)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to cleanup window: {str(e)}")

    def get_window_handle_from_cursor(self):
        cursor_position = win32gui.GetCursorPos()
        # WindowFromPoint gets the handle (a unique identifier) of the window located ath the cursor_position.
        return win32gui.WindowFromPoint(cursor_position)

    def get_window_handle_root(self):
        window_handle = self.get_window_handle_from_cursor()
        # win32con.GA_ROOT tells GetAncestor() to return the top-level or root window in the hierarchy of the given window_handle
        # When you click a part of a window, such as the main body, the window handle returned by functions like WindowFromPoint might refer to a sub-component or child window rather than the root (top-level) window.
        return win32gui.GetAncestor(window_handle, win32con.GA_ROOT)

    def is_valid_window(self, root_window_handle):
        selected_window_title = win32gui.GetWindowText(root_window_handle)
        return (
            True if selected_window_title and selected_window_title.strip() else False
        )

    def pin_window(self):
        """
        Pins the window that was clicked.
        """

        if not self.is_pinning:
            return

        self.stop_pin_process()

        root_window_handle = self.get_window_handle_root()

        # winfo_id() returns the window handle of the widget it's called on.
        if root_window_handle and root_window_handle != self.tk_window.winfo_id():
            try:
                if self.is_valid_window(root_window_handle):
                    # HWND_TOPMOST: Makes root_window_handle window stay on top of all other windows, even when it loses focus.
                    self.window_z_index(root_window_handle, win32con.HWND_TOPMOST)
                    self.pinned_windows.append(root_window_handle)

                    pushpin = PushPinIcon(root_window_handle)
                    self.pushpin_root_window_handle[root_window_handle] = pushpin
                else:
                    messagebox.showwarning("Error", "No valid window selected!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to pin window: {str(e)}")
        else:
            messagebox.showwarning("Error", "Please select a window other than this.")

    def remove_pin(self, pushpin_root_window_handle):
        if pushpin_root_window_handle in self.pushpin_root_window_handle:
            self.pushpin_root_window_handle[
                pushpin_root_window_handle
            ].pushpin_window.destroy()

            del self.pushpin_root_window_handle[pushpin_root_window_handle]

            self.window_z_index(pushpin_root_window_handle, win32con.HWND_NOTOPMOST)

    def run_mouse_hook(self):
        """
        Runs a mouse hook to capture left-click events for selecting windows to pin.
        """

        # callback_function sets up a bridge for Windows to talk to Python using low_level_mouse_handler() whenever a mouse event occurs.
        # event_status: Is an integer that indicates the type or status of the hook event, if non-negative, it means the hook should process the event. Negative value is for a mouse event that doesn't fit the conditions interested it.
        # event_type: Specifies the type of mouse event that triggered the hook.
        # event_info: A pointer to additional information about the mouse event, it can point to a structure containing details like the X and Y coordinates of the mouse events.
        def low_level_mouse_handler(event_status, event_type, event_info=None):
            if event_status >= 0 and event_type == win32con.WM_LBUTTONDOWN:
                # If milliseconds is 0 in after(), the callback function will be scheduled to run as soon as possible, but it will still be placed in the Tkinter event queue.
                self.tk_window.after(0, self.pin_window)
            # low_level_mouse_handler processes the event, does its own work (calls self.root.after()), and then lets the system continue processing the event, passing it to the next handler in the hook chain.
            # First Parameter: Indicates the next hook to call, by passing None, you're indicating that no specific hook is being referenced and the mouse click should continue its default job.
            return ctypes.windll.user32.CallNextHookEx(
                None, event_status, event_type, event_info
            )

        # WINFUNCTYPE must match the low_level_mouse_handler function's signature precisely, this matching is essential because callback_function tells Windows how the callback function is structured in terms of the parameter types and return type.
        # First Argument: Specifies the return type of the function.
        # Second, Third, Fourth Argument: Correspond to event_status, event_type, and event_info in low_level_mouse_handler().
        callback_function = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
        )
        # pointer is now a function pointer that will be passed to SetWindowsHookExA. The system expects a function pointer when setting up a hook procedure, which will be called whenever the specified event happens.
        pointer = callback_function(low_level_mouse_handler)
        # First Parameter: The value 14 corresponds to WH_MOUSE_LL, which stands for a low-level mouse hook.
        # Third Parameter: This is the module handle, None means the hook procedure is in the current module, meaning the python program itself is handling the events.
        # Fourth Parameter: This is the thread ID, a value of 0 means the hook is installed globally for all threads. It ensures that the mouse events are captured system-wide, not just in the current thread.
        self.hook = ctypes.windll.user32.SetWindowsHookExA(14, pointer, None, 0)

        # MSG object is used by the Windows API to store message information, holds details about messages sent to the application's message queue.
        msg = ctypes.wintypes.MSG()
        # GetMessageW(): Retrieves the next message from the application's message queue, storing the details in the msg object. Returns a non-zero value when a message other than WM_QUIT is retrieved.
        # None: Specifies that we want messages from all windows owned by the application
        # 0, 0: These two zero values mean we're interested in all types of messages (by setting the minimum and maximum message values to 0).
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            # DispatchMessageW takes the message that GetMessageW retrieved and directs it to the window or system component it's intended for to be handled.
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        ctypes.windll.user32.UnhookWindowsHookEx(self.hook)

    def start_mouse_hook(self):
        """
        Starts the mouse hook in a separate thread.
        """

        # if statement is intended to ensure that only one thread is running the run_mouse_hook() at any given time.
        if self.hook_thread is None or not self.hook_thread.is_alive():
            # Creates new thread and tells the thread to execute run_mouse_hook() when it starts.
            self.hook_thread = threading.Thread(target=self.run_mouse_hook)
            # Starts thread, which will begin executing concurrently with the main program.
            self.hook_thread.start()

    def start_pin_process(self):
        """
        Activates the pinning mode by enabling the mouse hook.
        """

        self.is_pinning = True
        self.pin_button.config(text="Cancel Pinning")
        self.start_mouse_hook()

    def stop_mouse_hook(self):
        """
        Stops the mouse hook and cleans up the thread.
        """

        if self.hook:
            # PostThreadMessageW: Posts a message to the message queue of a specific thread (identified by its thread ID).
            # hook_thread.ident: Gets the unique ID of the thread that is running the mouse hook.
            # WM_QUIT: Windows message that signals the thread to exit its message loop when the thread retrieves the message from the queue.
            # 0,0: Additional message parameters (event_type and event_info), which are unused in the case of WM_QUIT but still required in the function definition.
            ctypes.windll.user32.PostThreadMessageW(
                self.hook_thread.ident, win32con.WM_QUIT, 0, 0
            )
            # Waits for the thread to finish before moving on with the rest of the code.
            self.hook_thread.join()
            self.hook = None

    def stop_pin_process(self):
        """
        Deactivates the pinning mode by disabling the mouse hook.
        """

        self.is_pinning = False
        self.pin_button.config(text="Pin Window")
        self.stop_mouse_hook()

    def toggle_pin_process(self):
        """
        Toggles the pinning mode on or off based on the current state.
        """

        if not self.is_pinning:
            self.start_pin_process()
        else:
            self.stop_pin_process()

    def unpin_window(self):
        """
        Unpins the most recently pinned window.
        """

        if self.pinned_windows:
            try:
                window_handle = self.pinned_windows.pop()
                self.remove_pin(self, window_handle)
                # NOTOPMOST: Specifies that window_handle should no longer be a topmost window but instead be placed below all other topmost windows.
                self.window_z_index(window_handle, win32con.HWND_NOTOPMOST)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to unpin window: {str(e)}")
        else:
            messagebox.showwarning("Error", "No windows are pinned!")

    @staticmethod
    def window_z_index(self, window_handle, is_topmost):
        # 0,0,0,0: These represent the x and y positions and width and height of the root_window_handle window.
        # SWP_NOMOVE: This flag prevents the window from being moved, it ignores x and y values.
        # SWP_NOSIZE: This flag prevents the window from being resized, it ignores width and height values.
        # |: The bitwise OR (|) is used to combine ttwo bit flags into a single value. This allows both flags to be set simultaneously. This is common patterns in low-level Windows programming.
        win32gui.SetWindowPos(
            window_handle,
            is_topmost,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
        )


if __name__ == "__main__":
    # Initializes a blank window where you can add widgets (like buttons, labels, etc.).
    root = tk.Tk()
    app = PinWindow(root)
    # Keeps the application running and continuously checks for events (button clicks, mouse movements, keyboard input, etc.) to respond to them.
    root.mainloop()
