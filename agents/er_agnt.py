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
    def __init__(self, jid, password, environment:Environment, type):
        super().__init__(jid, password)
        self.environment = environment
        self.type = type

    async def setup(self):
        class GoToBuilding(OneShotBehaviour):
            async def run(self):
                msg = await self.receive(timeout=10)
                if msg:
                    print(f"ER Agent {self.type} {self.agent.jid} received message from BMS and is coming to the rescue...")
                    task_1 = asyncio.create_task(self.go_to_building()) #continue with other beahviours
                    task_1
                else:
                    print(f"ER Agent {self.type} {self.agent.jid} did not recieve any messages")

            async def go_to_building(self):
                await asyncio.sleep(30)
                print(f"ER Agent {self.agent.jid} has arrived to the scene")

        class GoToFloor(OneShotBehaviour):
            async def run(self):
                msg = await self.receive(timeout=10)
                #msg = "Please go to floor:z"
                if msg:
                    msg_received = msg.body
                    floor = msg_received.split(":")[-1].strip()
                    x, y, z = self.agent.environment.get_stair_loc(floor)[0]
                    self.agent.environment.update_er_position(self.agent.jid, x,y,z)
                else:
                    print(f"ER Agent {self.agent.jid} did not receive any information")
                

        class CheckForHealthState(CyclicBehaviour):
            async def run(self):
                print("Asking Occupants for their state...")
                await self.ask_health_state()
            
            async def ask_health_state(self):
                for i in range(len(self.agent.environment.get_all_ocuppants_loc())):
                    msg = Message(to=f"occupant{i}@localhost")
                    msg.set_metadata("performative", "informative")
                    msg.body("[ER] Please give me information on your health state")

                    await self.send(msg)

        print(f"ER Agent {self.agent.jid} of type {self.type} is starting...")
        self.add_behaviour(GoToBuilding())
        self.add_behaviour(CheckForHealthState())
        self.add_behaviour(GoToFloor())