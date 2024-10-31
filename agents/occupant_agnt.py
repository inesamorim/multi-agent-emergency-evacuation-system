from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import numpy as np
from spade.message import Message

MAX_HEALTH = 1000   #sempre q num quadrado com fumo, sofre dano

class OccupantAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
        self.floor = self.environment.get_occupant_loc(self.jid)[2]
        ##hellf
        self.elf = self.environment.get_occupant_state(self.jid)

        self.elf_bar = MAX_HEALTH    #quando chegar a 0 -> muda de nível   
    

    async def setup(self):
        print(f"Occupant {self.jid} starting ...")
        await asyncio.sleep(0.5)
    
    class ReceiveWarning(OneShotBehaviour):
            async def run(self):
                msg = await self.receive(timeout=10)
                if msg:
                    print(f"Occupant {self.agent.jid} received message: {msg.body}")
                else: 
                    print(f"Occupant {self.agent.jid} did not receive any messages")

    class LeaveFloor(OneShotBehaviour):
        #quando no quadrado 4(escadas) muda de andar
        def leave(self, cb: bool=False): #cima baixo  0 desce 1 sobe
            x, y, z = self.environment.get_occupant_loc(self.agent.jid)[2]
    
            #ver onde é q as escadas calham
            pass



    class  HOFAH(CyclicBehaviour):
        #recebe msg asking for health state
        async def run(self):
            holding_out_for_a_hero = await self.receive(timeout = 15)
            if holding_out_for_a_hero and (self.agent.elf > -1): #not dead
                print(f"Occupant {self.agent.jid} received message: {holding_out_for_a_hero.body}")

                #send info to ER agent on that floor
                await self.send_info_to_er()
                        
            else: 
                print(f"Occupant {self.agent.jid} did not receive any messages or is dead :(")
            
        async def send_info_to_er(self):
            x, y, z = self.agent.environment.get_occupant_loc(self.agent.jid)
            er_agents_locs = self.agent.environment.get_all_er_locs()
            for i in range(len(er_agents_locs)):
                loc = er_agents_locs[i]
                if loc[2] == z:
                    #o primeiro er agent nesse floor recebe msg
                    msg = Message(to=f"eragent{i}@localhost")
                    msg.set_metadata("performative", "informative")
                    msg.body = f"[Occupant] I am: {self.agent.id}; My position is: {x,y,z}; My health state is: {self.agent.elf}"

                    await self.send(msg)

    class LifeBar(CyclicBehaviour):
        '''if quadrado em q está == fumo
                self.elf_bar -= 1'''
        async def run(self):
            if self.elf_bar == 0:
                if self.elf == 0:
                    self.elf_bar = float("inf")
                else:
                    self.elf_bar = MAX_HEALTH
                self.elf = self.elf - 1
                    

            
    #occorre normalmente está constantemente a ser feita
    class EvacuateBehaviour(CyclicBehaviour):  
        async def run(self):
            print(f"Occupant {self.agent.jid} is trying to find exit")
            exit_loc = self.closest_exit()
            print(exit_loc)
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
                        #pessoa tem que desaparecer
                        #self.agent.environment.update_occupant_position(agent_id=self.agent.jid, new_x=x, new_y=y, new_z=z)
                        self.agent.environment.person_is_safe(self.agent.jid)
                        print(f"Occupant {self.agent.jid} left the building safely\n")
                        await self.agent.stop()
                    else:
                        print(f"Exit in {(x,y,z)} is closed. Occupant {self.agent.jid} is finding another options...")

            await asyncio.sleep(2)
        
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

    
    
