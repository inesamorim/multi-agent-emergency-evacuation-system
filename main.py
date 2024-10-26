from environment import Environment
from agents import occupant_agnt, er_agnt, bms_agnt
import spade
import asyncio

async def main():
    # Create and initialize the environment
    environment = Environment()
    
    async def enqueue_agent(agent):
        await agent.start(auto_register=True)
        await environment.queue.put(agent)

    async def enqueue_behaviour(agent, behaviour):
        await environment.queue.put((agent, behaviour))

    #Start 5 occupant agents
    occupants = []
    num_occupants = len(environment.get_all_occupants_loc())
    for i in range(num_occupants):
        occupant_agent = occupant_agnt.OccupantAgent(f"occupant{i}@localhost", "password", environment)
        occupants.append(occupant_agent)
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

    # Send warnings to occupants
    for occupant_agent in occupants:
        occupant_agent.add_behaviour(occupant_agent.ReceiveWarning())
        await asyncio.sleep(0.5)
    building_agent.add_behaviour(building_agent.SendWarnings())

    # Receive building plan
    building_agent.add_behaviour(building_agent.ReceiveBuildingPlan(period=3))

    # Evacuate occupants
    for occupant_agent in occupants:
        occupant_agent.add_behaviour(occupant_agent.EvacuateBehaviour())
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    spade.run(main())