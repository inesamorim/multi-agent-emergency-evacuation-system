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
        print(f"ER Agent {self.jid} of type {self.type} is starting...")
        await asyncio.sleep(0.5)


    class GoToBuilding(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"ER Agent {self.agent.type} {self.agent.jid} received message from BMS and is coming to the rescue...")
                await asyncio.create_task(self.sleep(30)) #time to get to the building
            else:
                print(f"ER Agent {self.agent.type} {self.agent.jid} did not recieve any messages")
            
        async def sleep(self, time):
            await asyncio.sleep(time)


    class GoToFloor(OneShotBehaviour):
        async def run(self):
            print(f"ER Agent {self.agent.jid} has arrived to the scene")
            msg = await self.receive(timeout=10)
            #msg = "Please go to floor:z"
            if msg:
                msg_received = msg.body
                floor = int(msg_received.split(":")[-1].strip())
                x, y, z = self.agent.environment.get_stair_loc(floor)[0]
                self.agent.environment.update_er_position(self.agent.jid, x,y,z)
                
            else:
                print(f"ER Agent {self.agent.jid} did not receive any information")
        async def sleep(self, time):
            await asyncio.sleep(time)

        
            

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
            self.receive_health_state()
        async def receive_health_state(self):
            msg = await self.receive(timeout=10)
            #msg: "I am: Occupanti@localhost; My Health State is: x"
            if msg:
                print("foo")
                #...