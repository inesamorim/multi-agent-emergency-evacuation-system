from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.behaviour import Event
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from environment import Environment
import time
import numpy as np
import heapq
import ast

class ERAgent(Agent):
    def __init__(self, jid, password, environment:Environment, type):
        super().__init__(jid, password)
        self.environment = environment
        self.type = type
        self.helping = False #se está a transportar alguém
        self.occupants = {} # a dictionary, e.g., {id: [health, x, y, z]} - tarefas
        self.busy = True
        self.floor_alocated = -1
        self.to_help_list = []
        self.tasks = [] #for firefighter outside


    async def setup(self):
        print(f"ER Agent {self.jid} of type {self.type} is starting...")
        await asyncio.sleep(0.1)


    class GoToBuilding(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"ER Agent {self.agent.type} {self.agent.jid} received message from BMS and is coming to the rescue...")
                await asyncio.sleep(5)
                print("#####################################################")
                print(f"ER Agent {self.agent.jid} has arrived to the scene")
                self.agent.busy = False

            await asyncio.sleep(1)
            if str(self.agent.jid) == "eragent0@localhost":
                agents_per_floor, resto = self.distribute_by_floor()
                await self.distribution(agents_per_floor, resto)

        async def distribution(self, agents_per_floor, resto):
            if agents_per_floor == 0:
                #the number of er agents is lower than the number of floors
                #one er agent per floor, until there is no one left to distribute
                for i in range(self.agent.environment.num_er):
                    floor = i
                    er_id = f"eragent{i}@localhost"
                    #self.agent.floor_alocated = floor

                    if i == 0:
                        print(f"ER Agent {er_id} is staying outside to help with fires and saving people through the windows")
                    
                    else:
                        self.agent.environment.update_er_role(er_id, True)
                        print(f"ER agent {er_id} is assigned captain of floor {floor}")

                        pos = self.possible_pos(floor)
                        while pos == 0:
                            await asyncio.sleep(2)
                            pos = self.possible_pos(floor)

                        print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                        self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                return 1

            z = 0
            print(f"ER Agent eragent0@localhost is staying outside to help with fires and saving people through the windows")
            for i in range(1,self.agent.environment.num_er,agents_per_floor):
                #the number of er agents is higher than the number of floors
                #agent_per_floor é a divisão inteira entre os agents e o numero de floors
                #o que sobra vai para o andar 0
                if z >= self.agent.environment.num_floors:
                    #distribuir os que sobram
                    z1 = 0
                    for j in range(i, i+resto):
                        if j == self.agent.environment.num_er: break
                        er_id = f"eragent{j}@localhost"
                        floor = z1
                        self.agent.floor_alocated = floor
                        pos = self.possible_pos(floor)
                        while pos == 0:
                            await asyncio.sleep(2)
                            pos = self.possible_pos(floor)
                        """if pos == 0:
                            pos = self.possible_pos(floor+1)
                            if pos == 0:
                                pos = pos = self.possible_pos(floor-1)"""
                        print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                        self.agent.environment.er_loc[str(er_id)] = (pos[0], pos[1],floor)
                        self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                    z1 += 1
                    break
                else:
                    for j in range(i, i+agents_per_floor):
                        er_id = f"eragent{j}@localhost"
                        if j == self.agent.environment.num_er: break
                        if i == j:
                            self.agent.environment.update_er_role(er_id, True)
                            print(f"ER agent {er_id} is assigned captain of floor {z}")
                        floor = z
                        self.agent.floor_alocated = floor
                        pos = self.possible_pos(floor)
                        while pos == 0:
                            await asyncio.sleep(2)
                            pos = self.possible_pos(floor)
                        """ if pos == 0:
                                pos = self.possible_pos(floor+1)
                                if pos == 0:
                                    pos = pos = self.possible_pos(floor-1)"""
                        print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                        self.agent.environment.er_loc[str(er_id)] = (pos[0], pos[1],floor)
                        self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                    z += 1

        def distribute_by_floor(self):
            #assuming firefighters can get through stairs with fire
            num_floors = self.agent.environment.num_floors
            num_er_agents = self.agent.environment.num_er
            agents_per_floor = num_er_agents // num_floors
            resto = num_er_agents % num_floors
            return agents_per_floor, resto

        def possible_pos(self, floor):
            grid = self.agent.environment.get_grid(floor)
            x, y = self.agent.environment.get_stairs_loc(floor)[0]
            x1 = [x-1, x+1]
            y1 = [y-1, y+1]
            for i in x1:
                for j in y1:
                    if grid[i][j] == 0:
                        return i,j
            return 0


    class ToSaveOrNotToSave(CyclicBehaviour):
        async def run(self):

            if self.agent.environment.er_type[str(self.agent.jid)] == 'firefighter' and self.agent.environment.er_loc[str(self.agent.jid)] != (-1,-1,-1):
                print("====================================================")
                print(f"Firefighter {self.agent.jid} is checking for fires")
                print("====================================================")
                await self.kill_that_fire()
            msg = await self.receive(timeout=10)
            if self.agent.environment.er_type[str(self.agent.jid)] == 'paramedic' and not self.agent.busy:
                if self.agent.to_help_list != []:
                    task = self.agent.to_help_list.pop(0)
                    self.agent.busy = True
                    occ_id = task[0]
                    x = task[2]
                    y = task[3]
                    z = task[4]
                    possible = [(x-1,y-1),(x,y-1),(x-1,y),
                                (x+1,y+1),(x,y+1),(x+1,y),
                                (x-1,y+1),(x+1,y-1)]
                    new_x, new_y = self.move_to_target((x,y))
                    if str(self.agent.jid) in self.agent.environment.er_loc.keys():
                        self.agent.environment.update_er_position(self.agent.jid, new_x, new_y, z)
                        print(f"Paramedic{self.agent.jid} moved to position {(new_x,new_y,z)}")
                        if (new_x,new_y) in possible:
                            self.cure(occ_id)
                            print(f"Paramedic {self.agent.jid} has cured occupant {occ_id}")
                            self.agent.busy == False


            if msg:
                if "leave the building" in msg.body:
                    print(f"ER Agent {self.agent.jid} is leaving the building")
                    x, y, z = self.agent.environment.er_loc[str(self.agent.jid)]
                    self.agent.environment.update_er_location(self.agent.jid,-1,-1,-1)
                    self.agent.environment.er_loc.pop(str(self.agent.jid))
                    await self.agent.stop()
                elif "New task" in msg.body and self.agent.environment.er_type[str(self.agent.jid)] == 'paramedic':
                    task = msg.body.split(":")[1].strip()
                    task = ast.literal_eval(task)
                    print(f"adding task {task}")
                    self.agent.to_help_list.append(task)


            await asyncio.sleep(5)

        



        #------------------------------------------------------------------------------------#
        #------------------------------------------------------------------------------------#
        #----------------------------funções dos paramédicos---------------------------------#
        def cure(self, occ_id):
            if str(occ_id) in self.agent.environment.occupants_health.keys():
                self.agent.environment.occupants_health[str(occ_id)] = 1


        # se paramed -> chegará beira da pessoa e invocar cura(dependedndo do estado demora x tempo)
        async def stagnation(self):
            """
            invocar quando er type==2 chega á beira do occ indicado
            Sets occ.elf_bar of the target agent to infinity.

            Parameters:
                occ (list): A list containing [occ_id, type, x, y, z]
            """
            if self.agent.environment.er_type[str(self.agent.jid)] == 'paramedic':
                # Assuming that occ_id can be used to access the agent instance
                occ_id = next(iter(self.occupants)) #o 1º id


                if occ_id is not None: 
                    if self.occupants[str(occ_id)][0] != -1: #ainda se pode salvar
                        
                        timm = [6, 4, 2] #tempo de salvar proporcional ao nível do occ
                        await asyncio.sleep(timm[self.occupants[str(occ_id)][0]])

                        # Set elf_bar of the target agent to infinity
                        if self.occupants[str(occ_id)][0] == -1:
                            self.agent.environment.er_occ_status.pop[str(occ_id)] #occ could not be saved
                        occ_id.white_ribons()
                        print(f"Set elf_bar of agent {occ_id} to infinity.")

                        #remove form list to_save
                    else:
                        #informar o ff que ficou encarege de socorrer a pessoa para a ignorar
                        self.agent.environment.er_occ_status.pop[str(occ_id)]
                        
                else:
                    print(f"Agent with id {occ_id} not found or dead.")

                self.occupants.pop(occ_id)#remover do dic

        #------------------------------------------------------------------------------------#
        #------------------------------------------------------------------------------------#
        #--------------------------------funções dos ff -------------------------------------#

        def get_that_fire(self):
            f = False
            x1, y1, z = self.agent.environment.er_loc[str(self.agent.jid)]
            #print(x1,y1,z)
            grid = self.agent.environment.get_grid(z)
            #print(grid)
            rows, cols = len(grid), len(grid[0])

            for x in range(rows):
                for y in range(cols):
                    if grid[x][y] == 5:
                        if self.agent.environment.obstacles[(x,y,z)] == "fire":
                            f = True
                            x1 = x 
                            y1 = y
                            return x1, y1, f
            return x1, y1, f

        async def kill_that_fire(self):
            '''
            se no andar sponar fogo o ff vai lá apagá-lo
            vê onde está o fogo no andar 
            caham path para essa pos
            enquanto houver fogo, chamar path para a 1ª pos encontrada

            o path já apaga parte do fo
            '''
            x1, y1, z = self.agent.environment.er_loc[str(self.agent.jid)]
            grid = self.agent.environment.get_grid(z)
            x, y, f = self.get_that_fire() 
            if f:
                print(f"Firefighter {self.agent.jid} found a fire in position {(x,y,z)}")
                x1,y1 = self.move_to_target((x,y))
                if str(self.agent.jid) in self.agent.environment.er_loc.keys():
                    self.agent.environment.update_er_position(self.agent.jid, x1, y1, z)
                    print(f"Firefighter {self.agent.jid} moved to position {(x1,y1,z)}")
                    #x, y, f = self.get_that_fire()
                    await asyncio.sleep(2)

                x_around = [x1-1,x1,x1+1]
                y_around = [y1-1,y1,y1+1]
                self.agent.environment.update_er_position(self.agent.jid, x1, y1, z)

                for i in x_around:
                    for j in y_around:
                        if i == x and j == y:
                            pass
                        if grid[i][j] == 5:
                            if (i,j,z) in self.agent.environment.stairs_locations:
                                self.agent.environment.building[z][i][j] = 3
                            elif (i,j,z) in self.agent.environment.windows_locations:
                                self.agent.environment.building[z][i][j] = 2
                            elif (i,j,z) in self.agent.environment.exit_loc:
                                self.agent.environment.building[z][i][j] = 6
                            else:
                                self.agent.environment.building[z][i][j] = 6
                            print(f"Successfully extinguished fire in position {(i,j)}") 
                            self.agent.environment.obstacles.pop((i,j,z))


                print(f"Successfully extinguished fire in position {(x,y)}") 
            else:
                print(f"Firefighter {self.agent.jid} did not found fires")

            return 
        
        def move_to_target(self, target):
            #target: x, y
            x_self, y_self, z = self.agent.environment.er_loc[str(self.agent.jid)]
            grid = self.agent.environment.get_grid(z)
            
            x = target[0]
            y = target[1]
            print(grid[x][y])
            x1 = [x-1,x-1,x-x+1,x+2]
            y1 = [y-1,y-1,y-y+1,y+2]

            min_dist = np.sqrt((x-x_self)**2+(y-y_self)**2)
            best_pos = (x_self, y_self)
            for i in x1:
                for j in y1:
                    if self.is_possible_move(i,j,grid):
                        dist = np.sqrt((i-x)**2+(j-y)**2)
                        if dist <= min_dist:
                            min_dist = dist
                            best_pos = (i,j)
            return best_pos
                            
        def is_possible_move(self, x, y, grid) -> bool:
            if x < 0 or y < 0 or x >= len(grid[0]) or y >= len(grid[0]):
                #fora da grid
                return False
            
            if grid[x][y] == 5: return True
            
            if grid[x][y] != 0 and grid[x][y] != 6 and grid[x][y] != 3 and grid[x][y] != 5: 
                #obstaculo
                return False
            return True
            



    class SaveThroughWindow(CyclicBehaviour):
        async def run(self):
            if str(self.agent.jid) in self.agent.environment.er_loc.keys():
                if self.agent.environment.er_loc[str(self.agent.jid)] == (-1,-1,-1) and str(self.agent.jid) == 'eragent0@localhost':
                    msg = await self.receive(timeout=10)
                    if msg:
                        print(f"ER Agent {self.agent.jid} received message from {msg.sender}")
                        if "We need stairs" in msg.body:
                            parts = msg.body.split('.')
                            floor = int(parts[0].split(':')[1].strip())
                            people_to_save = parts[1].split(';')
                            num_people = int(people_to_save[0].split(':')[1].strip())
                            raw_occupants = people_to_save[1].strip()
                            try:
                                occupants = ast.literal_eval(raw_occupants)
                                print(occupants)
                            except (SyntaxError, ValueError) as e:
                                print("Erro ao interpretar a lista:", e)
                                occupants = []
                            
                            self.agent.tasks.append((floor, num_people, occupants))
                        print("========================================================================================================")
                        print(f"ER Agent {self.agent.jid} is outside ready to start helping with firefighter's stairs\nTasks: {self.agent.tasks}")
                        print("========================================================================================================")
                        if not self.agent.busy:
                            while self.agent.tasks != []:
                                task = self.agent.tasks.pop(0)
                                if task:
                                    floor = task[0]
                                    num_people = task[1]
                                    occupants = task[2]
                                    print(f"ER Agent {self.agent.jid} is now helping people on floor {floor}")
                                    while num_people != 0:
                                        occ_id = occupants.pop(0)
                                        if str(occ_id) in self.agent.environment.occupants_loc.keys():
                                            print(f"Saving {occ_id}...")
                                            msg = Message(to=str(occ_id))
                                            msg.body = "You can come to the window"
                                            await self.send(msg)
                                            await asyncio.sleep(2)
                                            num_people -= 1
                                        else:
                                            print(f"Occupant {occ_id} already died or escaped")

            await asyncio.sleep(3)





    #creates captains and their functions

    class KarenOfFloor(CyclicBehaviour):
        '''
        numa primeira fase cada ER é mandado para uma poss(guardar o ocal de salvamento?)
        o cap guarda a équipa de salvamento(todos os ER alocados para o andar)

        chama pelos occ
        recebe list de occ
        divide équipa presente para salvar occ
        '''

        def __init__(self):
            super().__init__()
            self.can_give = {1: [], 2:[]} #the ER that can be transfered


        async def run(self):

            # Check if self.cap from the outer ER class is True
            if self.agent.environment.er_role[str(self.agent.jid)]:
                # Perform actions only if cap is True
                print("============================================")
                print("KarenOfFloor is active and performing tasks.")

                #CheckForHealthState, ReceiveHealthState
                await self.ask_health_state()
                await self.receive_health_state(self.agent.to_help_list)

                #distribuir tarefas
                team = self.get_team()
                for agent in team:
                    if agent[1] == 'paramedic':
                        er_id = agent[0]
                        if self.agent.to_help_list != []:
                            task = self.agent.to_help_list.pop(0)
                            print(f"[Captain {self.agent.jid}] Sending new task to paramedic {er_id}")
                            msg = Message(to=str(er_id))
                            msg.body = f"New task: {task}"
                            await self.send(msg)


                z = self.agent.environment.er_loc[str(self.agent.jid)][2]

                #check for people to save
                if self.can_we_leave():
                    for er_id in self.agent.environment.er_loc.keys():
                        if self.agent.environment.er_loc[str(er_id)][2] == z:
                            msg = Message(to=str(er_id))
                            msg.body = f"[Captain {z}] You can leave the building. There is no one to save."
                            await self.send(msg)
                else:
                    print(f"[Captain {z}] We can't leave yet.")

                #check if floor is blocked
                print(f"[Captain {self.agent.jid}] Checking for ways out in floor {self.agent.environment.er_loc[str(self.agent.jid)][2]}")
  
                if z != -1:
                    if not self.check_for_ways_out():
                        print(f"[Captain {self.agent.jid}] All exits and stairs in floor {z} are blocked.")
                        await self.ask_for_stairs()
                    else:
                        print(f"[Captain {self.agent.jid}] There are still exits and/or stairs available in floor {z}")
            
            await asyncio.sleep(5)


        def can_we_leave(self):
            z = self.agent.environment.er_loc[str(self.agent.jid)][2]
            for occ in self.agent.environment.occupants_loc.keys():
                if self.agent.environment.occupants_loc[str(occ)][2] == z:
                    return False
            return True

        async def message_to_paramedic(self,id, occ_id):
            print(f"Asking for paramedic {id} for help")
            msg = Message(to=id)
            msg.set_metadata("performative", "informative")
            msg.body = f"[ER captain] Can you help: {occ_id}"

            await self.send(msg)


        async def ask_health_state(self):
            num_occupants = self.agent.environment.num_occupants
            #captain asks for health state of the occupants in the same floor as him
            if str(self.agent.jid) in self.agent.environment.er_loc.keys():
                z_cap = self.agent.environment.er_loc[str(self.agent.jid)][2]
                for i in range(num_occupants):
                    id = f"occupant{i}@localhost"
                    if str(id) in self.agent.environment.occupants_loc.keys():
                        z_occ = self.agent.environment.occupants_loc[str(id)][2]
                        if z_cap == z_occ:
                            print(f"Captain {self.agent.jid} is sending message to {id}")
                            msg = Message(to=f"occupant{i}@localhost")
                            msg.set_metadata("performative", "informative")
                            msg.body = "[ER] Please give me information on your health state"

                            await self.send(msg)

        async def receive_health_state(self, to_help_list):
            '''
            se occ tiver no pick da health, não pede ajuda, só foge
            '''
            msg = await self.receive(timeout=10)  # Wait for a message with a 10-second timeout

            if msg:
                if "My position is" in msg.body:
                    print(f"Captain {self.agent.jid} received health check from {msg.sender}")
                    # Assuming msg.body contains the message text
                    content = msg.body 

                    # Split the message by semicolons to isolate sections
                    parts = content.split(";")

                    try:
                        # Extract `id`
                        id_part = parts[0].split(":")[1].strip()

                        # Extract `position` (x, y, z) - splitting by `:` and `,`
                        position_part = parts[1].split(":")[1].strip()
                        x, y, z = map(int, position_part.strip("()").split(","))

                        # Extract `health state`
                        health_state_part = parts[2].split(":")[1].strip()
                        health_state = int(health_state_part)

                        # Create the array with agent data
                        occ = [id_part, health_state, x, y, z]

                        print(f"Agent data Received by ER Agent:\n - Id: {occ[0]};\n - Health State: {occ[1]};\n - Position:{occ[2],occ[3],occ[4]}")
                        if occ[1] < 1:
                            #0: can't move
                            #print("appending")
                            to_help_list.append(occ)
                        #atualizar env
                        self.agent.environment.er_occ_status[str(occ[0])] = occ[1:]

                        """if health_state==1: #agent é curável
                            cure_behaviour = self.Cure(occ, to_help_list)
                            self.agent.add_behaviour(cure_behaviour)"""

                    except IndexError as e:
                        print("Failed to parse message. Make sure the message format is correct:", e)
                    except ValueError as e:
                        print("Failed to convert data to integers. Check the data format:", e)

            else:
                print(f"ER Agent {self.agent.jid} did not receive any messages")

        def check_for_ways_out(self):
            floor = self.agent.environment.er_loc[str(self.agent.jid)][2]
            grid = self.agent.environment.get_grid(floor)
            building = self.agent.environment.get_building()
            for exit in self.agent.environment.get_exit_loc(floor):
                x = exit[0]
                y = exit[1]
                if grid[x][y] == 6 and self.agent.environment.exits_state[(x,y,floor)] == 'open':
                    return True
            for stairs in self.agent.environment.stairs_locations:
                x = stairs[0]
                y = stairs[1]
                z = stairs[2]
                if (grid[x][y] == 3 and z == floor and z-1 != -1):
                    if (building[z-1][x][y] == 3):
                        return True
            return False


        async def ask_for_stairs(self):
            people_to_save = 0
            occupants = []
            z = self.agent.environment.er_loc[str(self.agent.jid)][2]
            for occ in self.agent.environment.occupants_loc.keys():
                if self.agent.environment.occupants_loc[str(occ)][2] == self.agent.environment.er_loc[str(self.agent.jid)][2]:
                    people_to_save += 1
                    occupants.append(occ)
            for er_id in self.agent.environment.er_loc.keys():
                if self.agent.environment.er_loc[str(er_id)] == (-1,-1,-1) and er_id == 'eragent0@localhost':
                    #is outside
                    print("----------------------------------------------------------")
                    print(f"ER Agent {self.agent.jid} is sending message to {er_id}")
                    msg = Message(to=str(er_id))
                    msg.body= f"[Captain {z}] We need stairs on the window in floor: {z}. People to save: {people_to_save}; {occupants}"
                    #print(occupants)
                    await self.send(msg)


        def get_team(self):
            """the team of a certain captain are all the er agents alocated to the same floor as himself
            the captain makes the decisions and the distribution of tasks"""
            team = []
            _, _, z = self.agent.environment.get_er_loc(self.agent.jid)
            dic = self.agent.environment.get_all_er_types()
            for agent in dic.keys():
                if str(agent) in self.agent.environment.er_loc.keys():
                    # dic -> id: type
                    type = dic[str(agent)]
                    er_pos = self.agent.environment.get_er_loc(agent)
                    if er_pos[2] == z:
                        team.append((agent, type))

            return team


