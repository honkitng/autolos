import os
import sys
import pyautogui

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from screeninfo import get_monitors


class Screen:
    def __init__(self, message):
        self.root = tk.Tk()

        monitors = get_monitors()
        width = 0
        height = 0
        for monitor in monitors:
            width += monitor.width
            height += monitor.height

        self.root.geometry(f"{width}x{height}+0+0")
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.5)
        self.root.update_idletasks()
        self.root.resizable(False, False)
        self.root.grab_set()
        self.root.overrideredirect(True)
        self.root.focus_force()

        self.root.bind("<Escape>", self.escape_press)

        self.root.title("Autolos - Screen")
        self.root.config(bg="#ffffff")

        self.instructions = tk.Toplevel(self.root)
        self.instructions.geometry(f"{width}x45+0+0")
        self.instructions.attributes("-topmost", True)
        self.root.update_idletasks()
        self.instructions.resizable(False, False)
        self.instructions.overrideredirect(True)

        self.instructions.config(bg="#496FF5")
        self.instructions.title("Autolos - Instructions")

        self.instructions_label = tk.Label(self.instructions, font=("Arial", 20), bg="#496FF5", text=message)
        self.instructions_label.pack(pady=10)

        self.canvas = tk.Canvas(self.root, width=self.root.winfo_width(), height=self.root.winfo_height(), bg="#ffffff")
        self.canvas.pack()

    def quit_screen(self, _):
        self.instructions.destroy()
        self.root.destroy()
        self.root.quit()

    def escape_press(self, _):
        self.root.destroy()
        self.root.quit()
        sys.exit(1)


class TrackWindow(Screen):
    def __init__(self, message):
        super().__init__(message)

        self.box_position = [0, 0, 100, 100]
        self.canvas_position = [(0, 0), (100, 100)]

        self.root.bind("<ButtonPress-1>", self.start_box)
        self.root.bind("<B1-Motion>", self.drag_box)
        self.root.bind("<ButtonRelease-1>", self.end_box)

        self.root.mainloop()

    def start_box(self, event):
        self.box_position[0] = pyautogui.position().x
        self.box_position[1] = pyautogui.position().y

        self.canvas_position = [(event.x, event.y), (event.x, event.y)]

        self.instructions.attributes("-topmost", True)
        self.root.unbind("<Return>")
        self.instructions.unbind("<Return>")

    def drag_box(self, event):
        self.canvas_position[1] = (event.x, event.y)

        self.canvas.delete("all")
        self.canvas.create_rectangle(*self.canvas_position, fill="#000000")

    def end_box(self, _):
        self.box_position[2] = abs(pyautogui.position().x - self.box_position[0])
        self.box_position[3] = abs(pyautogui.position().y - self.box_position[1])
        self.box_position[0] = min(pyautogui.position().x, self.box_position[0])
        self.box_position[1] = min(pyautogui.position().y, self.box_position[1])

        self.root.bind("<Return>", self.quit_screen)
        self.instructions.bind("<Return>", self.quit_screen)


class CursorPosition(Screen):
    def __init__(self, message):
        super().__init__(message)

        self.cursor_pos = (0, 0)
        self.root.bind("<Button-1>", self.get_cursor)

        self.root.mainloop()

    def get_cursor(self, event):
        self.cursor_pos = (pyautogui.position().x, pyautogui.position().y)

        self.canvas.delete("all")
        self.canvas.create_line(event.x, event.y-5, event.x, event.y+5, fill="red", width=2)
        self.canvas.create_line(event.x-5, event.y, event.x+5, event.y, fill="red", width=2)

        self.instructions.attributes("-topmost", True)
        self.root.bind("<Return>", self.quit_screen)
        self.instructions.bind("<Return>", self.quit_screen)


class LamellaePositions(Screen):
    def __init__(self, message):
        super().__init__(message)

        self.lamellae_positions = []
        self.cross_positions = []

        self.root.bind("<Button-1>", self.get_lamella)
        self.root.bind("<Return>", self.return_press)
        self.instructions.bind("<Return>", self.return_press)
        self.root.bind("<Control-z>", self.undo_lamella)
        self.instructions.bind("<Control-z>", self.undo_lamella)

        self.root.mainloop()

    def get_lamella(self, event):
        self.lamellae_positions.append((pyautogui.position().x, pyautogui.position().y))

        cross_h = self.canvas.create_line(event.x, event.y-5, event.x, event.y+5, fill="red", width=2)
        cross_v = self.canvas.create_line(event.x-5, event.y, event.x+5, event.y, fill="red", width=2)

        self.cross_positions.append((cross_h, cross_v))

        self.instructions.attributes("-topmost", True)

    def undo_lamella(self, _):
        if len(self.lamellae_positions) > 0:
            self.canvas.delete(*self.cross_positions[-1])
            self.cross_positions = self.cross_positions[:-1]
            self.lamellae_positions = self.lamellae_positions[:-1]

    def return_press(self, event):
        if len(self.lamellae_positions) > 0:
            self.quit_screen(event)


class ParameterWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.resizable(False, False)
        self.root.title("Autolos - Parameter Setup")

        self.validate_float = self.root.register(float_check)

        self.directory = tk.StringVar()
        self.time = tk.DoubleVar()
        self.voltage = tk.StringVar()
        self.current_imaging = tk.StringVar()
        self.current_milling = tk.StringVar()

        self.save_dir = ""
        self.run_time = 0
        self.voltage_idx = 0
        self.current_imaging_idx = 0
        self.current_milling_idx = 0
        self.ok = False

        self.voltage_current = {
            "2.00 kV": ("0.20 pA", "0.70 pA", "2.1 pA", "4.3 pA", "8.9 pA", "27 pA", "43 pA", "86 pA", "0.27 nA",
                        "0.43 nA", "0.61 nA", "1.3 nA", "2.7 nA", "4.3 nA", "7.1 nA"),
            "5.00 kV": ("0.30 pA", "1.3 pA", "3.9 pA", "7.7 pA", "16 pA", "48 pA", "77 pA", "0.15 nA", "0.48 nA",
                        "0.77 nA", "1.1 nA", "2.3 nA", "4.8 nA", "7.7 nA", "13 nA"),
            "8.00 kV": ("0.5 pA", "2.0 pA", "6.0 pA", "12 pA", "25 pA", "75 pA", "0.12 nA", "0.24 nA", "0.75 nA",
                        "1.2 nA", "1.7 nA", "3.5 nA", "7.5 nA", "12 nA", "20 nA"),
            "16.00 kV": ("1.0 pA", "4.0 pA", "11 pA", "23 pA", "50 pA", "0.15 nA", "0.25 nA", "0.50 nA", "1.5 nA",
                         "2.5 nA", "3.6 nA", "7.5 nA", "15 nA", "25 nA", "42 nA"),
            "30.00 kV": ("1.5 pA", "10 pA", "30 pA", "50 pA", "0.10 nA", "0.30 nA", "0.50 nA", "1.0 nA", "3.0 nA",
                         "5.0 nA", "7.0 nA", "15 nA", "30 nA", "50 nA", "65 nA")
        }

        self.time.set(0)
        self.voltage.set("30.00 kV")

        self.frame_parameters = tk.Frame(self.root)
        self.frame_parameters.grid(row=0, column=0)

        self.label_directory = tk.Label(self.frame_parameters, text="Save Directory:")
        self.label_directory.grid(row=0, column=0)
        self.input_directory = tk.Entry(self.frame_parameters, textvariable=self.directory)
        self.input_directory.grid(row=0, column=1)
        self.button_directory = tk.Button(self.frame_parameters, text="Browse", command=self.browse)
        self.button_directory.grid(row=0, column=2)

        self.label_time = tk.Label(self.frame_parameters, text="Time (min):")
        self.label_time.grid(row=1, column=0)
        self.input_time = tk.Entry(self.frame_parameters, textvariable=self.time, width=15, validate="key",
                                   validatecommand=(self.validate_float, "%P"))
        self.input_time.grid(row=1, column=1)

        self.label_voltage = tk.Label(self.frame_parameters, text="Voltage:")
        self.label_voltage.grid(row=2, column=0)
        self.input_voltage = tk.OptionMenu(self.frame_parameters, self.voltage, *self.voltage_current.keys(),
                                           command=self.set_voltage)
        self.input_voltage.config(width=10)
        self.input_voltage.grid(row=2, column=1)
        self.label_current_imaging = tk.Label(self.frame_parameters, text="Imaging Current:")
        self.label_current_imaging.grid(row=3, column=0)
        self.input_current_imaging = tk.OptionMenu(self.frame_parameters, self.current_imaging, "")
        self.input_current_imaging.config(width=10)
        self.input_current_imaging.grid(row=3, column=1)
        self.label_current_milling = tk.Label(self.frame_parameters, text="Milling Current:")
        self.label_current_milling.grid(row=4, column=0)
        self.input_current_milling = tk.OptionMenu(self.frame_parameters, self.current_milling, "")
        self.input_current_milling.config(width=10)
        self.input_current_milling.grid(row=4, column=1)

        self.set_voltage()

        self.frame_buttons = tk.Frame(self.root)
        self.frame_buttons.grid(row=1, column=0)
        self.button_start = tk.Button(self.frame_buttons, text="Start", command=self.start_press)
        self.button_start.grid(row=0, column=0)

        self.root.mainloop()

    def browse(self):
        directory = filedialog.askdirectory(title="Save directory")
        if directory:
            self.directory.set(directory)

    def set_voltage(self, _=None):
        menus = [self.input_current_imaging["menu"], self.input_current_milling["menu"]]
        voltage = self.voltage.get()
        for i, menu in enumerate(menus):
            menu.delete(0, tk.END)
            for current in self.voltage_current[voltage]:
                if i == 0:
                    menu.add_command(label=current, command=lambda value=current: self.current_imaging.set(value))
                else:
                    menu.add_command(label=current, command=lambda value=current: self.current_milling.set(value))
        self.current_imaging.set(self.voltage_current[voltage][0])
        self.current_milling.set(self.voltage_current[voltage][0])

    def start_press(self):
        self.save_dir = self.directory.get()

        self.run_time = self.time.get()
        if self.save_dir and os.path.exists(self.save_dir) and self.run_time:
            voltage = self.voltage.get()
            current_imaging = self.current_imaging.get()
            current_milling = self.current_milling.get()

            self.voltage_idx = list(self.voltage_current.keys()).index(voltage)
            self.current_imaging_idx = self.voltage_current[voltage].index(current_imaging)
            self.current_milling_idx = self.voltage_current[voltage].index(current_milling)

            self.ok = True

            self.root.destroy()
            self.root.quit()
            return
        messagebox.showerror(title="Error", message="Please enter a valid save directory & run time")
        return


def float_check(variable):
    try:
        if variable == "" or variable == ".":
            return True
        else:
            float(variable)
            return True
    except ValueError:
        return False
