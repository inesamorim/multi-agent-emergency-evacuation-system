from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import random 
import time

class EmergencyResponderAgent(Agent):
    class RespondToEmergenciesBehaviour(CyclicBehaviour):
        async def run(self):
            #Simulating movement and assisting behaviour
            responder_location = random.choice(self.agent.grid_locations)
            print(f"Responder {self.agent.name} is moving to location {responder_location}")

            #Checking for hazards and occupants who need help
            if responder_location in self.agent.hazard_locations:
                print(f"Responder {self.agent.name} is managing a hazard at location {responder_location}")
                self.agent.hazard_locations.remove(responder_location)

            for occupant in self.agent.occupants_needing_help:
                if occupant['location'] == responder_location:
                    print(f"Responder {self.agent.name} is helping {occupant['name']} at location {responder_location}")
                    self.agent.occupants_needing_help.remove(occupant)

            #Sending status update to building management system
            msg = Message(to='building@localhost')
            msg.body = f"Rsponder {self.agent.name} status: Location - {responder_location}, no hazards"
            await self.send(msg)

            await self.agent.sleep(1)

    async def setup(self):
        print(f"Responder agent {self.name} starting...")

        self.grid_locations = [(i,j) for i in range(10) for j in range(10)]
        self.hazard_locations = [(2,2), (4,5)] #example
        self.occupants_needing_help = [{'name': 'occupant0',
                                        'location': (2,2)}] #example
        
        respond_behaviour = self.RespondToEmergenciesBehaviour()
        self.add_behaviour(respond_behaviour)