#------------------------------------------------------------------------------------------------------------#
#-----------------------------------------------Not Used-----------------------------------------------------#
#------------------------------------------------------------------------------------------------------------#

def add_patient(self, patient_inf):
        ''' to add to list of attendence'''
        #patient_inf -> [id, type, x, y, z]
        if not(patient_inf[0] in self.occupants):
            self.occupants[patient_inf[0]] = patient_inf[1:]

def modify_other_agent_occ(self, other_agent_id, patient_inf):
    """
    Modify another agent's self.occupants if the agent exists.
    Adds the occ info to the list for the specified `occ_id`.
    """
    # Retrieve the other agent using the registry
    other_agent = Agent.agents_registry.get(other_agent_id)

    # Check if the other agent exists
    if other_agent:
        if not(patient_inf[0] in other_agent.occupants):
            other_agent.occupants[patient_inf[0]] = [patient_inf[1:]]  # Create a new entry if occ_id is new
            print(f" {other_agent_id} will try to treat occ: {other_agent.occ}")
    else:
        print(f"Agent with ID {other_agent_id} not found.")

        def evaluate_fire(self, x, y, z, max_fire_threshold=9):
            '''
            faz blob do fogo, e retorna o tamanho da blob
            defalt max_fire_threshold=9
            '''
            grid = self.agent.environment.get_grid(z)

            #se obstacle != 'fire'
            #print(self.agent.environment.obstacles)
            if (x, y, z) in self.agent.environment.obstacles.keys():
                if self.agent.environment.obstacles[(x, y, z)] != 'fire':
                    return 20 #no diff between large_fire and normal obstacle
            

            rows, cols = len(grid), len(grid[0])
            visited = set()
            stack = [(x, y)]
            fire_blocks = []  # Track all fire positions for potential extinguishing
            fire_count = 0

            # Flood fill logic
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited:
                    continue

                visited.add((cx, cy))
                if (cx,cy,z) in self.agent.environment.obstacles.keys():
                    if self.agent.environment.obstacles[(cx,cy,z)] == 'fire':
                        fire_count += 1
                        fire_blocks.append((cx, cy))  # Add position to extinguish list

                        # Explore neighbors
                        for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1),
                                    (cx+1, cy+1), (cx+1, cy-1), (cx-1, cy+1), (cx-1, cy-1)]:
                            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in visited:
                                stack.append((nx, ny))

            # Extinguish fire if the count is within the threshold and ER wannna go that way 
            if fire_count <= max_fire_threshold:
                for fx, fy in fire_blocks:
                    er_x, er_y, _ = self.agent.environment.get_er_loc(self.agent.jid)  # Assume ER's current position is stored
                    for fx, fy in fire_blocks:
                        if np.sqrt((fx - er_x)**2 + (fy - er_y)**2) < 2: 
                            # Extinguish all connected fire blocks
                            for f in fire_blocks:
                                self.environment.obstacles.pop(str(f))   # Clear the fire
                            print(f"Extinguished {fire_count} fire blocks starting from {x, y}.")
                            break
                    

            return fire_count
        

