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
        class SendWarnings(OneShotBehaviour):
            async def run(self):
                print("Sending evacuation instructions to occupants...")
                await self.send_warning_to_occupants()

                #TODO: send warnings to er agents

            async def send_warning_to_occupants(self):
                for i in range(len(self.agent.environment.occupants_loc)):
                    msg = Message(to=f"occupant{i}@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = "[BMS] There is an emergency. Please find the closest exit.\n"

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

        print(f"Building Management System Agent starting ...")
        self.add_behaviour(SendWarnings())
        self.add_behaviour(ReceiveBuildingPlan())