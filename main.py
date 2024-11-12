from environment import Environment
from agents import occupant_agnt, er_agnt, bms_agnt
import spade
import asyncio
from datetime import datetime
import threading
from user_interface import start_interface

async def main():
    # Create and initialize the environment
    environment = Environment(num_floors=3, num_occupants=10, num_er=5)

    #start user interface
    #interface_thread = threading.Thread(target=start_interface, args=(environment,))
    #interface_thread.start()
    
    async def enqueue_agent(agent):
        await agent.start(auto_register=True)
        await environment.queue.put(agent)

    #Start 5 occupant agents
    occupants = []
    num_occupants = len(environment.get_all_occupants_loc())
    for i in range(num_occupants):
        occupant_agent = occupant_agnt.OccupantAgent(f"occupant{i}@localhost", "password", environment)
        occupants.append(occupant_agent)
        #occupants.append(occupant_agent)
        await enqueue_agent(occupant_agent)

    

    #Start ER Agents 
    er_agents = []
    num_er = len(environment.get_all_er_locs())
    for i in range(num_er):
        if i % 2 == 0:
            type = 'firefighter'
        else:
            type = 'paramedic'
        er_agent = er_agnt.ERAgent(f"eragent{i}@localhost", "password", environment, type)
        er_agents.append(er_agent)
        await enqueue_agent(er_agent)


     # Start the Building Agent
    building_agent = bms_agnt.BMSAgent("building@localhost", "password", environment)
    await enqueue_agent(building_agent)
    print("\n")
    
    print("#####################################################################")
    print(f"All agents created. Starting simulation at {environment.start_time}")
    print("#####################################################################")

    print("\n")

    # Call ER agents to the scene
    for er_agent in er_agents:
        er_agent.add_behaviour(er_agent.GoToBuilding())
        #await asyncio.sleep(0.5)
    building_agent.add_behaviour(building_agent.CallER())
    #await asyncio.sleep(0.5)

    # Send warnings to occupants
    for occupant_agent in occupants:
        occupant_agent.add_behaviour(occupant_agent.ReceiveWarning())
        #await asyncio.sleep(0.5)
    building_agent.add_behaviour(building_agent.SendWarnings())
    #await asyncio.sleep(0.5)

    # Receive building plan
    building_agent.add_behaviour(building_agent.ReceiveBuildingPlan())

    behaviours = []
    # Evacuate occupants
    for occupant_agent in occupants:
        behav = occupant_agent.add_behaviour(occupant_agent.EvacuateBehaviour())
        behaviours.append(behav)
        #await asyncio.sleep(0.5)

    behaviours.append(building_agent.add_behaviour(building_agent.ReceiveBuildingPlan()))
    behaviours.append(building_agent.add_behaviour(building_agent.HelpWithOccupantsRoute()))


    #TODO: Check Health
    for er_agent in er_agents:
        while(er_agent.busy):
            await asyncio.sleep(5)
        if er_agent.environment.get_er_role(er_agent.jid):
            #print("foo =====================================================")
            behav_2 = er_agent.add_behaviour(er_agent.ReceiveHealthState())
            behaviours.append(behav_2)
            
    for occupant_agent in occupants:
        behav = occupant_agent.add_behaviour(occupant_agent.HOFAH())
        behaviours.append(behav)
    for er_agent in er_agents:
        while(er_agent.busy):
            await asyncio.sleep(5)
            print("Waiting....")
        print("Not Waiting...")
        print(er_agent.environment.get_er_role(er_agent.jid))
        if er_agent.environment.get_er_role(er_agent.jid):
            #print("foo =====================================================")
            behav = er_agent.add_behaviour(er_agent.CheckForHealthState())
            behaviours.append(behav)
            

    
    
    
    #await asyncio.gather(*behaviours)

    while True:
        await asyncio.sleep(100)
    


if __name__ == "__main__":
    spade.container.Container().run(main())
    #asyncio.run(main())