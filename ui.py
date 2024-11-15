import tkinter as tk
from environment import Environment
from datetime import datetime

class BuildingInterface:
    def __init__(self, environment: Environment):
        self.env = environment
        self.root = tk.Tk()
        self.root.title("Multi-Agent Emergency Evacuation System")
        self.root.config(background='pink')
    
        # Frame principal
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.config(background='pink')
        self.floor_frames = []
        for i in range(self.env.num_floors):
            frame = tk.Frame(self.main_frame, borderwidth=2, relief='groove')
            frame.grid(row = i // 4, column=i % 4, sticky='nsew')
            tk.Label(frame, text=f"Floor {i}").grid(row=0, column=0, columnspan=self.env.grid_size)
            frame.config(background='white')
            self.floor_frames.append(frame)

        self.grid_labels = []
        for z in range(self.env.num_floors):
            floor_grid = []
            for x in range(self.env.grid_size):
                row = []
                for y in range(self.env.grid_size):
                    label = tk.Label(self.floor_frames[z], text=" ", width=4, height=2, borderwidth=1, relief='solid')
                    label.grid(row=x +1, column=y)
                    label.config(background='white')
                    row.append(label)
                floor_grid.append(row)
            self.grid_labels.append(floor_grid)

        #stats
        self.stats = tk.Frame(self.main_frame)
        self.stats.grid(row=0, column=5, padx=20)
        self.stats.config(background='pink')
        tk.Label(self.stats, text="Stats", width=10).grid(row=0, column=0)

        self.time_label = tk.Label(self.stats, text="Time Passed: 0s", bg='pink')
        self.time_label.grid(row=1, column=0)

        self.saved_label = tk.Label(self.stats, text="Occupants Saved: 0", bg='pink')
        self.saved_label.grid(row=2, column=0)

        self.dead_label = tk.Label(self.stats, text="occupants Dead: 0", bg='pink')
        self.dead_label.grid(row=3, column=0)

        self.occupants_label = tk.Label(self.stats, text=f"Occupants to Evacuate: {self.env.num_occupants}", bg='pink')
        self.occupants_label.grid(row=4, column=0)

        self.is_done_label = tk.Label(self.stats, text= " ", bg='pink', fg='#c154c1', font=("Helvetica", 10, "bold"))
        self.is_done_label.grid(row=5, column=0)

        #legenda
        legenda = tk.Frame(self.main_frame)
        legenda.grid(row=1, column=5, padx=20)
        tk.Label(legenda, text="Legenda", width=10).grid(row=0, column=0)
        legenda.config(background='pink')

        colors = {
            '#ff007f': 'Exit',
            '#c154c1': 'Occupant',
            'pink': 'Window',
            'lightblue': 'Stairs',
            'red': 'Fire'
        }

        row = 1 
        for color, description in colors.items():

            color_circle = tk.Canvas(legenda, width=40, height=40)
            color_circle.grid(row=row, column=0, padx=2, pady=2)
            color_circle.create_oval(5, 5, 35, 35, fill=color, outline=color)

            description_label = tk.Label(legenda, text=description, width=30)
            description_label.grid(row=row, column=1, padx=2, pady=2)
            
            row += 1

    def update_stats(self):
        elapsed_time = datetime.now() - self.env.start_time
        self.time_label.config(text=f"Time Passed: {elapsed_time}")

        self.saved_label.config(text=f"Occupants Saved; {self.env.occupants_saved}")
        self.dead_label.config(text=f"Occupants Dead: {self.env.occupants_dead}")
        to_save =  self.env.num_occupants - self.env.occupants_dead - self.env.occupants_saved
        self.occupants_label.config(text=f"Occupants to Evacuate: {to_save}")
        if to_save == 0:
            self.is_done_label.config(text="All occupants left safely or are unfortunately dead *-*")

        self.root.after(1000, self.update_stats)

    def update_grid(self):
        for z in range(self.env.num_floors):
            grid = self.env.get_grid(z)
            for x in range(len(grid)):
                for y in range(len(grid[0])):
                    value = grid[x][y]
                    label = self.grid_labels[z][x][y]
                    color = "white"
                    if value == 1:
                        label.config(text= "🚪")  # Door
                    elif value == 2:
                        color = 'pink'   # Window
                    elif value == 3:
                        color = 'lightblue'   # Stairs
                    elif value == 4:
                        color = '#c154c1' # Occupant
                    elif value == 5:
                        color = "red"  # Fire
                    elif value == 6:
                        color = '#ff007f' # Exit
                    elif value == 7:
                        color = "blue"    # ER Agent
                    elif value == 8:
                        color = 'lightgray'     #Obstacle
                    label.config(bg=color)
        #look for smoke
        for loc in self.env.smoke_pos:
                x, y, z = loc
                label = self.grid_labels[z][x][y]
                label.config(text="S")
                    
        
                        

        self.main_frame.after(1000, self.update_grid)

    def run(self):
        self.update_grid()
        self.update_stats()
        self.root.mainloop()
        



#####################################################

def start_interface(environment):
    interface = BuildingInterface(environment)
    interface.run()