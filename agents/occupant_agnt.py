from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import numpy as np
from spade.message import Message


class OccupantAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
        self.floor = self.environment.get_occupant_loc(self.jid)[2]
        ##hellf
        self.helf = MAX_HEALF        

    async def setup(self):
        #só é invocada por trigger
        class ReceiveWarning(OneShotBehaviour):
            async def run(self):
                msg = await self.receive(timeout=10)
                if msg:
                    print(f"Occupant {self.agent.jid} received message: {msg.body}")
                else: 
                    print(f"Occupant {self.agent.jid} did not receive any messages")
                

        #occorre normalmente está constantemente a ser feita
        class EvacuateBehaviour(CyclicBehaviour):  
            async def run(self):
                await asyncio.sleep(3)
                exit_loc = self.closest_exit()
                if exit_loc == -1:
                    print(f"Occupant {self.agent.jid} has no available exits in its floor. Searching for another option\n")

                else:
                    z = self.agent.environment.get_occupant_loc(self.agent.jid)[2]
                    x, y = exit_loc
                    if self.agent.environment.get_grid(z)[x][y] == 5:
                        print("There is an obstacle in the closest exit.\n")
                    elif self.agent.environment.get_grid(z)[x][y] == 6:
                        if self.agent.environment.get_exit_status((x,y,z)) == 'open':
                            print(f"Exit in {(x,y,z)} is open,occupant {self.agent.jid} moving into it...\n")
                            self.agent.environment.update_occupant_position(agent_id=self.agent.jid, new_x=x, new_y=y, new_z=z)
                        else:
                            print(f"Exit in {(x,y,z)} is closed. Occupant {self.agent.jid} is finding another options...")

                await asyncio.sleep(2)
            
            def closest_exit(self):
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
                if grid[x][y] == 5:
                    #obstaculo
                    return False
                
                if x < 0 or y < 0 or x >= len(grid[0]) or y >= len(grid):
                    #fora da grid
                    return False
                
                occupant_state = self.agent.environment.get_occupant_state(self.agent.jid)
                x1, y1, z = self.agent.environment.get_occupant_loc(self.agent.jid)
                if occupant_state == 0:
                    #cant move more than 1 step /cell
                    if np.sqrt((x-x1)**2) == 2 or np.sqrt((y-y1)**2) == 2:
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
                '''

                x1 = [x-2, x-1, x, x+1, x+1]
                y1 = [y-2, y-1, y, y+1, y+2]
                possible_moves = []
                for i in range(5):
                    for j in range(5):
                        if self.is_possible_move(x1[i],y1[j], grid_z):
                            possible_moves.append(x1[i], y1[j])
                return possible_moves

            def get_distance(self, x, y):
                #exits_loc = função q devolve a loc das escadas e janelas(se andar 0) do andar(z)
                z = self.floor
                dist = len(self.environmment.get_grid(z)) + 1
                for exit in self.environment.get_exit_loc(z):
                    d = np.sqrt((exit[0] - x)**2 + (exit[1] - y)**2)
                    if d<dist: dist = d
                return dist
            
            def prefered_moves(self):
                possible_moves = self.possible_moves()
                distances = [0 for i in range(len(possible_moves))]

                #ver dist de cada poss à saida mais proxima e adequar priority list dessa forma
                for i in range(len(possible_moves)):
                    distances[i] = self.get_distance(possible_moves[i][0], possible_moves[i][1])

                sorted_coordinates = [[coord for coord, dist in sorted(zip(possible_moves, distances), key=lambda x: x[1])]]
                return sorted_coordinates


        print(f"Occupant {self.jid} starting ...")
        self.add_behaviour(ReceiveWarning())
        self.add_behaviour(EvacuateBehaviour())
        
