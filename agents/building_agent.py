# Manages building infrastructure, sends alerts and evacuation information

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

class BuildingAgent(Agent):
    class AlertBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"Building agent {self.agent.name} is sending evacuation alerts...")

            #add communications later

    async def setup(self):
        print(f"Building agent {self.name} starting...")
        alert_behaviour = self.AlertBehaviour()
        self.add_behaviour(alert_behaviour)

        

