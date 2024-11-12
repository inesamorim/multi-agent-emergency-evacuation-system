from environment import Environment
from agents import occupant_agnt, er_agnt, bms_agnt
import spade
import asyncio
from datetime import datetime

async def main():
    # Create and initialize the environment
    environment = Environment(num_floors=2)
    
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

    print(f"All agents created. Starting simulation at {environment.start_time}")


    # Processa a fila de agentes e behaviours em ordem
    while not environment.queue.empty():
        item = await environment.queue.get()
        if isinstance(item, tuple):  # Se for um behaviour
            agent, behaviour = item
            agent.add_behaviour(behaviour)
        else:  # Se for um agente
            agent = item
        environment.queue.task_done()

    # Call ER agents to the scene
    for er_agent in er_agents:
        er_agent.add_behaviour(er_agent.GoToBuilding())
        await asyncio.sleep(0.5)
    building_agent.add_behaviour(building_agent.CallER())
    await asyncio.sleep(0.5)
    

    # Send warnings to occupants
    for occupant_agent in occupants:
        occupant_agent.add_behaviour(occupant_agent.ReceiveWarning())
        await asyncio.sleep(0.5)
    building_agent.add_behaviour(building_agent.SendWarnings())
    await asyncio.sleep(0.5)

    

    # Receive building plan
    building_agent.add_behaviour(building_agent.ReceiveBuildingPlan())

    behaviours = []

    behaviours.append(building_agent.add_behaviour(building_agent.ReceiveBuildingPlan()))
    # Evacuate occupants
    for occupant_agent in occupants:
        behav = occupant_agent.add_behaviour(occupant_agent.EvacuateBehaviour())
        behaviours.append(behav)
        await asyncio.sleep(0.5)


    #Check Health

    
    behaviours.append(building_agent.add_behaviour(building_agent.HelpWithOccupantsRoute()))
    
    #await asyncio.gather(*behaviours)

    while True:
        await asyncio.sleep(100)
    


if __name__ == "__main__":
    spade.container.Container().run(main())
    #asyncio.run(main())