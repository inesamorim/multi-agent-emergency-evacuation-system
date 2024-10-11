# Represents occupants who follow evacuation instructions

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import random
import numpy as np
import asyncio
from user_interface import EvacuationUI

class OccupantAgent(Agent):
    class EvacuateBehaviour(CyclicBehaviour):
        ''' 
        estado de emergência constante
        se existir porta -> move to clossest exit
        se não ->  random moove
        '''

        async def clossest_exit(self):
            ''' ver se e quantas saidas existem,
            se não existem, andar aleatóriamente,
            se existem:
            se nada dito em prioridade, ver a mais proxima
            se dada prioridade, ver as mais proximas entre as de prioridade
            '''
            #get poss of ocupant based on name / name==poss na list
            poss_exits = EvacuationUI.exits_locations
            
            ###ver caso não existam saídas(saida==curr_poss ou -1)-> andar aleatóriamente 
            if not poss_exits:return -1

            x, y = EvacuationUI.occupants_loc[self.name] #[x, y]

            #ver prioridade -> mais á frente... :)

            dist = EvacuationUI.grid_size + 1
            i = 0
            p_dist = -1

            for i in range(poss_exits):
                x1 = poss_exits[i][0]
                y1 = poss_exits[i][1]
                if np.sqrt((x-x1)**2 + (y-y1)**2)<dist:
                    dits = np.sqrt((x-x1)**2 + (y-y1)**2)<dist
                    p_dist = i

            return poss_exits[p_dist][0], poss_exits[p_dist][1]
        


        async def run(self):
            ''' 
            se saida-> vai para saida
            se não random
            '''

            if self.clossest_exit()!= -1:
                EvacuationUI.update_agent_position(self.agent.name,self.clossest_exit())

            if self.agent.exits["Exit 1"] == 'closed':
                print(f"{self.agent.name} found Exit 1 clsoed, rerouting to another exit...")

            else:
                print(f"{self.agent.name} is heading to Exit 1")

            if self.agent.elevator == 'off':
                print(f"{self.agent.name} found the elevator off, will try to use stairs")


            await asyncio.sleep(2)


        

    async def setup(self):
        print(f"Occupant agent {self.name} starting ...")

        self.exits = {"Exit 1": 'open',
                      "Exit 2": 'open'}
        self.elevator = 'on'

        
        evac_behaviour = self.EvacuateBehaviour()
        self.add_behaviour(evac_behaviour)

    

    
    
    ###

