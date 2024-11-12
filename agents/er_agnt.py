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


class ERAgent(Agent):
    def __init__(self, jid, password, environment:Environment, type, hellping=False):
        super().__init__(jid, password)
        self.environment = environment
        self.type = type
        ###### BOB WAS HERE ######
        self.helping = hellping #se está a transportar alguém
        self.occupants = {} # a dictionary, e.g., {id: [health, x, y, z]}
        self.floor = self.environment.send_plan_to_bms()  #ou recebem o andar onde estão ou recebem a grid toda
        self.busy = False
        self.building = self.environment.get_building()  #ou recebem o andar onde estão ou recebem a grid toda
        self.occupant_info = None

    async def setup(self):
        print(f"ER Agent {self.jid} of type {self.type} is starting...")
        await asyncio.sleep(0.5)


    class GoToBuilding(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"ER Agent {self.agent.type} {self.agent.jid} received message from BMS and is coming to the rescue...")
                await asyncio.sleep(10)
                print("#####################################################")
                print(f"ER Agent {self.agent.jid} has arrived to the scene")
            
            await asyncio.sleep(1)
            #print("ER Agents are now distributing themselves through the floors...")
            if str(self.agent.jid) == "eragent0@localhost":
                agents_per_floor = self.distribute_by_floor()
                self.distribution(agents_per_floor)

        def distribution(self, agents_per_floor):
            z = 0
            for i in range(0,self.agent.environment.num_er,agents_per_floor):
                #print(f"i: {i}")
                for j in range(i, i+agents_per_floor):
                    #print(f"j: {j}")
                    er_id = f"eragent{j}@localhost"
                    if i == j:
                        self.agent.environment.update_er_role(er_id, True)
                        print(f"ER agent {er_id} is assigned captain of floor {z}")
                    floor = z
                    pos = self.possible_pos(floor)
                    print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                    self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                z += 1

        def distribute_by_floor(self):
            #TODO: se as escadas no andar 'x' estão impedidas por um obstáculo, então os er agents podem apenas ser distribuidos pelos andares anteriores?
            # assumindo que bombeiros passam fogo...
            num_floors = self.agent.environment.num_floors
            num_er_agents = self.agent.environment.num_er
            #print(num_floors, num_er_agents)
            #se a divisão inteira de num_agents pelo num_floors tiver resto, os agents a mais ficam à espera de info?
            agents_per_floor = num_er_agents // num_floors
            #print(agents_per_floor)
            return agents_per_floor
        
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



    class CheckForHealthState(CyclicBehaviour):
        async def run(self):
            await self.ask_health_state()

        async def ask_health_state(self):
            num_occupants = len(self.agent.environment.get_all_occupants_loc())
            for i in range(num_occupants):
                msg = Message(to=f"occupant{i}@localhost")
                msg.set_metadata("performative", "informative")
                msg.body = "[ER] Please give me information on your health state"
                asyncio.create_task(self.sleep(10))

                await self.send(msg)
        async def sleep(self, time):
            await asyncio.sleep(time)


    class ReceiveHealthState(CyclicBehaviour):
        async def run(self):
            to_help_list = []
            while True:  # Continuously listen for messages
                await self.receive_health_state(to_help_list)
                #[id, healf, x, y, z]


        async def receive_health_state(self, to_help_list):
            msg = await self.receive(timeout=10)  # Wait for a message with a 10-second timeout

            if msg:
                # Assuming msg.body contains the message text
                content = msg.body  # or msg.content, depending on the message library

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

                    print("Agent data array:", occ)
                    to_help_list.append(occ)

                    if health_state==1: #agent é curável
                        cure_behaviour = self.Cure(occ)
                        self.agent.add_behaviour(cure_behaviour)

                except IndexError as e:
                    print("Failed to parse message. Make sure the message format is correct:", e)
                except ValueError as e:
                    print("Failed to convert data to integers. Check the data format:", e)

        class Cure(OneShotBehaviour):
            def __init__(self, agent_data):
                super().__init__()
                self.agent_data=agent_data
                self.to_help_list=to_help_list

            async def run(self):
                agent_id, health, x, y, z = self.agent_data
                print(f"Attempting to cure agent {agent_id} with health state {health}")

                self.agent_data[1]=0 #curado, health_state=0 (?)
                print(f"Agent {agent_id} has been cured")

                if self.agent_data in self.to_help_list:
                    self.to_help_list.remove(self.agent_data)

    class SaveThroughWindow(CyclicBehaviour):
        def __init__(self, agent_data, exits_available, stairs_available):
            super().__init__()
            self.agent_data = agent_data
            self.exits_available = exits_available   ##
            self.stairs_available = stairs_available ##

        async def run(self):
            agent_id, health, x, y, z = self.agent_data
            if health == 0 and not self.exits_available and not self.stairs_available:
                print(f"Agent {agent_id} was saved through the window")

                self.kill()
            else:
                print(f"Agent {agent_id} is waiting for an available exit or stairs")
                await self.agent.async_sleep(2)


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

            if (grid[x][y]!=0)or(grid[x][y]!=3):
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
