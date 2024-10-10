import tkinter as tk
import random

class EvacuationUI: 
    def __init__(self, root, grid_size=10):
        self.root = root
        self.grid_size = grid_size
        self.cell_size = 50 

        self.root.configure(bg='pink') #background color

        self.canvas = tk.Canvas(root, 
                                width=self.grid_size*self.cell_size, 
                                height=self.grid_size*self.cell_size,
                                bg='pink')
        self.canvas.pack()

        self.agents = {}
        self.create_grid()

        #simulate random agents
        #TODO: link to real agents
        for i in range(5):
            x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.add_agent(f"agent{i}", x,y)

        self.root.after(1000, self.update_agents)


    def create_grid(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x1, y1 = i * self.cell_size, j * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="coral")
    
    def add_agent(self, agent_id, x, y):
        radius = 15
        x1, y1 = x * self.cell_size + radius, y * self.cell_size + radius
        x2, y2 = x1 + radius*2, y1 + radius*2
        agent = self.canvas.create_oval(x1,y1, x2, y2, fill='coral', outline='coral')
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
