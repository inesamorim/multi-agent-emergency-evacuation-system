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
import heapq


MAX_HEALTH = 5   #sempre q num quadrado com fumo, sofre dano

class OccupantAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
        self.floor = self.environment.get_occupant_loc(self.jid)[2]
        self.elf = self.environment.get_occupant_state(self.jid)
        self.elf_bar = MAX_HEALTH    #quando chegar a 0 -> muda de nível 
        self.path = []

    

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
        #HOFAH -> holding out for a hero :)
        ''' 
        ER Agents ask for a health check and if the occupant is not dead or already saved,
        responds with is health state
        if health < 2, ER Agent tries to cure occupant
        '''
        #recebe msg asking for health state
        async def run(self):
            holding_out_for_a_hero = await self.receive(timeout = 15)
            if holding_out_for_a_hero:
                if "come to the window" in holding_out_for_a_hero.body:
                    await self.go_to_window()
                if holding_out_for_a_hero and (self.agent.elf > -1) and (self.agent.elf < 2): #not dead
                    print(f"Occupant {self.agent.jid} received message: {holding_out_for_a_hero.body}")

                    #send info to ER agent on that floor
                    er_id = holding_out_for_a_hero.sender
                    await self.send_info_to_er(er_id)
            await asyncio.sleep(3)
                        
            #else: 
                #print(f"Occupant {self.agent.jid} did not receive any messages or is dead :(")
            
        async def send_info_to_er(self, er_id):
            if str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
                #er_agents_locs = self.agent.environment.get_all_er_locs()
                #o captain desse floor recebe msg
                if str(er_id) != 'building@localhost':
                    print(f"Occupant {self.agent.jid} is sending health check to captain {er_id}")
                    msg = Message(to=str(er_id))
                    msg.set_metadata("performative", "informative")
                    msg.body = f"[Occupant] I am: {self.agent.jid}; My position is: {x,y,z}; My health state is: {self.agent.elf}"
                    await self.send(msg)
                    #print(msg._to)

                #i = 0
            """ for id in er_agents_locs.keys():
                    loc = er_agents_locs[str(id)]
                    if loc[2] == z and self.agent.environment.er_role[str(id)]:
                        #o captain desse floor recebe msg
                        msg = Message(to=f"eragent{i}@localhost")
                        msg.set_metadata("performative", "informative")
                        msg.body = f"[Occupant] I am: {self.agent.jid}; My position is: {x,y,z}; My health state is: {self.agent.elf}"

                        await self.send(msg)
                    i += 1"""
        
        async def go_to_window(self):
            print(f"[Occupant {self.agent.jid}] Coming to the window...")
            #TODO: graduatly goes to window
            self.agent.environment.leave_building(self.agent.jid)
            await self.agent.stop()


    class LifeBar(CyclicBehaviour):
        '''
        if an occupant is a cell with smoke, then he progressively loses health
        '''
        async def run(self):
            if str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
                #se estiver num local com fumo ativar lower_life_spam
                if (x,y,z) in self.agent.environment.smoke_pos:
                    print(f"[SMOKE INFO] Occupant {self.agent.jid} is in the presence of smoke\nLife Bar: {self.agent.elf_bar}\nHealth State: {self.agent.elf}")
                    await self.lower_life_spam()
            await asyncio.sleep(1)
            
        async def lower_life_spam(self):
            if await asyncio.sleep(10) == 0:
                if self.agent.elf == -1:
                    self.agent.elf_bar = float("inf")
                else:
                    self.agent.elf_bar = MAX_HEALTH
                self.agent.elf -= 1 
                if self.agent.elf == -1:
                    print(f"[SMOKE INFO] Occupant {self.agent.jid} died due to inhalation of smoke")
                    self.agent.stop()
                    self.agent.environment.occupants_loc.pop(str(self.agent.jid))
                    self.agent.environment.occupants_dead += 1

        def white_ribons(self):
            ''' quando paramed "cura" o occ ele deixa de poder morrer'''
            self.elf_bar = float("inf")                   

            
    #occorre normalmente está constantemente a ser feita
    class EvacuateBehaviour(CyclicBehaviour):  
        """occupants move to the exit"""
        async def run(self):
            #find target
            """target = self.closest_exit()
            if target == -1:
                target = self.closeste_stairs()
            if target == -1:
                target = self.closest_windows()

            self.find_path(target)"""

            hierarchy = self.prefered_moves() #array with possible moves ordered by distance to closest exit, stairs or window
            #print(hierarchy)
            if str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                grid = self.agent.environment.get_grid(self.agent.environment.occupants_loc[str(self.agent.jid)][2])
            for pos in hierarchy[0]:
                #print(pos)
                if self.is_possible_move(pos[0], pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                    #can go to position
                    if pos in self.agent.environment.exit_loc:
                        #exit
                        self.agent.environment.leave_building(self.agent.jid)
                        print(f"Occupant {self.agent.jid} left the building safely")
                        await self.agent.stop()
                    elif pos in self.agent.environment.stairs_locations and pos[2]-1 != -1:
                          #change floor
                           if self.leavefloor(pos[2]-1, pos=pos) != []:
                                grid = self.agent.environment.get_grid(pos[2]-1)
                                new_pos = self.leavefloor(pos[2]-1, pos=pos)[0]
                                #print(f"new_pos: {new_pos}")
                                if self.is_possible_move(new_pos[0], new_pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys() and pos not in self.agent.environment.obstacles.keys():
                                    print(f"Occupant {self.agent.jid} is moving to floor {pos[2]-1} and heading to new position {new_pos}")
                                    self.agent.environment.update_occupant_position(self.agent.jid, *new_pos)
                                    self.agent.floor = new_pos[2]
                                else:
                                    print(f"The stairs in floor {pos[2]-1} are blocked. Occupant {self.agent.jid} waiting to be saved through window")
                    
                    elif pos in self.agent.environment.stairs_locations and pos[2]-1 == -1:
                        new_pos = 0
                        x = pos[0]
                        y = pos[1]
                        x1 = [x-1,x,x+1]
                        y1 = [y-1,y,y+1]
                        for i in x1:
                            for j in y1:
                                if (i != x or j != y) and (i,j,pos[2]) not in self.agent.environment.stairs_locations:
                                    new_pos = (i,j)
                                    if new_pos != -1 and self.is_possible_move(new_pos[0], new_pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys() and new_pos not in self.agent.environment.stairs_locations:
                                        print(f"Occupant {self.agent.jid} is moving to new position {pos}")
                                        self.agent.environment.update_occupant_position(self.agent.jid, *pos)
                    else:
                        if self.is_possible_move(pos[0], pos[1], grid) and str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
                            print(f"Occupant {self.agent.jid} is moving to new position {pos}")
                            self.agent.environment.update_occupant_position(self.agent.jid, *pos)

                    break

            await asyncio.sleep(3)


        async def go_to_window(self):
            print(f"[Occupant {self.agent.jid}] Coming to the window...")
            #TODO: graduatly goes to window
            #z = self.agent.environment.occupants_loc[str(self.agent.jid)][2]
            print(f"foo")
            pos = self.distance_to_window()
            print(f"pos: {pos}")
            while pos not in self.agent.environment.windows_locations:
                print(f"pos: {pos}")
                self.agent.environment.update_occupant_position(self.agent.jid, *pos)
                pos = self.distance_to_window()
                await asyncio.sleep(1)
            self.agent.environment.leave_building(self.agent.jid)
            print(f"[Occupant {self.agent.jid}] Left the building safely")
            await self.agent.stop()


        def distance_to_window(self):
            min_dist = len(self.agent.environment.get_grid(0)) + 2
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            best_pos = (-1,-1,-1)
            for loc in self.agent.environment.windows_locations:
                xw, yw, zw = loc
                if z == zw:
                    possible_moves = self.possible_moves()
                    for pos in possible_moves:
                        dist = np.sqrt((x-xw)**2+(y-yw)**2)
                        if dist < min_dist: best_pos = pos
            return best_pos
        
        def closest_windows(self):
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            grid = self.agent.environment.get_grid(z)
            possible_windows = self.agent.environment.get_windows_loc(z)

            if not possible_windows: return -1

            min_dist = np.sqrt((len(grid))**2 * 2) + 1
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

            min_dist = np.sqrt(2*(len(self.agent.environment.get_grid(0))**2)) + 1
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

            min_dist = np.sqrt(2*(len(self.agent.environment.get_grid(0))**2)) + 1
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
            

            if str(self.agent.jid) not  in self.agent.environment.occupants_loc.keys():
                return False
            occupant_state = self.agent.environment.get_occupant_state(self.agent.jid)
            x1, y1, z = self.agent.environment.get_occupant_loc(self.agent.jid)
        
            if occupant_state == 1:

                #cant move more than 1 step /cell
                if np.sqrt((x-x1)**2) > 1 or np.sqrt((y-y1)**2) > 1:
                    return False
                
            if occupant_state == 0: 
                    return False
            
            return True
            
        def possible_moves(self):
            possible_moves = []
            if str(self.agent.jid) in self.agent.environment.occupants_loc.keys():
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

                x1 = [x-2,x-1, x, x+1,x+2]
                y1 = [y-2,y-1, y, y+1,y+2]
                possible_moves = []
                for i in range(5):
                    for j in range(5):
                        if (i != 0 or j != 0) and (i!= 0 or j != 4) and (i != 4 or j != 0) and (i != 4 or j != 4):
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
                if self.agent.environment.exits_state[(exit[0],exit[1],z)] == 'open':
                    d = np.sqrt((exit[0] - x)**2 + (exit[1] - y)**2)
                    if d<dist:
                        dist = d
            if dist >= np.sqrt((len(grid))**2 *2)+1:
                #no exits 
                # search for closest stairs
                for stairs in self.agent.environment.get_stairs_loc(z):
                    if z != 0:
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
            #x,y,_ = self.agent.environment.get_occupant_loc(self.agent.jid)
            #possible_moves = self.astar_possible_moves(x,y)
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
            floor = self.agent.environment.get_grid(chosen_z)
            #print(floor)
            
            #sself.agent.environment.update_occupant_position(self.agent.jid, x, y, chosen_z)#desce as escadas fora do tempo
            x1 = [x-1, x, x+1]
            y1 = [y-1, y, y+1]

            possible_moves = []
            for i in range(3):
                for j in range(3):
                    if (x==x1[i] and y==y1[j]):
                        pass
                    elif self.is_possible_move(x1[i],y1[j], floor):
                        possible_moves.append((x1[i], y1[j], chosen_z))

            #retorna locais onde possa ficar 
            return possible_moves


        #------------------------------------BOB-WAS-HERE------------------------------------#


        def astar_possible_moves(self,x,y):
            _,_,z = self.agent.environment.get_occupant_loc(self.agent.jid)
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
                    #if (i != 0 or j != 0) and (i!= 0 or j != 4) and (i != 4 or j != 0) and (i != 4 or j != 4):
                        if self.is_possible_move(x1[i],y1[j], grid_z):
                            possible_moves.append([x1[i], y1[j]])

            return possible_moves
        
        def find_path(self, target):
            """
            Finds a path to the target using A*.
            returns what it thinks is the best path

            used after defining clossest exit, 
            if no path foiund, go to next closest exit
            until no exit 
            after just run from fire
            
            make it so that they only jump if told so
            else sudoku igs

            h = dist até target
            g = quantidade de movimentos usados 
            f = g + h
            
            
            [[1,5,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,0,1,1,1,1,1,0,0,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,1,1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1,0,0,0,1,1],
            [1,1,0,0,0,0,0,0,0,0,1,1],
            [1,0,0,0,0,0,0,0,0,0,0,0],
            [1,0,1,1,1,1,1,0,0,0,(x,y),1],
            [1,1,1,1,1,1,1,1,1,1,1,1]]       ->testar com cenario específico apenas um occ e sem incêndio, 
                                                ativar só a emergência
            
            """
            
            open_set = []
            x, y, _ = self.environment.get_occupant_loc(self.agent.jid)
            position = [x, y]
            heapq.heappush(open_set, (0, position))  # Priority queue with (cost, position)
            came_from = {}
            g_score = {position: 0}
            f_score = {position: self.heuristic(position, target)}

            while open_set:
                _, current = heapq.heappop(open_set)

                # Target reached
                if current == target:  
                    #o occ guarda o caminho q quer fazer 
                    path = self.reconstruct_path(came_from, current)
                    return path[0] if path else None  



                x, y = current
                neighbors = self.astar_possible_moves(x, y) #where he can walk to(they are poss moves)
                for nx, ny in neighbors:
                    tentative_g_score = g_score[current] + 1
                    if tentative_g_score < g_score.get((nx, ny), float('inf')):
                        came_from[[nx, ny]] = current
                        g_score[[nx, ny]] = tentative_g_score
                        f_score[[nx, ny]] = tentative_g_score + self.heuristic([nx, ny], target)

                        # Avoid duplicates in the open_set
                        if [nx, ny] not in f_score:
                            heapq.heappush(open_set, (f_score[[nx, ny]], [nx, ny]))

            return None  # No path found

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


        #------------------------------------BOB-WAS-HERE------------------------------------#


            




    
    
