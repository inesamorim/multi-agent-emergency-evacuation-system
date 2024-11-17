import asyncio
from datetime import datetime
import random

class Environment:
    def __init__(self, grid_size=10, num_floors=1, num_occupants = 5, num_er = 4):
        self.grid_size = grid_size
        self.num_floors = num_floors
        self.num_occupants = num_occupants
        self.num_er = num_er

        self.building = [[[0 for _ in range(grid_size)] for _ in range(grid_size)] for _ in range(num_floors)]
        self.building.append((-1,-1,-1)); # pos outside of building

        self.current_floor = 0

        self.queue = asyncio.Queue() #fila para gerenciamento da ordem das operações

        self.start_time = datetime.now()

        self.occupants_saved = 0
        self.occupants_dead = 0

        #DOORS INFO
        self.doors_locations = [(0,4,0),(9,7,0)]
        for x, y, z in self.doors_locations:
            self.building[z][x][y] = 1             
        self.doors_state = {"Door 0": 'open',
                            "Door 1": 'closed'}
        
        #WINDOWS INFO
        self.windows_locations = []
        self.windows_state = {} # dic -> {Windowi: state}
        for i in range(self.num_floors):
            self.windows_locations.append((2,0,i))
        for x, y, z in self.windows_locations:
            self.building[z][x][y] = 2 
            window = f"Window{i}"
            self.windows_state[str(window)] = 'open'

        #STAIRS INFO
        self.stairs_locations = []
        for i in range(self.num_floors):
            self.stairs_locations.append((5,5,i))
        for x, y, z in self.stairs_locations:
           self.building[z][x][y] = 3

        #EXIT INFO
        self.exit_loc = [(0,0,0)]
        for x, y, z in self.exit_loc:
            self.building[z][x][y] = 6
        self.exits_state = {(0,0,0): 'open'}
        
        #ELEVATOR INFO
        self.elevator = 'on'


        #OCCUPANTS INFO
        self.occupants_loc = {}
        self.occupants_health = {}
        available_positions = self.get_available_positions()
        for i in range(num_occupants):
            id = f"occupant{i}@localhost"
            pos = random.choice(available_positions)
            self.occupants_loc[str(id)] = pos
            self.occupants_health[str(id)] = random.randint(1,2)
            available_positions.remove(pos)

        """       
        -1 -> morto
        0 -> n se consegue mexer
        1 -> mexe-se 1 quadrado, precisa de cura
        2 -> mexe-se 2 quadrados, is perfectly good
        """
        for x,y,z in self.occupants_loc.values():
            self.building[z][x][y] = 4

        #OBSTACLES INFO
        """
        fire - only firefighters can pass through
        smoke - everyone can pass trhough, but loses health
        obstacle (algo que caiu do teto, etc) - no one passes through
        """
        self.smoke_pos = []
        self.obstacles_type = ['fire','obstacle']
        self.obstacles = {} # loc: type
        #self.obstacles_loc = []
        #for x, y, z in self.obstacles_loc:
            #self.building[z][x][y] = 5

        #ER AGENTS INFO - 7
        self.er_loc = {}
        self.er_role = {}
        self.er_type = {}
        for i in range(self.num_er):
            id = f"eragent{i}@localhost"
            self.er_loc[str(id)] = (-1,-1,-1)
            self.er_role[str(id)] = False
            if i%2 == 0:
                self.er_type[str(id)] = 'firefighter'
            else:
                self.er_type[str(id)] = 'paramedic'
        self.er_occ_status = {} #cap insets occ, paramedics remove occ if dead

        #BMS INFO
        self.bms_agent = "building@localhost"


        
    def get_num_of_floors(self):
        return len(self.building)
    
    def get_grid(self, floor):
        """returns the current grid for the given floor"""
        grid = self.building[floor]
        return grid
    
    def get_building(self):
        return self.building
    
    def send_plan_to_bms(self):
        return self.building
    
    def get_exit_loc(self,floor):
        locs = []
        for x, y, z in self.exit_loc:
            if z == floor:
                locs.append((x,y))
        return locs
    
    def get_all_exits_loc(self):
        return self.exit_loc
    
    def get_exit_status(self, exit_coords):
        return self.exits_state[exit_coords]

    
    def get_doors_loc(self, floor):
        """returns a list of localizations of all door in the given floor"""
        locs = []
        for x, y, z in self.doors_locations:
            if z == floor:
             locs.append((x,y))
        return locs
    
    def get_doors_loc_by_id(self, floor):
        """get doors loc organized by id"""
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
        """returns the door state, i.e., closed or open"""
        door_status = self.doors_state[F"Door {door_id}"]
        door_location = self.doors_locations[door_id]
        
        return door_status, door_location
    
    def get_windows_loc(self, floor):
        locs = []
        for x, y, z in self.windows_locations:
            if z == floor:
                locs.append((x,y))
        return locs
    
    
    def get_stairs_loc(self, floor):
        locations = []
        for x, y, z in self.stairs_locations:
            if z == floor:
                locations.append((x,y))
        return locations
    
    def get_available_positions(self):
        res = []
        for z in range(self.num_floors):
            #print(self.building[z])
            for x in range(self.grid_size):
                for y in range(self.grid_size):
                    if self.building[z][x][y] == 0:
                        res.append((x,y,z))
        return res
    
    def get_all_positions(self):
        res = []
        for z in range(self.num_floors):
            #print(self.building[z])
            for x in range(self.grid_size):
                for y in range(self.grid_size):
                    res.append((x,y,z))
        return res
    
    #=============================================OCCUPANTS==========================================#

    def get_all_occupants_loc(self):
        return self.occupants_loc
    
    def get_occupant_loc(self, occupant_id):
        x, y, z = self.occupants_loc[str(occupant_id)]
        return x,y,z
    
    def get_all_occupants_state(self):
        return self.occupants_health

    def get_occupant_state(self, occupant_id):
        return self.occupants_health[str(occupant_id)]
    
    def person_is_safe(self, occupant_id):
        x, y, z = self.occupants_loc[str(occupant_id)]
        self.building[z][x][y] = 0
        del self.occupants_loc[str(occupant_id)]
        del self.occupants_health[str(occupant_id)]
        self.occupants_saved += 1

    def update_occupant_position(self, agent_id, new_x, new_y, new_z):
        if str(agent_id) not in self.occupants_loc:
            print(f"Error: Agent ID {agent_id} not found in occupants_loc.")

        x, y, z = self.occupants_loc[str(agent_id)]
        self.occupants_loc[str(agent_id)] = (new_x, new_y, new_z)
        self.building[z][x][y] = 0
        self.building[new_z][new_x][new_y] = 4
        return 1
    
    def leave_building(self, agent_id):
        x, y, z = self.occupants_loc[str(agent_id)]
        self.building[z][x][y] = 0
        self.occupants_loc.pop(str(agent_id))
        self.occupants_saved += 1
        return 1
    
    
    #====================================================EMERGENCY RESPONDERS=======================================#

    def get_er_loc(self, er_id):
        return self.er_loc[str(er_id)]
    
    def get_er_in_floor(self, floor):
        agents = []
        for agent in self.er_loc.keys:
            z = self.er_loc[str(agent)][2]
            if z == floor:
                agents.append(agent)
        return agents
                
    def get_all_er_locs(self):
        return self.er_loc

    def get_er_type(self, er_id):
        return self.er_type[str(er_id)]
    
    def get_all_er_types(self):
        return self.er_type
    
    def get_er_role(self, er_id):
        return self.er_role[str(er_id)]
        
    def get_all_er_roles(self):
        return self.er_role
    
    def update_er_role(self, er_id, is_captain):
        self.er_role[str(er_id)] = is_captain
    
    def update_er_position(self, agent_id, new_x, new_y, new_z):
        # Verifique se o agente está no dicionário antes de tentar acessar
        if str(agent_id) not in self.er_loc:
            print(f"Error: Agent ID {agent_id} not found in er_loc.")
            return 0  # Retorne um código de erro ou tome uma ação apropriada
        
        x,y,z = self.er_loc[str(agent_id)] 
        self.er_loc[str(agent_id)] = (new_x, new_y, new_z)
        if (x,y,z) != (-1,-1,-1):
            self.building[z][x][y] = 0
        self.building[new_z][new_x][new_y] = 7
        return 1
    
    #======================================================================================#
        
