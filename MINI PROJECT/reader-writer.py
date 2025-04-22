import tkinter as tk
import random
from tkinter import messagebox, simpledialog, filedialog

# Simulation settings
ICON_RADIUS = 50
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 800

# Timing (in milliseconds)
WRITER_ACTIVE_TIME = 3000
WRITER_IDLE_TIME = 5000
READER_ACTIVE_TIME = 4000
READER_CHECK_INTERVAL = 500

# Offsets for captions relative to the icons
CAPTION_OFFSET_Y = 70
PEN_OFFSET_X = 30

# Fonts
WRITER_ACTIVE_FONT = ("Helvetica", 40)
WRITER_INACTIVE_FONT = ("Helvetica", 24)
READER_ACTIVE_FONT = ("Helvetica", 36)
READER_INACTIVE_FONT = ("Helvetica", 24)
CAPTION_FONT = ("Helvetica", 16)
LOG_FONT = ("Courier", 12)

class Writer:
    def __init__(self, canvas, x, y, name, priority):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.name = name
        self.priority = priority
        self.active = False
        self.icon = canvas.create_oval(x - ICON_RADIUS, y - ICON_RADIUS,
                                       x + ICON_RADIUS, y + ICON_RADIUS,
                                       fill=self.get_color(), outline="black", width=2)
        self.label = canvas.create_text(x, y, text=self.name, fill="white", font=WRITER_INACTIVE_FONT)
        self.caption = canvas.create_text(x, y + CAPTION_OFFSET_Y, text=f"Priority: {self.priority}", fill="black", font=CAPTION_FONT)

    def get_color(self):
        return "#ff6666" if self.active else "#999999"

    def set_active(self, active):
        self.active = active
        self.render()

    def render(self):
        self.canvas.itemconfig(self.icon, fill=self.get_color())
        if self.active:
            self.canvas.itemconfig(self.label, text="✍️", font=WRITER_ACTIVE_FONT)
            self.canvas.coords(self.label, self.x + PEN_OFFSET_X, self.y)
            self.canvas.itemconfig(self.caption, text=f"Writing (P: {self.priority})")
        else:
            self.canvas.itemconfig(self.label, text=self.name, font=WRITER_INACTIVE_FONT)
            self.canvas.coords(self.label, self.x, self.y)
            self.canvas.itemconfig(self.caption, text=f"Priority: {self.priority}")
        self.canvas.coords(self.caption, self.x, self.y + CAPTION_OFFSET_Y)

class Reader:
    def __init__(self, canvas, x, y, name, priority, sim):
        self.canvas = canvas
        self.sim = sim
        self.x = x
        self.y = y
        self.name = name
        self.priority = priority
        self.state = "waiting"
        self.icon = canvas.create_oval(x - ICON_RADIUS, y - ICON_RADIUS, x + ICON_RADIUS, y + ICON_RADIUS,
                                       fill=self.get_color(), outline="black", width=2)
        self.label = canvas.create_text(x, y, text=self.name, fill="white", font=READER_INACTIVE_FONT)
        self.caption = canvas.create_text(x, y + CAPTION_OFFSET_Y, text=f"Priority: {self.priority}", fill="black", font=CAPTION_FONT)

    def get_color(self):
        return "#66cc66" if self.state == "reading" else "#999999"

    def update_state(self, writer_active):
        if not writer_active and self.sim.mode == "reader":
            if self.state != "reading":
                self.sim.active_readers += 1
                self.sim.log(f"{self.name} started reading.")
            self.state = "reading"
        else:
            if self.state == "reading":
                self.sim.active_readers -= 1
                self.sim.log(f"{self.name} stopped reading.")
            self.state = "waiting"
        self.render()

    def render(self):
        self.canvas.itemconfig(self.icon, fill=self.get_color())
        new_text = "📖" if self.state == "reading" else self.name
        new_font = READER_ACTIVE_FONT if self.state == "reading" else READER_INACTIVE_FONT
        self.canvas.itemconfig(self.label, text=new_text, font=new_font)
        caption_text = "Reading" if self.state == "reading" else f"Priority: {self.priority}"
        self.canvas.itemconfig(self.caption, text=caption_text)
        self.canvas.coords(self.caption, self.x, self.y + CAPTION_OFFSET_Y)

