# Manages building infrastructure, sends alerts and evacuation information

from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from spade.message import Message

class BuildingAgent(Agent):
    class AlertBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"Building agent {self.agent.name} is sending evacuation alerts...")

            #add communications later
    class ManageBuildingBehaviour(CyclicBehaviour):
        async def run(self):
            if self.agent.emergency_scenario == 'fire':
                self.agent.close_exit("Exit 1")
                self.agent.switch_off_elevator()
                msg = Message(to="occupant0@localhost")
                msg.body = "Exit 1 is closed, use alternative exits."
                await self.send(msg)
            
            await self.agent.sleep(5)
    
        async def on_end(self):
            print("Building management behaviour ended.")


    async def setup(self):
        print(f"Building agent {self.name} starting...")

        alert_behaviour = self.AlertBehaviour()
        self.add_behaviour(alert_behaviour)

        self.exits = {"Exit 1": 'open',
                      "Exit 2": 'open'}
        self.windows = {"Window 1": 'closed',
                        "Window 2": 'closed'}
        self.elevator = 'on'

        self.emergency_scenario = 'fire'

        manage_building = self.ManageBuildingBehaviour()
        self.add_behaviour(manage_building)

    def open_exit(self, exit_name):
        if exit_name in self.exits:
            self.exists[exit_name] = 'open'
            print(f"Building agent has opened {exit_name}.")

    def close_exit(self, exit_name):
        if exit_name in self.exits:
            self.exits[exit_name] = 'closef'
            print(f"Building agent has opened {exit_name}.")
    
    def switch_off_elevator(self):
        self.elevator = 'off'
        print("Building Agent has switched off the elevator.")

    def switch_on_elevator(self):
        self.elevator = 'on'
        print("Building Agent has switched on the elevator.")

    

        

