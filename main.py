from agents.occupant_agent import OccupantAgent
from agents.building_agent import BuildingAgent
from agents.emergency_responder_agent import EmergencyResponderAgent
import time
import asyncio
import threading
import user_interface

async def start_agents():
    
    # Start the Building Agent
    building_agent = BuildingAgent("building@localhost", "password")
    await building_agent.start(auto_register=True)
    

    # Start 5 Occupant Agents
    occupants = []
    for i in range(5):
        occupant_agent = OccupantAgent(f"occupant{i}@localhost", "password")
        occupants.append(occupant_agent)
        await occupant_agent.start(auto_register=True)
    

    #Start 3 Responder Agents
    #responders = []
    #for i in range(3):
        #responder_agent = EmergencyResponderAgent(f"responder{i}@localhost", "password")
        #responders.append(responder_agent)
        #await responder_agent.start(auto_register=True)
      

    print("All agents are running...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping agents...")
        #building_agent.stop()
        for occupant in occupants:
            occupant.stop()
        #responder_agent.stop()

def run_spade_agents():
    asyncio.run(start_agents())

if __name__ == "__main__":
    #threading allows multiple tasks to run concurrently within the same program
    # 1- managing the agents' lyfecycle
    # 2- ruuning user interface
    agent_thread = threading.Thread(target=run_spade_agents)
    agent_thread.start()

    #Start User Interface
    root = user_interface.tk.Tk()
    root.title("Emergency Evacuation System")
    evacuation_ui = user_interface.EvacuationUI(root, grid_size=10)
    root.mainloop()

    #stop the agents thread once the UI is closed
    agent_thread.join()