class Simulation:
    def __init__(self, root, num_readers, num_writers, mode):
        self.root = root
        self.num_readers = num_readers
        self.num_writers = num_writers
        self.mode = mode.strip().lower()

        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT - 100, bg="white")
        self.canvas.pack()

        control_frame = tk.Frame(root)
        control_frame.pack(fill=tk.X)

        self.log_box = tk.Text(root, height=6, font=LOG_FONT, bg="#f0f0f0")
        self.log_box.pack(fill=tk.X)

        tk.Button(control_frame, text="Reset Simulation", command=self.reset_simulation).pack(side=tk.LEFT)
        tk.Button(control_frame, text="Export Log", command=self.export_log).pack(side=tk.LEFT)

        self.readers = []
        self.writers = []
        self.active_readers = 0
        self.current_writer = None
        self.deadlock_reported = False
        self.deadlock_resolved_reported = False

        self.setup_simulation()

    def log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def export_log(self):
        log_data = self.log_box.get("1.0", tk.END)
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if filename:
            with open(filename, "w") as file:
                file.write(log_data)
            messagebox.showinfo("Export Log", f"Log successfully saved to {filename}")

    def reset_simulation(self):
        self.canvas.delete("all")
        self.log_box.delete("1.0", tk.END)
        self.readers.clear()
        self.writers.clear()
        self.active_readers = 0
        self.current_writer = None
        self.deadlock_reported = False
        self.deadlock_resolved_reported = False
        self.num_readers = simpledialog.askinteger("Input", "Enter number of readers:", minvalue=1, maxvalue=10)
        self.num_writers = simpledialog.askinteger("Input", "Enter number of writers:", minvalue=1, maxvalue=5)
        self.mode = simpledialog.askstring("Priority Mode", "Enter mode (reader or writer priority):", initialvalue="reader")
        self.setup_simulation()

    def setup_writers(self, num_writers):
        start_x, y = 100, CANVAS_HEIGHT // 2
        spacing = 140
        for i in range(num_writers):
            x = start_x + (i * spacing)
            name = f"W{i+1}"
            priority = random.randint(1, 10)
            self.log(f"{name} assigned priority {priority}")
            writer = Writer(self.canvas, x, y, name, priority)
            self.writers.append(writer)

    def setup_readers(self, num_readers):
        start_x, y = 100, CANVAS_HEIGHT // 4
        spacing = 140
        for i in range(num_readers):
            x = start_x + (i * spacing)
            name = f"R{i+1}"
            priority = random.randint(1, 10)
            self.log(f"{name} assigned priority {priority}")
            reader = Reader(self.canvas, x, y, name, priority, self)
            self.readers.append(reader)

    def resolve_initial_deadlock(self):
        self.activate_writer()
        self.log("Initial deadlock avoided by activating a writer.")
        messagebox.showinfo("Initial Deadlock Avoided", "Deadlock was detected at start and avoided by activating a writer.")

    def update_simulation(self):
        if self.mode == "writer":
            if self.current_writer is None:
                self.activate_writer()
        else:
            if self.current_writer is None:
                self.activate_readers()

        for reader in self.readers:
            reader.update_state(writer_active=(self.current_writer is not None))
        self.check_deadlock()
        self.root.after(READER_CHECK_INTERVAL, self.update_simulation)

    def activate_writer(self):
        if self.writers and self.active_readers == 0:
            if self.current_writer:
                self.current_writer.set_active(False)
            self.current_writer = sorted(self.writers, key=lambda w: w.priority)[0]
            self.current_writer.set_active(True)
            self.log(f"Writer activated: {self.current_writer.name}")
            self.root.after(WRITER_ACTIVE_TIME, self.deactivate_writer)

    def deactivate_writer(self):
        if self.current_writer:
            self.log(f"Writer deactivated: {self.current_writer.name}")
            self.current_writer.set_active(False)
            self.current_writer = None
            self.activate_readers()
            self.root.after(READER_ACTIVE_TIME, self.deactivate_readers)

    def activate_readers(self):
        sorted_readers = sorted(self.readers, key=lambda r: r.priority)
        for reader in sorted_readers:
            reader.state = "reading"
            reader.render()
        self.active_readers = len(self.readers)
        self.log("Readers activated for reading.")

    def deactivate_readers(self):
        for reader in self.readers:
            if reader.state == "reading":
                reader.state = "waiting"
                self.active_readers -= 1
                self.log(f"{reader.name} stopped reading.")
                reader.render()
        self.activate_writer()

    def check_deadlock(self):
        if self.active_readers == 0 and self.current_writer is None:
            if not self.deadlock_reported:
                self.deadlock_reported = True
                self.log("Deadlock detected. Resolving...")
                messagebox.showerror("Deadlock Detected", "All readers are waiting and no writer is active. Deadlock occurred! Resolving...")
                self.resolve_deadlock()
        else:
            if self.deadlock_reported and not self.deadlock_resolved_reported:
                self.deadlock_resolved_reported = True
                self.log("Deadlock resolved.")
                messagebox.showinfo("Deadlock Resolved", "Deadlock has been resolved. Simulation continues.")
            self.deadlock_reported = False

    def resolve_deadlock(self):
        self.activate_writer()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    mode = simpledialog.askstring("Priority Mode", "Enter mode (reader or writer priority):", initialvalue="reader")
    if not mode:
        messagebox.showerror("Input Error", "Simulation mode is required.")
        root.destroy()
        exit()

    num_readers = simpledialog.askinteger("Input", "Enter number of readers:", minvalue=1, maxvalue=10)
    if num_readers is None:
        messagebox.showerror("Input Error", "Number of readers is required.")
        root.destroy()
        exit()

    num_writers = simpledialog.askinteger("Input", "Enter number of writers:", minvalue=1, maxvalue=5)
    if num_writers is None:
        messagebox.showerror("Input Error", "Number of writers is required.")
        root.destroy()
        exit()

    root.deiconify()
    root.title("Reader-Writer Visualization")
    sim = Simulation(root, num_readers, num_writers, mode)
    root.mainloop()