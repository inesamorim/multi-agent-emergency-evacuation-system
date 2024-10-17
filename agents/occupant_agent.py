# Represents occupants who follow evacuation instructions

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import asyncio
from user_interface import EvacuationUI
import numpy as np


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
                    dist = np.sqrt((x-x1)**2 + (y-y1)**2)
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



    def __init__(self, body_state):
        '''
        body_state -> defines movement
        disabled
        0-> cant use stairs, slow, no movment in dangerous situations
        1-> can use stairs, slow (affected by hazerd, disabled with paramedics)
        2-> can use stairs, normal speed
        proposta como easter egg
        3-> consegue saltar por buracos entre pisos/ tem formato de pato
        '''
        self.body_state = body_state


    '''
    poss_moves
    preff_moves
    '''
    async def ploss(self, x, y, grid_sz):

        if grid_sz[x, y] == 5: return False
        if x<0 or y<0: return False
        if x>=len(grid_sz[0]) or y>len(grid_sz):return False
        
        pers_state = self.body_state
        x1, y1, z = EvacuationUI.occupants_loc[self.name]

        if pers_state == 0:
            if np.sqrt((x-x1)**2) == 2 or np.sqrt((y-y1)**2) == 2:return False

        return True
    
    async def poss_moves(self)-> list:
        x, y, z = EvacuationUI.occupants_loc[self.name]
        grid_sz = EvacuationUI.grid_size #no futuro alterar para BMS.get_floor(z) ->return grid

        ''' 
        1->portas 
        2->janelas
        3->escadas
        4->pessoas
        5->obstáculos

        [[0, 0, 0, 0, 0, 0,]
        [1, 0, 0, 0, 0, 0,]
        [0, 0, 3, 0, 0, 0,]
        [0, 0, 0, 0, 2, 2,]
        [0, 0, 0, 0, 2, 0,]
        [0, 0, 0, 0, 1, 0]]
        '''
        x1 = [x-2, x-1, x, x+1, x+1]
        y1 = [y-2, y-1, y, y+1, y+2]
        poss_moves = []
        for i in range(5):
            for j in range(5):
                if ploss(x1[i], y1[i], grid_sz): poss_moves.append([x1[i], y1[i]])
        return poss_moves
    
    async def get_diss(self, move):
        #exits_loc = função q devolve a loc das escadas e janelas(se andar 0) do andar(z)

        #return dist
        pass
    
    async def preff_moves(self):
        poss_moves = poss_moves()
        list_of_dist = [0 for i in range(len(poss_moves))]
        #ver dist de cada poss à saida mais proxima e adequar priority list dessa forma
        for i in range(len(poss_moves)):
            list_of_dist[i] = get_diss(poss_moves[i])
        pass
       


    async def setup(self):
        print(f"Occupant agent {self.name} starting ...")

        self.exits = {"Exit 1": 'open',
                      "Exit 2": 'open'}
        self.elevator = 'on'


        evac_behaviour = self.EvacuateBehaviour()
        self.add_behaviour(evac_behaviour)





    ###
