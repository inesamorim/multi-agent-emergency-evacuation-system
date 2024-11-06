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
            for floor in range(len(self.current_plan)):
                print(f"Plan of floor {floor}:\n")
                print(self.current_plan[floor])
                print("\n")
            await asyncio.sleep(3)

        def receive_building_plan(self):
            return self.agent.environment.send_plan_to_bms()
        
        
    class SendERToFloor(OneShotBehaviour):
        async def run(self):
            agents_per_floor = self.distribute_by_floor()
            self.send_info_to_er(agents_per_floor)

        async def send_info_to_er(self, agents_per_floor):
            for i in range(0,len(self.agent.environment.er_loc),agents_per_floor):
                for j in range(i, agents_per_floor):
                    floor = i
                    msg = Message(to=f"eragent{j}@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = f"[BMS] Please go to floor:{floor}"

                    await self.send(msg)

        def distribute_by_floor(self):
            #TODO: se as escadas no andar 'x' estão impedidas por um obstáculo, então os er agents podem apenas ser distribuidos pelos andares anteriores?
            # assumindo que bombeiros passam fogo...
            num_floors = self.agent.environment.get_num_of_floors()
            num_er_agents = len(self.agent.envrionment.get_er_loc())
            #se a divisão inteira de num_agents pelo num_floors tiver resto, os agents a mais ficam à espera de info?
            agents_per_floor = num_er_agents // num_floors
            return agents_per_floor

    class HelpWithOccupantsRoute(CyclicBehaviour):
        async def run(self):
            preferences = {}
            num_occupants = len(self.agent.environment.get_all_occupants_loc())

            print("Waiting for occupants preferences")

            while len(preferences) < num_occupants:
                msg = await self.receive(timeout=10)
                if msg:
                    # Extrai o occupant_id e a lista de preferências da mensagem
                    content = msg.body
                    occupant_id = content.split(";")[0].split(":")[-1].strip()
                    hierarchy_str = content.split(";")[-1].split(":")[-1].strip()
                    hierarchy = ast.literal_eval(hierarchy_str)
            
                    # Armazena a lista de preferências no dicionário
                    preferences[occupant_id] = hierarchy
                    print(f"Preferences of {occupant_id} received: {hierarchy}")
                else:
                    print("Didn't receive any messages")
                    break


            # Verifica se todas as preferências foram recebidas
            if len(preferences) == num_occupants:
                # Faz uma cópia profunda da grid
                grid_copy = copy.deepcopy(self.agent.environment.get_building())
                print("Deep copy created.")

                # Realiza lógica para determinar o próximo movimento com base nas preferências
                await self.process_moves(preferences, grid_copy)
            
            await asyncio.sleep(2)

        async def process_moves(self, preferences, grid_copy):
            print("Processando as preferências dos ocupantes...")
            final_positions = {}
            occupied_positions = set() #keep up with occupied positions

            for occupant_id, hierarchy in preferences.items():
                hierarchy = hierarchy[0]
                #print(f"hierarchy: {hierarchy}")
                for preferred_move in hierarchy:
                    #check if its available
                    if preferred_move not in occupied_positions:
                        final_positions[occupant_id] = preferred_move
                        print(f"New position for {occupant_id}: {preferred_move}")
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
                msg.body = f"Go to new position: {position}"
                print(f"Sending new position {position} to occupant {occupant_id}.")
            
            await self.send(msg)
            
        
        