from agents.occupant_agent import OccupantAgent
from agents.building_agent import BuildingAgent
import time

if __name__ == "__main__":
    # Start the Building Agent
    building_agent = BuildingAgent("building@localhost", "password")
    future = building_agent.start()
    future.result()

    # Start 5 Occupant Agents
    occupants = []
    for i in range(5):
        occupant_agent = OccupantAgent(f"occupant{i}@localhost", "password")
        occupants.append(occupant_agent)
        future = occupant_agent.start()
        future.result()

    print("All agents are running...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping agents...")
        building_agent.stop()
        for occupant in occupants:
            occupant.stop()