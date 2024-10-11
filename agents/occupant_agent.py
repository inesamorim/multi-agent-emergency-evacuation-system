# Represents occupants who follow evacuation instructions

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import asyncio


class OccupantAgent(Agent):
    class EvacuateBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.exits["Exit 1"] == 'closed':
                print(f"{self.agent.name} found Exit 1 clsoed, rerouting to another exit...")

            else:
                print(f"{self.agent.name} is heading to Exit 1")

            if self.agent.elevator == 'off':
                print(f"{self.agent.name} found the elevator off, will try to use stairs")

            await asyncio.sleep(2)

    class ReceiveAlertBehaviour(CyclicBehaviour):
        async def run(self):
            #Receive a message
            msg = await self.receive(timeout=10)
            if msg:
                print(f"Occupant {self.agent.name} received alert: {msg.body}")
                #TODO: add reaction to this msg


    async def setup(self):
        print(f"Occupant agent {self.name} starting ...")

        self.exits = {"Exit 1": 'open',
                      "Exit 2": 'open'}
        self.elevator = 'on'

        
        evac_behaviour = self.EvacuateBehaviour()
        self.add_behaviour(evac_behaviour)

        receive_alert_behaviour = self.ReceiveAlertBehaviour()
        receive_template = Template(sender="building@localhost")
        self.add_behaviour(receive_alert_behaviour, receive_template)