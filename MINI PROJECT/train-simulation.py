import threading
import time
import random
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.figure as mplfig
from datetime import datetime

def bankers_algorithm():
    available = [1] * NUM_TRACKS  
    max_claim = [[1, 1] for _ in range(NUM_TRAINS)]  
    allocated = [[0, 0] for _ in range(NUM_TRAINS)]  

    safe_sequence = []
    finished = [False] * NUM_TRAINS
    while len(safe_sequence) < NUM_TRAINS:
        allocated_any = False
        for i in range(NUM_TRAINS):
            if not finished[i] and all(max_claim[i][j] - allocated[i][j] <= available[j] for j in range(2)):
                safe_sequence.append(i)
                for j in range(2):
                    available[j] += allocated[i][j]
                finished[i] = True
                allocated_any = True
                break
        if not allocated_any:
            return False  
    return True  

root = tk.Tk()
root.withdraw()
NUM_TRAINS = simpledialog.askinteger("Input", "Enter the number of trains:")

if NUM_TRAINS is None or NUM_TRAINS <= 0:
    exit("Invalid input or user canceled input.")

train_names = []
for i in range(NUM_TRAINS):
    name = simpledialog.askstring("Train Name", f"Enter name for Train {i}:")
    if not name:
        name = f"Train_{i}"
    train_names.append(name)

NUM_TRACKS = NUM_TRAINS

if not bankers_algorithm():
    messagebox.showerror("Deadlock Detected", "The track allocation may lead to deadlock. Exiting...")
    exit()
else:
    messagebox.showinfo("Deadlock Check", "Deadlock checked: No deadlock detected.")

track_locks = [threading.Semaphore(1) for _ in range(NUM_TRACKS)]
mutex = threading.Lock()
root.deiconify()
root.title("Railway Track Allocation Simulation")
canvas_width = 800
canvas_height = 100 + (NUM_TRAINS * 60)
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.pack()

log_window = tk.Toplevel(root)
log_window.title("Train Status Log")
log_window.geometry("400x300")
log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, height=15, width=50)
log_text.pack()

def log_message(message):
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)

priorities = {}
waiting_times = [0] * NUM_TRAINS
moving_times = [0] * NUM_TRAINS

def set_priorities():
    global priorities
    priority_window = tk.Toplevel(root)
    priority_window.title("Set Train Priorities")
    priority_window.geometry("400x300")

    entries = []
    for i in range(NUM_TRAINS):
        tk.Label(priority_window, text=f"{train_names[i]}:").grid(row=i, column=0)
        entry = tk.Entry(priority_window)
        entry.grid(row=i, column=1)
        entry.insert(tk.END, str(random.randint(1, 10)))
        entries.append(entry)

    def apply_priorities():
        global priorities
        priorities = {i: int(entries[i].get()) for i in range(NUM_TRAINS)}
        log_message("\u2705 Priorities updated successfully!")
        priority_window.destroy()

    tk.Button(priority_window, text="Apply", command=apply_priorities).grid(row=NUM_TRAINS, columnspan=2)

tk.Button(root, text="Set Priorities", command=set_priorities).pack()

def draw_track(y_pos):
    canvas.create_line(50, y_pos + 10, canvas_width - 50, y_pos + 10, width=3, fill="black")

def draw_train(x, y, train_id, color):
    return canvas.create_text(x, y, text=f"\U0001F686 {train_names[train_id]} (Priority {priorities.get(train_id, 1)})", font=("Arial", 18), fill=color)

def move_train(train_id, start_x, end_x, y_pos, color):
    start_time = time.time()
    train = draw_train(start_x, y_pos, train_id, color)
    for x in range(start_x, end_x, 5):
        if not canvas.winfo_exists():
            return  
        canvas.move(train, 5, 0)
        canvas.update()
        time.sleep(0.05)
    canvas.delete(train)
    end_time = time.time()
    moving_times[train_id] = end_time - start_time
    log_message(f"\U0001F686 {train_names[train_id]} took {round(end_time - start_time, 2)} seconds to move.")

def train_routine(train_id):
    left_track = train_id
    right_track = (train_id + 1) % NUM_TRACKS
    y_pos = 50 + train_id * 60
    draw_track(y_pos)

    while True:
        wait_start = time.time()
        log_message(f"\U0001F686 {train_names[train_id]} (Priority {priorities.get(train_id, 1)}) is waiting for track {left_track} and {right_track}...")
        waiting_train = draw_train(50, y_pos, train_id, "red")
        time.sleep(random.uniform(0.5, 1.5))
        wait_end = time.time()
        waiting_times[train_id] = wait_end - wait_start

        with mutex:
            track_locks[left_track].acquire()
            track_locks[right_track].acquire()

        if canvas.winfo_exists():
            canvas.delete(waiting_train)
        log_message(f"\U0001F686 {train_names[train_id]} waited for {round(wait_end - wait_start, 2)} seconds.")
        move_train(train_id, 50, canvas_width - 50, y_pos, "green")

        track_locks[left_track].release()
        track_locks[right_track].release()
        time.sleep(random.uniform(1, 2))

def show_efficiency_report():
    if not any(waiting_times) and not any(moving_times):
        messagebox.showwarning("Warning", "No data available yet!")
        return
    total_waiting = sum(waiting_times)
    total_moving = sum(moving_times)
    avg_waiting = total_waiting / NUM_TRAINS
    avg_moving = total_moving / NUM_TRAINS

    report = f"Efficiency Report:\n\n" \
             f"Total Waiting Time: {total_waiting:.2f} s\n" \
             f"Total Moving Time: {total_moving:.2f} s\n" \
             f"Average Waiting Time per Train: {avg_waiting:.2f} s\n" \
             f"Average Moving Time per Train: {avg_moving:.2f} s"

    messagebox.showinfo("Efficiency Report", report)

tk.Button(root, text="Show Efficiency Report", command=show_efficiency_report).pack()

# -------------------- \uD83D\uDD18 Button-Triggered Live Graph --------------------
graph_window = None
def show_efficiency_graph():
    global graph_window
    if graph_window is not None and graph_window.winfo_exists():
        graph_window.lift()
        return

    graph_window = tk.Toplevel(root)
    graph_window.title("Live Efficiency Graph")
    fig = mplfig.Figure(figsize=(8, 5))
    ax = fig.add_subplot(111)
    canvas_plot = FigureCanvasTkAgg(fig, master=graph_window)
    canvas_plot.get_tk_widget().pack()

    def update_graph():
        if not graph_window.winfo_exists():
            return
        if any(waiting_times) or any(moving_times):
            ax.clear()
            ax.plot(range(NUM_TRAINS), waiting_times, label='Waiting Time', color='red', marker='o')
            ax.plot(range(NUM_TRAINS), moving_times, label='Moving Time', color='green', marker='o')
            ax.set_title("Live Efficiency Chart (Auto-updated)")
            ax.set_xlabel("Train Number")
            ax.set_ylabel("Time (s)")
            ax.legend()
            ax.grid(True)
            canvas_plot.draw()
        graph_window.after(2000, update_graph)

    update_graph()

tk.Button(root, text="Show Efficiency Graph", command=show_efficiency_graph).pack()
# ------------------------------------------------------------------------

train_threads = []
for i in range(NUM_TRAINS):
    thread = threading.Thread(target=train_routine, args=(i,), daemon=True)
    train_threads.append(thread)
    thread.start()

root.mainloop()
