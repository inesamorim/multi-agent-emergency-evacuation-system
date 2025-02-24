import tkinter as tk
from tkinter import ttk
from datetime import datetime
import asyncio
import threading
from environment import Environment
from tkinter import PhotoImage
from PIL import Image, ImageTk

#standby
#images not working for some reason
class BuildingInterface:
    def __init__(self, env:Environment):
        self.env = env
        self.root = tk.Tk()
        self.root.title("Multi-Agent Emergency Evacuation System")

        

        
        """#icons
        self.open_door_img = PhotoImage(file="./icons/open_door.png")
        self.exit_img = Image.open("./icons/exit.png").resize((2, 2), Image.Resampling.LANCZOS)
        print(self.exit_img.size)
        self.exit_img = ImageTk.PhotoImage(self.exit_img)

        #main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        #main grid config
        self.floor_frames = []
        for i in range(env.num_floors):
            frame = tk.Frame(self.main_frame, borderwidth=2, relief="groove")
            frame.grid(row= (i // 2)+2, column= (i % 2)+2, padx=5, pady=5)
            tk.Label(frame, text=f"Floor {i}").grid(row=0, column=0, columnspan=env.grid_size)
            self.floor_frames.append(frame)

        #show floor grid
        self.grid_labels = []
        for z in range(env.num_floors):
            floor_grid = []
            for x in range(env.grid_size):
                row = []
                for y in range(env.grid_size):
                    label = tk.Label(self.floor_frames[z], text=" ", width=4, height=2, borderwidth=1, relief="solid")
                    label.grid(row=x, column=y)
                    row.append(label)
                floor_grid.append(row)
            self.grid_labels.append(floor_grid)

        #stats
        self.stats_frame = tk.Frame(self.root)
        self.stats_frame.grid(row=1, column=0, sticky="ew")

        self.time_label = tk.Label(self.stats_frame, text="Time: 00:00")
        self.time_label.grid(row=0, column=0, padx=5, sticky="w")

        self.saved_label = tk.Label(self.stats_frame, text="Occupants Saved: 0")
        self.saved_label.grid(row=0, column=1, padx=5, sticky="w")

        self.dead_label = tk.Label(self.stats_frame, text="Dead Occupants: 0")
        self.dead_label.grid(row=0, column=2, padx=5, sticky="w")

        #cronometro
        self.start_time = env.start_time
        self.update_clock()
    
    def update_clock(self):
        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(elapsed.seconds, 60)
        self.time_label.config(text=f"Time: {minutes:02}:{seconds:02}")

        self.saved_label.config(text=f"Occupants Saved: {self.env.occupants_saved}")
        self.dead_label.config(text=f"Dead Occupants: {self.env.occupants_dead}")

    def update_grid(self):
        for z in range(self.env.num_floors):
            grid = self.env.get_grid(z)
            for x in range(len(grid)):
                for y in range(len(grid[0])):
                    value = grid[x][y]
                    label = self.grid_labels[z][x][y]
                    color = "white"
                    if value == 1:
                        label.config(image=self.open_door_img)  # Door
                    elif value == 2:
                        color = "blue"   # Window
                    elif value == 3:
                        color = "grey"   # Stairs
                    elif value == 4:
                        color = "yellow" # Occupant
                    elif value == 5:
                        color = "black"  # Obstacle
                    elif value == 6:
                        label.config(image=self.exit_img)  # Exit
                    elif value == 7:
                        color = "red"    # ER Agent
                    label.config(bg=color)

        self.root.after(1000, self.update_grid)
    
    def run(self):
        self.update_grid()
        self.root.mainloop()

def start_interface(environment):
    interface = BuildingInterface(environment)
    interface.run()
"""