class AbductionOfOcc(OneShotBehaviour):

    ''' se houver um grupo de pessoas é fornecido antecipadamente por ??? dada uma lista de prioridade e
    por ordem cada ER vai buscar a pessoa q lhe foi referide'''

    async def can_hellp(self):
        #if is already helping or can help
        return not self.helping


    async def fuse(self, occupant_id):
        ''' se houver uma pessoa a 1 quadrado de distância ela é "acolhida" pelo ER que vai carregar o seu id '''

        # Check if the occupant exists in the occupants dictionary
        if occupant_id not in self.occupants:
            print(f"Occupant with ID {occupant_id} not found.")
            return

        self.helping = True

        # Retrieve occupant's info and print or store it as needed
        self.occupant_info = self.occupants[occupant_id]
        print("Abducting occupant:", self.occupant_info)

        # Update grid (e.g., setting position to `None` if using a 2D array or removing the key in a dict)
        self.environment.update_occupant_position(occupant_id, -1, -1, -1) #tentar assumir q está fora da grid

        # Optionally, remove occupant from the occupants dictionary
        del self.occupants[occupant_id]
        print(f"Occupant {occupant_id} removed from the occupants list.")


    ############################################################################
    ############################################################################
    ############################################################################


    async def poss_drop(self,x, y, grid):
        if x < 0 or y < 0 or x >= len(grid[0]) or y >= len(grid[0]):
            #fora da grid
            return False

        if (grid[x][y]!=0) or (grid[x][y]!=3):
            #obstaculo
            return False

        return True


    async def where_to_drop(self):
        x, y, z = self.agent.environment.get_er_loc(self.agent.jid)
        x1 = [x-1,x,x+1]
        y1 = [y-1,y,y+1]
        grid =  self.agent.environment.get_grid(z)

        for i in range(3):
            for j in range(3):
                if self.poss_drop(x1[i],y1[j], grid):
                    return x1[i], y1[j], z

        return -1

    async def releace_hostege(self):
        #quando em segurança liberta a pessoa
        #se a pessoa está a 0 só quando na exit é q é dropada
        #se 1 quando numa área determinada como não afetada (DEC)
        #vai ter de procurar o sítio mais prox para dar drop

        # get_exit_loc(self,floor)
        # get_er_loc(self, er_id)
        x, y, z = self.agent.environment.get_er_loc(self.agent.jid)
        if not([x,y] in self.agent.environment.get_exit_loc(z)):
            #dropping action occurs faster than moving
            if self.where_to_drop() == -1:
                return -1
            x1, y1, z1 = self.where_to_drop()
            self.environment.update_occupant_position(self.occupant_info, x1, y1, z1)

        #else deu drop na saída poss de occ não altera
        self.helping = False


