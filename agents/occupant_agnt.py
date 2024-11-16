from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import numpy as np
from spade.message import Message
import ast


MAX_HEALTH = 1000   #sempre q num quadrado com fumo, sofre dano

class OccupantAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
        self.floor = self.environment.get_occupant_loc(self.jid)[2]
        self.elf = self.environment.get_occupant_state(self.jid)
        self.elf_bar = MAX_HEALTH    #quando chegar a 0 -> muda de nível 
    

    async def setup(self):
        #initialize occupant agent
        print(f"Occupant {self.jid} starting ...")
        print(f"Initial position: {self.environment.get_occupant_loc(self.jid)}")
        await asyncio.sleep(0.1)
    
    class ReceiveWarning(OneShotBehaviour):
            #receive warning from BMS saying there is an emergency
            async def run(self):
                msg = await self.receive(timeout=10)
                if msg:
                    print(f"Occupant {self.agent.jid} received message: {msg.body}")
                else: 
                    print(f"Occupant {self.agent.jid} did not receive any messages")



    class  HOFAH(CyclicBehaviour):
        ''' 
        ER Agents ask for a health check and if the occupant is not dead or already saved,
        responds with is health state
        if health < 2, ER Agent tries to cure occupant
        '''
        #recebe msg asking for health state
        async def run(self):
            holding_out_for_a_hero = await self.receive(timeout = 15)
            if holding_out_for_a_hero and (self.agent.elf > -1) and (self.agent.elf < 2): #not dead
                print(f"Occupant {self.agent.jid} received message: {holding_out_for_a_hero.body}")

                #send info to ER agent on that floor
                await self.send_info_to_er()
                        
            else: 
                print(f"Occupant {self.agent.jid} did not receive any messages or is dead :(")
            
        async def send_info_to_er(self):
            if str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
                er_agents_locs = self.agent.environment.get_all_er_locs()
                i = 0
                for id in er_agents_locs.keys():
                    loc = er_agents_locs[str(id)]
                    if loc[2] == z and self.agent.environment.er_role[str(id)]:
                        #o primeiro er agent nesse floor recebe msg
                        msg = Message(to=f"eragent{i}@localhost")
                        msg.set_metadata("performative", "informative")
                        msg.body = f"[Occupant] I am: {self.agent.jid}; My position is: {x,y,z}; My health state is: {self.agent.elf}"

                        await self.send(msg)
                    i += 1

    class LifeBar(CyclicBehaviour):
        '''
        if an occupant is a cell with smoke, then he progressively loses health
        '''
        async def run(self):
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            #se estiver num local com fumo ativar lower_life_spam
            if self.agent.environment.obstacles[self.agent.environment.get_occupant_loc(self.agent.jid)] == 'smoke':
                self.lower_life_spam
            
        async def lower_life_spam(self):
            if self.elf_bar == 0:
                if self.elf == 0:
                    self.elf_bar = float("inf")
                else:
                    self.elf_bar = MAX_HEALTH
                self.elf = self.elf - 1

        async def white_ribons(self):
            ''' quando paramed "cura" o occ ele deixa de poder morrer'''
            self.elf_bar = float("inf")                   

            
    #occorre normalmente está constantemente a ser feita
    class EvacuateBehaviour(CyclicBehaviour):  
        """occupants move to the exit"""
        async def run(self):

            hierarchy = self.prefered_moves() #array with possible moves ordered by distance to closest exit or stairs
            msg = Message(to="building@localhost")
            msg.set_metadata("performative", "informative")
            msg.body = f"Occupant: {self.agent.jid}; Preferred Moves: {hierarchy}"

            await self.send(msg)
            
            #print(f"Preferences of occupant {self.agent.jid}: {hierarchy}")

            response = await self.receive(timeout=10) 

            if response:
                await self.process_move(response.body)
            else:
                print(f"Occupant {self.agent.jid} didn't move")

            await asyncio.sleep(2)

        async def process_move(self, new_postition):
            if "new position" in new_postition:
                pos_str = new_postition.split(':')[-1].strip()
                pos = ast.literal_eval(pos_str)
                exits = self.agent.environment.get_all_exits_loc()
                stairs = self.agent.environment.stairs_locations
                windows = self.agent.environment.windows_locations
                grid = self.agent.environment.get_grid(pos[2])
                if pos in exits:
                    #print(f"Occupant {self.agent.jid} is moving to new position {pos}")
                    #leave building
                    if self.is_possible_move(pos[0], pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                        self.agent.environment.leave_building(self.agent.jid)
                        print(f"Occupant {self.agent.jid} left the building safely")
                        await self.agent.stop()
                
                elif pos in stairs:
                    if self.leavefloor(pos[2]-1, pos=pos) != []:
                        #change floor
                        grid = self.agent.environment.get_grid(pos[2]-1)
                        new_pos = self.leavefloor(pos[2]-1, pos=pos)[0]
                        #print(f"new_pos: {new_pos}")
                        if self.is_possible_move(new_pos[0], new_pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys() and pos not in self.agent.environment.obstacles.keys():
                            print(f"Occupant {self.agent.jid} is moving to floor {pos[2]-1} and heading to new position {new_pos}")
                            self.agent.environment.update_occupant_position(self.agent.jid, *new_pos)
                            self.agent.floor = new_pos[2]
                    else:
                        print(f"The stairs in floor {pos[2]-1} are blocked. Occupant {self.agent.jid} is going to the window")
                        new_pos = self.closest_windows()
                        new_pos = (new_pos[0], new_pos[1], pos[2]-1)
                        if new_pos != -1 and self.is_possible_move(new_pos[0], new_pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                            if new_pos in windows:
                                print(f"Occupant {self.agent.jid} threw himself out the window in floor {pos[2]}")
                                #TODO: check if he is alive
                                self.agent.environment.occupants_loc.pop(str(self.agent.jid))
                                self.agent.environemnt.occupants_saved += 1 #assuming he survived
                                await self.agent.stop()
                            else:
                                self.agent.environment.update_occupant_position(self.agent.jid, *new_pos, self.agent.environment.occupants_loc[str(self.agent.jid)][2])
                        #TODO: ask for someone to catch him

                elif pos in windows:
                    print(f"Occupant {self.agent.jid} threw himself out the window in floor {pos[2]}")
                    #TODO: check if he is alive
                    self.agent.environment.occupants_loc.pop(str(self.agent.jid))
                    self.agent.environemnt.occupants_saved += 1 #assuming he survived
                    await self.agent.stop()


                else:
                    if self.is_possible_move(pos[0], pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                        print(f"Occupant {self.agent.jid} is moving to new position {pos}")
                        self.agent.environment.update_occupant_position(self.agent.jid, *pos)

                #print(f"Occupant {self.agent.jid} is now in position {self.agent.environment.get_occupant_loc(self.agent.jid)}")
            else:
                print(f"Occupant {self.agent.jid} didn't move")

        
        def distance_to_window(self):
            min_dist = len(self.agent.environment.get_grid(0)) + 2
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            best_pos = (-1,-1,-1)
            for loc in self.agent.environment.windows_locations:
                xw, yw, zw = loc
                if z == zw:
                    possible_moves = self.possible_moves()
                    for pos in possible_moves:
                        dist = np.sqrt((pos[0]-xw)**2+(pos[1]-yw)**2)
                        if dist < min_dist: best_pos = pos
            return best_pos
        
        def closest_windows(self):
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            grid = self.agent.environment.get_grid(z)
            possible_windows = self.agent.environment.get_windows_loc(z)

            if not possible_windows: return -1

            min_dist = np.sqrt((len(grid))**2 * 2)+1
            i = 0
            pos = (0,0)

            for position in possible_windows:
                x1 = position[0]
                y1 = position[1]
                dist = np.sqrt((x-x1)**2 + (y-y1)**2)
                if dist < min_dist:
                    min_dist = dist
                    pos = (x1,y1)
                i += 1

            if min_dist == np.sqrt((len(grid))**2 * 2)+1:
                return -1 #windows are blocked

            return x1, y1
                    
        def closeste_stairs(self):
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            possible_stairs = self.agent.environment.get_stairs_loc(z)

            if not possible_stairs: return -1

            min_dist = len(self.agent.environment.get_grid(0)) + 2
            i = 0
            pos = (0,0)

            for position in possible_stairs:
                x1 = position[0]
                y1 = position[1]
                if(self.agent.environment.get_grid(z)[x1][y1] == 5):
                    continue
                dist = np.sqrt((x-x1)**2 + (y-y1)**2)
                if dist < min_dist:
                    min_dist = dist
                    pos = (x1,y1)
                i += 1

            if min_dist == len(self.agent.environment.get_grid(0)) + 2:
                return -1 #stairs are blocked

            return x1, y1
        
        def closest_exit(self):
            """retorna a saída mais próxima"""
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            possible_exits = self.agent.environment.get_exit_loc(z)

            if not possible_exits:
                return -1
            
            #TODO: check priorities

            min_dist = len(self.agent.environment.get_grid(0)) + 1
            i = 0
            pos = (0,0)

            for position in possible_exits:
                x1 = position[0]
                y1 = position[1]
                dist = np.sqrt((x-x1)**2 + (y-y1)**2)
                if dist < min_dist:
                    min_dist = dist
                    pos = (x1,y1)
                i += 1

            return x1, y1

        def is_possible_move(self, x, y, grid) -> bool:
            if x < 0 or y < 0 or x >= len(grid[0]) or y >= len(grid[0]):
                #fora da grid
                return False
            
            if grid[x][y] != 0 and grid[x][y] != 6 and grid[x][y] != 3: 
                #obstaculo
                return False
            
            
            occupant_state = self.agent.environment.get_occupant_state(self.agent.jid)
            x1, y1, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            if occupant_state == 0:
                #cant move more than 1 step /cell
                if np.sqrt((x-x1)**2) > 1 or np.sqrt((y-y1)**2) > 1:
                    return False
                
            return True
            
        def possible_moves(self):
            x,y,z = self.agent.environment.get_occupant_loc(self.agent.jid)
            grid_z = self.agent.environment.get_grid(z) #no futuro alterar para BMS.get_floor(z) ->return grid
            
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
                    if self.is_possible_move(x1[i],y1[j], grid_z):
                        possible_moves.append((x1[i], y1[j], self.agent.floor))



            #encurtar a lista até o poss_move == curr_move
            filtered_coordinates = []
            for coord in possible_moves:
                filtered_coordinates.append(coord)
                if coord == [x,y,z]:
                    break  

            return filtered_coordinates

        def get_distance(self, x, y):
            #exits_loc = função q devolve a loc das escadas, saídas e janelas 
            z = self.agent.floor
            grid = self.agent.environment.get_grid(z)
            #search for closest exit
            dist = np.sqrt((len(grid))**2 * 2)+1
            for exit in self.agent.environment.get_exit_loc(z):
                d = np.sqrt((exit[0] - x)**2 + (exit[1] - y)**2)
                if d<dist:
                    dist = d
            if dist >= np.sqrt((len(grid))**2 *2)+1:
                #no exits 
                # search for closest stairs
                for stairs in self.agent.environment.get_stairs_loc(z):
                    d = np.sqrt((stairs[0] -x)**2 + (stairs[1] - y)**2)
                    if d<dist:
                        dist = d
                if dist >= np.sqrt((len(grid))**2 *2)+1:
                    #no available stairs
                    #searching for closest window
                    for window in self.agent.environment.get_windows_loc(z):
                        d = np.sqrt((window[0] -x)**2 + (window[1] - y)**2)
                        if d<dist:
                            dist = d

            return dist
        
        def prefered_moves(self):
            possible_moves = self.possible_moves() #todos os movimentos possíveis
            distances = [0 for i in range(len(possible_moves))] 

            #ver dist de cada poss à saida mais proxima e adequar priority list dessa forma
            #encortar a lista para ir até a poss atual
            for i in range(len(possible_moves)):
                distances[i] = self.get_distance(possible_moves[i][0], possible_moves[i][1]) #lista de distâncias à saída mais próxima ou escadas mais próximas
            
            #print(f"{self.agent.jid}: {possible_moves} {np.round(distances, 2)}")

            sorted_coordinates = [[coord for coord, dist in sorted(zip(possible_moves, distances), key=lambda x: x[1])]]
            return sorted_coordinates
        
        #quando no quadrado 4(escadas) muda de andar
        def leavefloor(self,  chosen_z, pos): #cima baixo  0 desce 1 sobe cb: bool=False,
            x, y, z = pos[0], pos[1], pos[2]
            self.floor = self.agent.environment.get_grid(chosen_z)
            #sself.agent.environment.update_occupant_position(self.agent.jid, x, y, chosen_z)#desce as escadas fora do tempo
            x1 = [x-1, x, x+1]
            y1 = [y-1, y, y+1]

            possible_moves = []
            for i in range(3):
                for j in range(3):
                    if (x==x1[i] and y==y1[j]):
                        pass
                    elif self.is_possible_move(x1[i],y1[j], self.floor):
                        possible_moves.append((x1[i], y1[j], chosen_z))

            #retorna locais onde possa ficar 
            return possible_moves
            




    
    
