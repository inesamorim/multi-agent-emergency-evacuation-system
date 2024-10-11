import tkinter as tk
import random

class EvacuationUI: 
    def __init__(self, root, grid_size=10):
        self.root = root
        self.grid_size = grid_size
        self.cell_size = 100

        #EXITS INFO
        self.exits_locations = [(0,4),(9,7)]
        self.exits = {"Exit 0": 'open',
                      "Exit 1": 'closed'}
        
        #WINDOWS INFO
        self.windows = {"Window 1": 'closed',
                        "Window 2": 'closed'}
        
        #ELEVATOR INFO
        self.elevator = 'on'

        #OCCUPANTS INFO
        self.occupants_loc = [(1,2), (2,4), (5,7), (3,8), (9,7)]

        self.root.configure(bg='pink') #background color
        self.canvas = tk.Canvas(root, 
                                width=self.grid_size*self.cell_size, 
                                height=self.grid_size*self.cell_size,
                                bg='pink')
        self.canvas.pack(side=tk.LEFT)

        self.agents = {}
        self.create_grid()

        #simulate random agents
        #TODO: link to real agents
        for i in range(5):
            x, y = self.occupants_loc[i]
            self.add_agent(f"occupant{i}", x,y)
        
        #create doors
        for i in range(len(self.exits)):
            x = self.exits_locations[i][0]
            y = self.exits_locations[i][1]
            curr_state = self.exits[f"Exit {i}"]
            self.create_door(x, y, curr_state)

        #criar legenda
        self.legend_frame = tk.Frame(root)
        self.legend_frame.pack(side=tk.RIGHT, padx=10)
        self.create_legend()
        
        #randomly update occupants position
        self.root.after(1000, self.update_agents)


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
            '#c154c1': 'Occupant'
        }

        for color, description in colors.items():
            color_label = tk.Label(self.legend_frame, bg=color, width=15)
            color_label.pack(pady=5)
            description_label = tk.Label(self.legend_frame, text=description)
            description_label.pack(pady=5)

    def create_door(self, x,y, curr_state):
        if curr_state == 'open':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#fc8eac')
        if curr_state == 'closed':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#ff007f')
    
    def change_door_state(self, door, x,y, curr_state):
        if curr_state == 'open':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#ff007f')
            self.exits[f"Exit {door}"] = 'closed'
        if curr_state == 'closed':
            self.canvas.itemconfig(self.cells[(x,y)], fill='#fc8eac')
            self.exits[f"Exit {door}"] = 'open'

    
    def add_agent(self, agent_id, x, y):
        radius = 15
        x1, y1 = x * self.cell_size + radius, y * self.cell_size + radius
        x2, y2 = x1 + radius*2, y1 + radius*2
        agent = self.canvas.create_oval(x1,y1, x2, y2, fill='#c154c1', outline='#c154c1')
        self.agents[agent_id] = (agent, x, y)

    def update_agent_position(self, agent_id, new_x, new_y):
        agent, old_x, old_y = self.agents[agent_id]
        dx, dy = (new_x - old_x) * self.cell_size, (new_y - old_y) * self.cell_size
        self.canvas.move(agent, dx, dy)
        self.agents[agent_id] = (agent, new_x, new_y)

    def update_agents(self):
        """"Randomly update the positions of all agents"""
        for agent_id in self.agents:
            new_x, new_y = random.randint(0 , self.grid_size-1), random.randint(0 , self.grid_size-1)
            self.update_agent_position(agent_id, new_x, new_y)

        self.root.after(1000, self.update_agents)
    
if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg='pink')
    root.title("Emergency Evacuation System")

    ui = EvacuationUI(root, grid_size=10)

    root.mainloop()
