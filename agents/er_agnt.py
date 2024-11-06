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
            while True:  # Continuously listen for messages
                await self.receive_health_state()
            
        async def receive_health_state(self):
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
                    occ = [health_state, id_part, x, y, z]
                    
                    print("Agent data array:", occ)
                    
                except IndexError as e:
                    print("Failed to parse message. Make sure the message format is correct:", e)
                except ValueError as e:
                    print("Failed to convert data to integers. Check the data format:", e)


