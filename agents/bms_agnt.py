from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import Event
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from environment import Environment
import time
import numpy as np
import copy
import ast
from spade import run
from datetime import datetime

class BMSAgent(Agent):
    def __init__(self, jid, password, environment:Environment):
        super().__init__(jid, password)
        self.environment = environment
        self.current_plan = self.environment.send_plan_to_bms()
    

    async def setup(self):
        print(f"Building Management System Agent starting ...")
        await asyncio.sleep(0.5)

    class SendWarnings(OneShotBehaviour):
            async def run(self):
                print("[BMS] Sending evacuation instructions to occupants...")
                await self.send_warning_to_occupants()

                #TODO: send warnings to er agents

            async def send_warning_to_occupants(self):
                for i in range(len(self.agent.environment.occupants_loc)):
                    msg = Message(to=f"occupant{i}@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = "[BMS] There is an emergency. Please find the closest exit.\n"

                    await self.send(msg) 
        
    class CallER(OneShotBehaviour):
        async def run(self):
            print("[BMS] Alerting ER Agents...")
            await self.call_er_agents()
        
        async def call_er_agents(self):
            for i in range(len(self.agent.environment.er_loc)):
                msg = Message(to=f"eragent{i}@localhost")
                msg.set_metadata("performative", "inform")
                msg.body = "[BMS] There is an emergency. Please come to the building."

                await self.send(msg)

    class ReceiveBuildingPlan(CyclicBehaviour):
        async def run(self):
            self.current_plan = self.receive_building_plan()
            print(f"BMS is receiving updated building plan...")
            #for floor in range(len(self.current_plan)):
                #print(f"Plan of floor {floor}:\n")
                #print(self.current_plan[floor])
                #print("\n")
            await asyncio.sleep(3)

        def receive_building_plan(self):
            return self.agent.environment.send_plan_to_bms()
        
        

    class HelpWithOccupantsRoute(CyclicBehaviour):
        async def run(self):
            preferences = {}
            num_occupants = len(self.agent.environment.get_all_occupants_loc())

            if(num_occupants == 0):
                print("All occupants left safely or are dead")
                end_time = datetime.now()
                print("###################### STATS ######################")
                print(f"Evacuation took {end_time - self.agent.environment.start_time}")
                print(f"Occupants Saved: {self.agent.environment.occupants_saved}")
                print(f"Dead Occupants: {self.agent.environment.occupants_dead}")
                #await stop_agents()

            while len(preferences) < num_occupants:
                msg = await self.receive(timeout=5)
                if msg:
                    # Extrai o occupant_id e a lista de preferências da mensagem
                    content = msg.body
                    occupant_id = content.split(";")[0].split(":")[-1].strip()
                    hierarchy_str = content.split(";")[-1].split(":")[-1].strip()
                    hierarchy = ast.literal_eval(hierarchy_str)
            
                    # Armazena a lista de preferências no dicionário
                    preferences[occupant_id] = hierarchy
                else:
                    print("BMS didn't receive any messages")
                    break


            
            # Faz uma cópia profunda da grid
            grid_copy = copy.deepcopy(self.agent.environment.get_building())

            # Realiza lógica para determinar o próximo movimento com base nas preferências
            await self.process_moves(preferences, grid_copy)
        
            await asyncio.sleep(2)

        async def process_moves(self, preferences, grid_copy):

            final_positions = {}
            occupied_positions = set() #keep up with occupied positions

            for occupant_id, hierarchy in preferences.items():
                hierarchy = hierarchy[0]
                #print(f"hierarchy: {hierarchy}")
                for preferred_move in hierarchy:
                    #check if its available
                    if preferred_move not in occupied_positions:
                        final_positions[occupant_id] = preferred_move
                        occupied_positions.add(preferred_move)
                        break
                    else:
                        final_positions[occupant_id] = None
            
            #Send new positions to occupants
            for occupant_id, position in final_positions.items():
                await self.send_move_instruction(occupant_id, position)

        async def send_move_instruction(self, occupant_id, position):
            msg = Message(to=occupant_id)
            msg.set_metadata("performative", "inform")
            if position:
                msg.body = f"new position: {position}"

            
            await self.send(msg)
            
        
        