def astar_possible_moves(self, x, y):
    _,_,z = self.agent.environment.get_er_loc(self.agent.jid)
    grid_z = self.agent.environment.get_grid(z)
    
    ''' 
        1->portas 
        2->janelas
        3->escadas
        4->pessoas
        5->obstáculos
        6->saída
    '''

    x1 = [x-2, x-1, x, x+1, x+1]
    y1 = [y-2, y-1, y, y+1, y+2]
    possible_moves = []
    for i in range(5):
        for j in range(5):
            if self.is_valid_move(x1[i],y1[j], z, grid_z):
                possible_moves.append((x1[i], y1[j], z))

    return possible_moves

def is_valid_move(self, x, y, z, grid):
    if x < 0 or y < 0 or x >= len(grid) or y >= len(grid[0]):
        #fora da grid
        return False
    
    if grid[x][y] == 5:
        obstacle = self.evaluate_fire(x, y, z)

        if obstacle <= 9:
            # Allowed to move into small fire
            return True
    
    if grid[x][y] != 0 and grid[x][y] != 6 and grid[x][y] != 3: 
        #obstaculo
        return False

                    
    return True

def find_path(self, target):
    # A* algorithm with modifications for two-step movement
    open_set = []
    position = self.agent.environment.get_er_loc(self.agent.jid) #x,y,z
    heapq.heappush(open_set, (0, position))  # Priority queue with (cost, position)
    came_from = {}
    g_score = {position: 0}
    f_score = {position: self.heuristic(position, target)}

    while open_set:
        _, current = heapq.heappop(open_set)

        # Exit reached
        if current == target:  
            #o occ guarda o caminho q quer fazer 
            self.path = self.reconstruct_path(came_from, current)
            return self.path

        x, y, _ = current
        neighbors = self.astar_possible_moves(x, y) #where he can walk to(they are poss moves)
        for nx, ny, nz in neighbors:
            #obstacle = self.evaluate_fire(nx, ny, nz)

            # Calculate movement cost based on the obstacle
            move_cost = 1
            #if obstacle <= 9: #small_fire <= 9 blocks
                #   move_cost += obstacle*2  # Add a penalty for moving into fire (size of fire influences)
            #else:
                #   continue  # Skip large fire entirely

            tentative_g_score = g_score[current] + move_cost
            if tentative_g_score < g_score.get((nx, ny), float('inf')):
                came_from[(nx, ny, nz)] = current
                g_score[(nx, ny, nz)] = tentative_g_score
                f_score[(nx, ny, nz)] = tentative_g_score + self.heuristic((nx, ny), target)

                # Avoid duplicates in the open_set
                if (nx, ny) not in f_score:
                    heapq.heappush(open_set, (f_score[(nx, ny, nz)], (nx, ny, nz)))

    return None  # No path found


