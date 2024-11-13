from environment import Environment
from agents import occupant_agnt, er_agnt, bms_agnt
import spade
import asyncio
from datetime import datetime
import threading
from user_interface import start_interface
import random

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

    async def make_disasters():
        disaster = random.choice(environment.obstacles_type)
        positions = environment.get_available_positions()
        if disaster == 'smoke':
            #everyone can pass through, we don't add it to the grid but we know where it is
            positions = environment.get_all_positions()
            pos = random.choice(positions)
            environment.obstacles[(pos)] = disaster
            print("#############################################")
            print(f"There is smoke in position {pos}")
            print("#############################################")
        elif disaster == 'fire':
            #firefighters can passthough, we add it to the grid
            #TODO: fogo alastra-se?
            pos = random.choice(positions)
            environment.obstacles[(pos)] = disaster
            environment.building[pos[2]][pos[0]][pos[1]] = 5 #fire
            print("#############################################")
            print(f"There is a fire starting in position {pos}")
            print("#############################################")
        else:
            #no one can pass through, we add it to the grid
            pos = random.choice(positions)
            environment.obstacles[(pos)] = disaster
            environment.building[pos[2]][pos[0]][pos[1]] = 8 #obstacle
            print("#############################################")
            print(f"There is an obstacle in position {pos}")
            print("#############################################")

    async def manage_disasters():
        #se existe fogo num certo sítio, ele vai alastrar-se e matar quem estiver nos lugares para onde se alastrou
        to_add = []
        to_pop = []
        for disaster in environment.obstacles.items():
            pos = disaster[0]
            type = disaster[1]
            print(disaster)
            if type == 'fire':
                x = pos[0]
                y = pos[1]
                z = pos[2]
                x1 = [x-1, x+1]
                y1 = [y-1, y-2]
                for i in range(len(x1)):
                    for j in range(len(y1)):
                        new_pos = (i,j,z)
                        print(f"The fire as now expanded to position {new_pos}")
                        if environment.building[z][i][j] == 4:
                            #occupant dies
                            for agent_id in environment.occupants_loc.keys():
                                if environment.occupants_loc[str(agent_id)] == new_pos:
                                    to_pop.append(str(agent_id))
                                for agent in occupants:
                                    if agent.jid == agent_id:
                                        agent.stop()
                environment.building[z][i][j] = 5 # fire
                to_add.append(new_pos)
        for i in to_add:
            environment.obstacles[i] = 'fire'
        for i in to_pop:
            environment.occupants_loc.pop(i)
            environment.occupants_dead += 1
            print(f"Occupant {i} is dead due to a fire")


        

    #start an emergency
    await make_disasters()

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
            #print("Waiting....")
        #print("Not Waiting...")
        #print(er_agent.environment.get_er_role(er_agent.jid))
        if er_agent.environment.get_er_role(er_agent.jid):
            #print("foo =====================================================")
            behav = er_agent.add_behaviour(er_agent.CheckForHealthState())
            behaviours.append(behav)
            

    
    
    
    #await asyncio.gather(*behaviours)

    while True:
        await manage_disasters()
        await make_disasters()
        await asyncio.sleep(10)
    


if __name__ == "__main__":
    spade.container.Container().run(main())
    #asyncio.run(main())