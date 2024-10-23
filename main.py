from environment import Environment
from agents import occupant_agnt, er_agnt, bms_agnt
import spade
import asyncio

async def main():
    # Create and initialize the environment
    environment = Environment()

    #Start 5 occupant agents
    occupants = []
    for i in range(5):
        occupant_agent = occupant_agnt.OccupantAgent(f"occupant{i}@localhost", "password", environment)
        occupants.append(occupant_agent)
        await occupant_agent.start(auto_register=True)
    print("\n")
    await asyncio.sleep(1)


    # Start the Building Agent
    building_agent = bms_agnt.BMSAgent("building@localhost", "password", environment)
    await building_agent.start(auto_register=True)
    print("\n")




if __name__ == "__main__":
    spade.run(main())