def find_next_position(self, target):
    _,_,z = self.agent.environment.get_occupant_loc(self.agent.jid)
    grid = self.agent.environment.get_grid(z) #no futuro alterar para BMS.get_floor(z) ->return grid

    # Find and reserve the next position
    path = self.find_path(target)
    if path and len(path) > 0:
        next_position = path[0]  # Take the first step in the path
        #grid[x][y] != 0 and grid[x][y] != 6 and grid[x][y] != 3
        if grid[next_position[0]][next_position[1]]!=0 and grid[next_position[0]][next_position[1]]!=6 and grid[next_position[0]][next_position[1]]!=3:
        #if next_position not in self.environment.occupied_positions:
            self.agent.environment.update_er_position(next_position[0], next_position[1], z)
            #self.environment.occupied_positions.add(next_position)  # Reserve position
            return next_position
    return self.current_position  # Stay in place if no valid move
    

def move_to_position(self, new_position):
    # Move and update occupied positions
    self.environment.occupied_positions.remove(self.current_position)  # Free current position
    self.current_position = new_position  # Update position
    self.environment.occupied_positions.add(new_position)  # Mark new position as occupied
    
    self.agent.environment.update_er_position(self.agent.jid, *new_position)

def act(self, target):
    """Main method for the ER agent to take an action."""
    next_position = self.find_next_position(target)
    self.move_to_position(next_position)

