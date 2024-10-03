# Represents occupants who follow evacuation instructions

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import random

class OccupantAgent(Agent):
    class EvacuateBehaviour(CyclicBehaviour):
        async def run(self):
            print(f"Occupant {self.agent.name} is trying to evacuate...")

            if random.random() > 0.2:
                print(f"Occupant {self.agent.name} has moved closer to the exit")

            else: 
                print(f"Occupant {self.agent.name} is blocked and is trying another route")

            await self.sleep(2)

    async def setup(self):
        print(f"Occupant agent {self.name} starting ...")
        evac_behaviour = self.EvacuateBehaviour()
        self.add_behaviour(evac_behaviour)
