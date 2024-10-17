# Manages building infrastructure, sends alerts and evacuation information
import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import user_interface as ui

class BuildingAgent(Agent):
    class AlertBehaviour(OneShotBehaviour):
        async def run(self):
            print(f"Building agent {self.agent.name} is sending evacuation alerts...")

    class MonitorExits(CyclicBehaviour):
        async def run(self):
            #The BuildingAgent should periodically send messages to the occupant agents. These messages will contain evacuation instructions (e.g., which exits to use).

            exit_status, exit_location = ui.EvacuationUI.get_exit_status(0)

            for i in range(len(ui.EvacuationUI.occupants_loc)):
                msg = Message(to=f"occupant{i}@localhost")
                if exit_status == 'open':
                    msg.body = f"You can use Exit 0 at location {exit_location}. It is open."               
                else:
                    msg.body = "Exit 0 is closed. Find an alternative."
                await self.send(msg)


    async def setup(self):
        print(f"Building agent {self.name} starting...")

        alert_behaviour = self.AlertBehaviour()
        self.add_behaviour(alert_behaviour)

        monitor_behaviour = self.MonitorExits(period=5)
        self.add_behaviour(monitor_behaviour)

        #self.emergency_scenario = 'fire'

        #manage_building = self.ManageBuildingBehaviour()
        #self.add_behaviour(manage_building)

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

    

        

