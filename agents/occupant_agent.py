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
        self.grid = EvacuationUI.get_original_grid(EvacuationUI.occupants_loc[self.name][2])
        self.existing_exits = EvacuationUI.get_stairs_loc(EvacuationUI.occupants_loc[self.name][2])
        self.grid_size = len(self.grid) * len(self.grid[0])



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
                if self.ploss(x1[i], y1[i], grid_sz): poss_moves.append([x1[i], y1[i]])
        return poss_moves
    
    async def get_diss(self, x, y):
        #exits_loc = função q devolve a loc das escadas e janelas(se andar 0) do andar(z)
        dist = self.grid_size + 1
        for exit in self.existing_exits:
            d = np.sqrt((exit[0] - x)**2 + (exit[1] - y)**2)
            if d<dist: dist = d
        return dist


    '''
    preff_mover
    gets the list of possible mooves exp:[(x1,y1), (x2, y2), (x3, y3)]
    get_diss -> para uma dada coordenada exp(x1, y1) ela dá a distância á saída mais próxima
    [2, 4.5, 0]
    [(x1,y1), (x2, y2), (x3, y3)]
    e vai returnar
    [(x3, y3), (x1, y1), (x2, y2)]

    '''
    
    async def preff_moves(self):
        poss_moves = poss_moves()
        list_of_dist = [0 for i in range(len(poss_moves))]
        #ver dist de cada poss à saida mais proxima e adequar priority list dessa forma
        for i in range(len(poss_moves)):
            list_of_dist[i] = self.get_diss(poss_moves[i][0], poss_moves[i][1])

        sorted_coordinates = [coord for coord, dist in sorted(zip(poss_moves, list_of_dist), key=lambda x: x[1])]
        return sorted_coordinates 
       


    async def setup(self):
        print(f"Occupant agent {self.name} starting ...")

        self.exits = {"Exit 1": 'open',
                      "Exit 2": 'open'}
        self.elevator = 'on'


        evac_behaviour = self.EvacuateBehaviour()
        self.add_behaviour(evac_behaviour)





    ###
