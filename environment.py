import asyncio

class Environment:
    def __init__(self, grid_size=10, num_floors=1):
        self.grid_size = grid_size
        self.num_floors = num_floors

        self.building = [[[0 for _ in range(grid_size)] for _ in range(grid_size)] for _ in range(num_floors)]
        self.building.append((-1,-1,-1)); # pos outside of building

        self.current_floor = 0

        self.queue = asyncio.Queue() #fila para gerenciamento da ordem das operações

        #DOORS INFO
        self.doors_locations = [(0,4,0),(9,7,0)]
        for x, y, z in self.doors_locations:
            self.building[z][x][y] = 1             
        self.doors_state = {"Door 0": 'open',
                            "Door 1": 'closed'}
        
        #WINDOWS INFO
        self.windows_locations = [(2, 0, 0), (7, 9, 0)]
        for x, y, z in self.windows_locations:
            self.building[z][x][y] = 2 
        self.windows_state = {"Window 1": 'closed',
                            "Window 2": 'closed'}
        
        #STAIRS INFO
        self.stairs_locations = [(5,5,0)]
        for x, y, z in self.stairs_locations:
           self.building[z][x][y] = 3


        #OCCUPANTS INFO
        self.occupants_loc = {"occupant0@localhost": (1,2,0), 
                              "occupant1@localhost": (2,4,0),
                              "occupant2@localhost": (5,7,0), 
                              "occupant3@localhost": (3,8,0), 
                              "occupant4@localhost": (8,7,0)}
        """
        -1 -> morto
        0 -> n se consegue mexer
        1 -> mexe-se 1 quadrado, precisa de cura
        2 -> mexe-se 2 quadrados, is perfectly good
        """
        self.occupants_health = {"occupant0@localhost": 1, 
                              "occupant1@localhost": 0,
                              "occupant2@localhost": 1, 
                              "occupant3@localhost": 2, 
                              "occupant4@localhost": 1} # 0 means not able-bodied -> cant move
        for x,y,z in self.occupants_loc.values():
            self.building[z][x][y] = 4
        
        #print(self.building)

        #OBSTACLES INFO
        self.obstacles_loc = []
        for x, y, z in self.obstacles_loc:
            self.building[z][x][y] = 5

        #EXIT INFO
        self.exit_loc = [(0,0,0)]
        for x, y, z in self.exit_loc:
            self.building[z][x][y] = 6
        self.exits_state = {(0,0,0): 'open'}
        
        #ELEVATOR INFO
        self.elevator = 'on'

        #ER AGENTS INFO
        self.er_loc = {"eragent0@localhost": (1,0,0),
                       "eragent1@localhost": (1,0,0),
                       "eragent2@localhost": (1,0,0),
                       "eragent3@localhost": (1,0,0)}
        self.er_type = {"eragent0@localhost": 'firefighter',
                       "eragent1@localhost": 'firefighter',
                       "eragent2@localhost": 'paramedic',
                       "eragent3@localhost": 'paramedic'}
        self.er_role = {"eragent0@localhost": False,
                       "eragent1@localhost": False,
                       "eragent2@localhost": False,
                       "eragent3@localhost": False}
        for x,y,z in self.er_loc.values():
            self.building[z][x][y] = 7
        
        #print(self.building)

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
    
    
    def get_stairs_loc(self, floor):
        locations = []
        for x, y, z in self.stairs_locations:
            if z == floor:
                locations.append((x,y))
        return locations
    
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
    
    def update_occupant_position(self, agent_id, new_x, new_y, new_z):
        # Verifique se o agente está no dicionário antes de tentar acessar
        if str(agent_id) not in self.occupants_loc:
            print(f"Error: Agent ID {agent_id} not found in occupants_loc.")
            return 0  # Retorne um código de erro ou tome uma ação apropriada

        x, y, z = self.occupants_loc[str(agent_id)]
        self.occupants_loc[str(agent_id)] = (new_x, new_y, new_z)
        self.building[z][x][y] = 0
        self.building[new_z][new_x][new_y] = 4
        return 1
    
    def leave_building(self, agent_id):
        x, y, z = self.occupants_loc[str(agent_id)]
        self.building[z][x][y] = 0
        self.occupants_loc.pop(str(agent_id))
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
        return self.er_type[str(er_id)]
        
    def get_all_er_roles(self):
        return self.er_type
    
    def update_er_position(self, agent_id, new_x, new_y, new_z):
        # Verifique se o agente está no dicionário antes de tentar acessar
        if str(agent_id) not in self.er_loc:
            print(f"Error: Agent ID {agent_id} not found in er_loc.")
            return 0  # Retorne um código de erro ou tome uma ação apropriada
        
        x,y,z = self.er_loc[str(agent_id)] 
        self.er_loc[str(agent_id)] = (new_x, new_y, new_z)
        self.building[z][x][y] = 0
        self.building[new_z][new_x][new_y] = 7
        return 1
    
    #======================================================================================#
        
