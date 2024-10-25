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

class BMSAgent(Agent):
    def __init__(self, jid, password, environment:Environment):
        super().__init__(jid, password)
        self.environment = environment
        self.current_plan = self.environment.send_plan_to_bms()
    

    async def setup(self):
        print(f"Building Management System Agent starting ...")

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
            await asyncio.sleep(2)
        
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
            #se a divisão inteira num_agents pelo num_floors tiver resto, os agents a mais ficam à espera de info?
            agents_per_floor = num_er_agents // num_floors
            return agents_per_floor