def heuristic(self, a, b):
    """
    ?Euclidean? distance heuristic for grid navigation.
    """
    return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def reconstruct_path(self, came_from, current):
    """
    Reconstructs the path from start to target.

    exp:
    came_from = {
        (C): (B),
        (B): (A),
        (A): (start)
    }

    chamado pela find_path para dar o caminho esperado
    """
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


async def save_stairs(self, extinguish_limit=4, time_period=2 ):
    '''
    in floor their in, if not salvable-> too in flames
    get poss of main stairs(this case only one exists)
    for radius of 3 kill fire
    '''
    x1, y1, z = self.agent.environment.er_loc[str(self.agent.jid)]
    x, y = self.agent.environment.get_stairs_loc(z) #[x, y]
    grid = self.agent.environment.get_grid(z)

    extinguished_count = 0  # Counter for flames extinguished in this period

    # Define the range to check (2 squares around)
    for dx in range(-2, 3):  # Includes -2, -1, 0, 1, 2
        for dy in range(-2, 3):
            # Calculate the coordinates to check
            nx, ny = x + dx, y + dy
            
            # Check if the coordinates are within bounds of the grid
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]):
                # If the square contains flames, extinguish them
                if grid[nx][ny] == 5:
                    if self.environment.obstacles(str(nx, ny)) == "fire":
                        self.environment.obstacles.pop(str(nx, ny))
                        print(f"Flame extinguished at ({nx}, {ny})")
                        extinguished_count += 1
                    
                    # Check if the extinguished limit is reached
                    if extinguished_count >= extinguish_limit:
                        print(f"Reached extinguish limit of {extinguish_limit}. Pausing for {time_period} seconds...")
                        time.sleep(time_period)  # Pause
                        extinguished_count = 0  # Reset counter


    return 
        