"""class EvacuationUI:
    
    def __init__(self, root=None, grid_size=10, num_floors = 1, communication_queue = None):
        self.root = root
        self.grid_size = grid_size
        self.cell_size = 100
        self.num_floors = num_floors
        self.floors = []
        self.communication_queue = communication_queue #fila para comunicação com o BMS

        for i in range(num_floors):
            self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            self.floors.append(self.grid)

        self.current_floor = 0

        #DOORS INFO
        self.doors_locations = [(0,4,0),(9,7,0)]
        for x, y, z in self.doors_locations:
            grid = self.floors[z]
            grid[x][y] = 1
        self.doors_state = {"Door 0": 'open',
                            "Door 1": 'closed'}

        #WINDOWS INFO
        self.windows_locations = [(2, 0, 0), (7, 9, 0)]
        for x, y, z in self.windows_locations:
            grid = self.floors[z]
            grid[x][y] = 2
        self.windows_state = {"Window 1": 'closed',
                            "Window 2": 'closed'}

        #STAIRS INFO
        self.stairs_locations = [(5,5,0)]
        for x, y, z in self.stairs_locations:
            grid = self.floors[z]
            grid[x][y] = 3

        #OCCUPANTS INFO
        self.occupants_loc = [(1,2,0), (2,4,0), (5,7,0), (3,8,0), (8,7,0)]
        self.occupants_health = [1,0,1,1,1] # 0 means not able-bodied -> cant move
        for x, y, z in self.occupants_loc:
            grid = self.floors[z]
            grid[x][y] = 4

        self.initial_grid = self.floors

        #OBSTACLES INFO
        self.obstacles_loc = []
        for x, y, z in self.obstacles_loc:
            grid = self.floors[z]
            grid[x][y] = 5

        #ELEVATOR INFO
        self.elevator = 'on'

        #INTERFACE CREATION
        self.root.configure(bg='pink') #background color
        self.canvas = tk.Canvas(root,
                                width=self.grid_size*self.cell_size,
                                height=self.grid_size*self.cell_size,
                                bg='pink')
        self.canvas.pack(side=tk.LEFT)
        self.create_grid()

        self.agents = {}

        #simulate random agents
        #TODO: link to real agents
        for i in range(5):
            x, y, z = self.occupants_loc[i]
            self.add_agent(f"occupant{i}", x,y,z)

        #create doors
        for i in range(len(self.doors_locations)):
            x = self.doors_locations[i][0]
            y = self.doors_locations[i][1]
            curr_state = self.doors_state[f"Door {i}"]
            self.create_door(x, y, curr_state)

        #create windows
        for i in range(len(self.windows_locations)):
            x = self.windows_locations[i][0]
            y = self.windows_locations[i][1]
            self.create_window(x,y)

        #create stairs
        for i in range(len(self.stairs_locations)):
            x = self.stairs_locations[i][0]
            y = self.stairs_locations[i][1]
            self.create_stairs(x,y)

        #criar legenda
        self.legend_frame = tk.Frame(root)
        self.legend_frame.pack(side=tk.RIGHT, padx=10)
        self.create_legend()

        #updates information every 2 seconds
        self.root.after(2000, self.send_plan_to_bms)
        #self.root.after(2000, self.update_positions)


    def get_original_grid(self, z):
        grid = self.floors[z]
        return grid

    def create_grid(self):
        self.cells = {}
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x1, y1 = i * self.cell_size, j * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.cells[(i,j)] = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#ff007f")

    def create_legend(self):
        colors = {
            '#fc8eac': 'Open Door',
            '#ff007f': 'Closed Door',
            '#c154c1': 'Occupant',
            'white': 'Window',
            'lightblue': 'Stairs'
        }

        for color, description in colors.items():
            color_label = tk.Label(self.legend_frame, bg=color, width=15)
            color_label.pack(pady=5)
            description_label = tk.Label(self.legend_frame, text=description)
            description_label.pack(pady=5)

    def send_plan_to_bms(self):
        print("[UI] Sending plan to BMS")

        grid_state = self.floors #grid for all floors

        #get doors status
        doors_status = self.doors_state
        #get windows status
        windows_status = self.windows_state

        plan = {
            'floors': grid_state,
            'doors': doors_status,
            'windows': windows_status
        }

        if self.communication_queue:
            self.communication_queue.put(plan)
            print("[UI] Plan sent to BMS")
        else:
            print("[UI] Communication queue is not defined")


    def create_door(self, x,y, curr_state):
        if curr_state == 'open':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#fc8eac')
        if curr_state == 'closed':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#ff007f')

    def get_doors_loc(self, floor):
        locs = []
        for x, y, z in self.doors_locations:
            if z == floor:
             locs.append((x,y))
        return locs

    def get_doors_loc_by_id(self, floor):
        doors_loc = {}
        i = 0
        for door_id in self.doors_state:
            if self.doors_locations[i][2] == floor:
                x = self.doors_locations[i][0]
                y = self.doors_locations[i][1]
                doors_loc[f"{door_id}"] = (x,y)
            i += 1
        return doors_loc

    def get_door_status(self, door_id):
        door_status = self.doors_state[F"Door {door_id}"]
        door_location = self.doors_locations[door_id]

        return door_status, door_location

    def change_door_state(self, door_number, x,y):
        curr_state = self.doors_state["Door f{door_number}"]
        if curr_state == 'open':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#ff007f')
            self.doors_state[f"Door {door_number}"] = 'closed'
        if curr_state == 'closed':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#fc8eac')
            self.doors_state[f"Door {door_number}"] = 'open'

    def create_window(self, x, y):
        self.canvas.itemconfig(self.cells[(x,y)], fill='white')

    def create_stairs(self, x, y):
        self.canvas.itemconfig(self.cells[x,y], fill='lightblue')

    def get_stairs_loc(self, floor):
        locations = []
        for x, y, z in self.stairs_locations:
            if z == floor:
                locations.append((x,y))
        return locations


    def get_occupant_loc(self, occupant_id):
        x, y, z = self.agents[f'{occupant_id}']
        return x,y,z

    def add_agent(self, agent_id, x, y, z):
        radius = 15
        x1, y1 = x * self.cell_size + radius, y * self.cell_size + radius
        x2, y2 = x1 + radius*2, y1 + radius*2
        agent = self.canvas.create_oval(x1,y1, x2, y2, fill='#c154c1', outline='#c154c1')
        self.agents[agent_id] = (agent, x, y, z)

    def update_agent_position(self, agent_id, new_x, new_y):
        agent, old_x, old_y, z = self.agents[agent_id]
        dx, dy = (new_x - old_x) * self.cell_size, (new_y - old_y) * self.cell_size
        self.canvas.move(agent, dx, dy)
        self.agents[agent_id] = (agent, new_x, new_y)

        def update_agents(self):

            for agent_id in self.agents:
            new_x, new_y = random.randint(0 , self.grid_size-1), random.randint(0 , self.grid_size-1)
            self.update_agent_position(agent_id, new_x, new_y)

        self.root.after(1000, self.update_agents)

    def update_agents(self):
        occupied_positions = set((x, y) for _, x, y, _ in self.agents.values()) #posições atuais
        for i, agent_id in enumerate(self.agents):
            preferences = demand_list(i)

            for preferred_position in preferences:
                new_x, new_y = preferred_position
                if (new_x, new_y) not in occupied_positions: #se está livre
                    #occupied_positions.remove((old_x, old_y))  remove a posição anterior do agent
                    self.update_agent_position(agent_id, new_x, new_y) #move para lá
                    occupied_positions.add((new_x, new_y)) 
                    break

        self.root.after(1000, self.update_agents)

    def demand_list(self):
        ''' recives all the ocupants requests for new positions '''
        list_of_demanded_positions = []


        for z in self.num_floors:
            floor = []
            for i in self.agents:
                if self.agents[i][2] == z:
                    floor.append(occupant_agent.halt_the_demands())
            list_of_demanded_positions.append(floor)

        return list_of_demanded_positions

    def create_obstacle(self, x, y):
        self.canvas.itemconfig(self.cells[x,y], fill='red')
"""