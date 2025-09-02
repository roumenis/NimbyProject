import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from datetime import datetime, timedelta


class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Turn Schedule Creator - Basic Version")

        # Data
        self.data = None
        self.schedules = None
        self.min_turnaround = timedelta(minutes=2)  # minimum turnaround time

        # Buttons
        btn_load = tk.Button(root, text="Load Schedule (CSV)", command=self.load_csv)
        btn_load.pack(pady=5)

        btn_create = tk.Button(root, text="Create Schedules", command=self.create_schedules)
        btn_create.pack(pady=5)

        btn_save = tk.Button(root, text="Save to Excel", command=self.save_excel)
        btn_save.pack(pady=5)

        # Table to show data
        self.tree = ttk.Treeview(root)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def load_csv(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.data = pd.read_csv(file_path)

            # Convert departure and arrival times to datetime.time
            self.data["departure_time"] = pd.to_datetime(self.data["departure_time"], format="%H:%M")
            self.data["arrival_time"] = pd.to_datetime(self.data["arrival_time"], format="%H:%M")

            # Count turnaround time (minutes)
            turnaround_times = [0]
            for i in range(1, len(self.data)):
                delta = (self.data.loc[i, "departure_time"] - self.data.loc[i - 1, "arrival_time"]).total_seconds() / 60
                turnaround_times.append(int(delta)) # int delta -> 12,5 -> 12

            self.data["turnaround_time"] = turnaround_times

            # Convert back to HH:MM format for display
            self.data["departure_time"] = self.data["departure_time"].dt.strftime("%H:%M")
            self.data["arrival_time"] = self.data["arrival_time"].dt.strftime("%H:%M")

            self.show_data(self.data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def show_data(self, dataframe):
        # Clear table
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(dataframe.columns)
        self.tree["show"] = "headings"

        for col in dataframe.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        for _, row in dataframe.iterrows():
            self.tree.insert("", tk.END, values=list(row))

    def create_schedules(self):
        if self.data is None:
            messagebox.showwarning("Warning", "Please load a schedule first!")
            return

        trips = self.data.sort_values("departure_time").reset_index(drop=True)

        schedules = []
        for _, trip in trips.iterrows():
            dep_time = datetime.combine(datetime.today(), trip["departure_time"])
            arr_time = datetime.combine(datetime.today(), trip["arrival_time"])
            origin = trip["origin"]
            destination = trip["destination"]

            assigned = False
            for schedule in schedules:
                last_trip = schedule[-1]
                last_arrival = datetime.combine(datetime.today(), last_trip["arrival_time"])
                schedule_start = datetime.combine(datetime.today(), schedule[0]["departure_time"])

                duty_time = last_arrival - schedule_start
                gap = dep_time - last_arrival

                # If gap >= 10 minutes, reset duty time
                if gap >= timedelta(minutes=10):
                    schedule_start = dep_time
                    duty_time = timedelta(0)

                if (
                    last_trip["destination"] == origin
                    and dep_time >= last_arrival + self.min_turnaround
                    and duty_time <= timedelta(hours=4, minutes=30)
                ):
                    schedule.append({
                        "departure_time": trip["departure_time"],
                        "arrival_time": trip["arrival_time"],
                        "origin": origin,
                        "destination": destination
                    })
                    assigned = True
                    break

            if not assigned:
                schedules.append([{
                    "departure_time": trip["departure_time"],
                    "arrival_time": trip["arrival_time"],
                    "origin": origin,
                    "destination": destination
                }])

        # Save schedules
        schedule_list = []
        for i, schedule in enumerate(schedules, start=1):
            trips_text = "; ".join(
                f"{t['origin']} {t['departure_time'].strftime('%H:%M')} → {t['destination']}" for t in schedule
            )
            schedule_list.append({"Schedule": i, "Trips": trips_text})

        self.schedules = pd.DataFrame(schedule_list)
        self.show_data(self.schedules)

    def save_excel(self):
        if self.schedules is None:
            messagebox.showwarning("Warning", "Please create schedules first!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            self.schedules.to_excel(file_path, index=False)
            messagebox.showinfo("Done", f"File saved as:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Excel:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.geometry("1280x720")
    root.mainloop()