async def find_accessible_window(self, x, y, z):
    windows = self.agent.environment.windows_locations
    for window in windows:
        wx, wy = window
        if self.is_window_accessible(wx, wy, x, y):
            return (wx, wy, z)

    for floor in range(len(self.agent.environment.windows_locations)):
        if floor != z:
            windows = self.agent.environment.windows_locations[floor]
            for window in windows:
                wx, wy = window
                if self.is_window_accessible(wx, wy, x, y):
                    return (wx, wy, floor)

    return None

def is_window_accessible(self, wx, wy, x, y):
    distance = ((wx - x) ** 2 + (wy - y) ** 2) ** 0.5
    return distance <= 1  #janela acessível se distância<=1..

async def perform_save(self, agent_id, window_position):
    print(f"Agent {agent_id} is saving through the window at {window_position}...")
    await asyncio.sleep(3)
    print(f"Agent {agent_id} successfully saved the occupant through the window")

    #self.exits_available.append(window_position)
    self.agent.environment.exits.add(window_position)
    self.agent.environment.windows.remove(window_position)
    self.kill()


    async def trafg_ER_to(self, p_in_need, ff_in_need, cap_in_need, id):
        '''
        enquanto puder transferir, transfere para o piso necessário
        '''
        if str(id) == self.agent.jid:
            #altera vall para onde er_id foi alocado
            #se get_team for constantemente atualizada não necessita de trafg_ER_from()
            #paramed
            _, _, z = self.agent.environment.get_er_loc(cap_in_need)
            while p_in_need>0 and len(self.can_give[1])>0:
                id_team_member = self.can_give[1][0]
                self.can_give[1].pop()
                id_team_member.agent.floor_alocated = z
                p_in_need -= 1

            #ff
            while p_in_need>0 and len(self.can_give[1])>0:
                id_team_member = self.can_give[2][0]
                self.can_give[2].pop()
                id_team_member.agent.floor_alocated = z
                ff_in_need -= 1

        '''
        se = 0 já está o prob resolvido
        se != continua a pedir aos mais prox
        se for a todos e nada é acrescentada a urgência para BMS se urgência >= z/2 -> são pedidos reforços
        '''
        return p_in_need, ff_in_need


    def get_order_for_loors(self, pos):
        # Create a list of tuples (distance, index, element) for each element in lst
        #z_tot = self.agent.environment.num_floors()
        lst = [i for i in range(self.agent.environment.num_floors())]

        elements_with_distance = [
            (abs(i - pos), i, lst[i]) for i in range(len(lst))
        ]

        # Sort by distance, and in case of tie, by index
        elements_with_distance.sort(key=lambda x: (x[0], x[1]))

        # Extract the sorted elements only (ignoring distance and index)
        reordered_list = [element for _, _, element in elements_with_distance if _ != pos]

        return reordered_list


    async def call_for_suport(self, p_in_need, ff_in_need):
        '''
        ir por andares
        obter agentes do andar
        ver o cap e mandar-lhe a msg
        '''
        z = self.agent.environment.er_loc[self.agent.ijd][2]
        zzz = self.get_order_for_loors()
        for z in zzz:
            agents_f = self.agent.environment.get_er_in_floor(z)
            for agent in agents_f:
                if self.agent.environment.er_role[agent]:
                    p_in_need, ff_in_need = self.trafg_ER_to(self, p_in_need, ff_in_need, self.agen.jid, id)
            if p_in_need == 0 and ff_in_need == 0:
                return -1
        return 1 #não conseguiu, ainda necessita de ajuda

    def get_n_of(self, team, len_to_save):
        '''
        ver quantos menmbros da team são paramed e quantos são ff

        se valores diff dos esperados gardar as alterações
        '''
        n_paramed = 0.001
        n_ff = 0.001
        for agent in team:
            if agent[1] == 2: n_paramed+=1
            if agent[1] == 1: n_ff+=1

        '''
                    neste caso, pedir por ajuda
        -> paramédicos     type:1     n/ner >=7.5
        -> ff              type:2     n/ner >=5.5

        neste caso criar lista de possíveis transferências
        -> paramédicos     type:1     n/ner <=3.5
        -> ff              type:2     n/ner <=1.5


        '''
        p_in_need = 0
        ff_in_need = 0

        #paramed
        if len_to_save/n_paramed<=3.5:
            for id, type_ in team:
                if type_ == 1:
                    self.can_give[1].append(id)
                    #self.can_give.append([id, type_])
                    if len_to_save / n_paramed > 3.5:
                        break

        elif len_to_save/n_paramed>=7.5:
            for id, type_ in team:
                if type_ == 1:
                    p_in_need+=1
                    if len_to_save / n_paramed < 7.5:
                        break

        #ff
        if len_to_save/n_ff<=1.5:
            for id, type_ in team:
                if type_ == 2:
                    self.can_give[2].append(id)
                    if len_to_save / n_ff > 1.5:
                        break

        elif len_to_save/n_paramed>=5.5:
            #in need
            for id, type_ in team:
                if type_ == 1:
                    ff_in_need+=1
                    if len_to_save / n_paramed < 5.5:
                        break


        if p_in_need>0 or ff_in_need>0:
            self.call_for_suport(p_in_need, ff_in_need) #manda ms a pedir pelo nº de pessoas q necessita


        return n_paramed, n_ff


    def its_hero_time(self, team, to_save):
        '''
        usando a lista de pessoas  e os ER do andar
        (chamada sempre q é notado alterações de nº de ER ou DEC causa mt estrago)

        to_save = [[id, healf, x, y, z], [id, healf, x, y, z], [id, healf, x, y, z]]
        ordered by healf draws by dist
        team = {id: type}

        a pessoa(occ) pode morrer entretanto, se mt perto do -1 ignora ou, quando for ver ignorar pk está morto
        '''

        n_paramd, n_ff = self.get_n_of(team, len(to_save))
        n_p = n_paramd
        n_f = n_ff
        for agent in team:
            if agent[1] == 2:
                n_p -= 1
                for i in range(n_p, len(to_save), n_paramd):
                    self.modify_other_agent_occ(id, to_save[i])


            #se so(ainda por criar) deixar de ser membro da team trocal elif para else
            elif agent[1] == 1:
                n_f -= 1
                for i in range(n_f, len(to_save), n_ff):
                    print("foo")
                    self.modify_other_agent_occ(id, to_save[i])


        #self.occupants = {} # a dictionary, e.g., {id: [health, x, y, z]}
    
