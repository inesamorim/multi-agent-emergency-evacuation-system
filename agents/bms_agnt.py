from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.behaviour import PeriodicBehaviour
from spade.behaviour import Event
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from environment import Environment
import time
import numpy as np
import copy
import ast
from spade import run
from datetime import datetime

class BMSAgent(Agent):
    def __init__(self, jid, password, environment:Environment):
        super().__init__(jid, password)
        self.environment = environment
        self.current_plan = self.environment.send_plan_to_bms()
    

    async def setup(self):
        print(f"Building Management System Agent starting ...")
        await asyncio.sleep(0.5)

    class SendWarnings(OneShotBehaviour):
            async def run(self):
                print("[BMS] Sending evacuation instructions to occupants...")
                await self.send_warning_to_occupants()

                #TODO: send warnings to er agents

            async def send_warning_to_occupants(self):
                for i in range(len(self.agent.environment.occupants_loc)):
                    msg = Message(to=f"occupant{i}@localhost")
                    msg.set_metadata("performative", "inform")
                    msg.body = "[BMS] There is an emergency. Please find the closest exit.\n"

                    await self.send(msg) 
        
    class CallER(OneShotBehaviour):
        async def run(self):
            print("[BMS] Alerting ER Agents...")
            await self.call_er_agents()
        
        async def call_er_agents(self):
            for i in range(len(self.agent.environment.er_loc)):
                msg = Message(to=f"eragent{i}@localhost")
                msg.set_metadata("performative", "inform")
                msg.body = "[BMS] There is an emergency. Please come to the building."

                await self.send(msg)

    class ReceiveBuildingPlan(CyclicBehaviour):
        async def run(self):
            self.current_plan = self.receive_building_plan()
            print(f"BMS is receiving updated building plan...")
            #for floor in range(len(self.current_plan)):
                #print(f"Plan of floor {floor}:\n")
                #print(self.current_plan[floor])
                #print("\n")
            await asyncio.sleep(3)

        def receive_building_plan(self):
            return self.agent.environment.send_plan_to_bms()
        
 
#------------------------------------------------------------------------------------------------------------#
#-----------------------------------------------Not Used-----------------------------------------------------#
#------------------------------------------------------------------------------------------------------------#
       
    class Path_Throu_Building(CyclicBehaviour):

        async def run(self):
            ''' 
            
            andtes dos ER chegarem, se n houver saidas
            se o andar do rés do chão tiver janelas, a mais perto das escadas e longe do fogo 
            é tornada numa saída para os occ

            quando a saida for bloqueada
            BMS diz quais são os andares n afetados(menos afetados) -> occ dirigem-se para andar mais prox
            func safe_floors()

            quando ER chegar chamar choose_floor (demora dist ao rés do chão segundos a ser ativada)
            
            '''
            ...

        async def poss_path(self, z_inical, z_final, stair_pos):
            '''
            def duable(self, initial_pos, destination)-> Boolean
            se as escadas estiverem bem e não houver fogo numa dist inf a 2
            '''
            c = 1 if z_final>z_inical else -1 

            for i in range(z_inical, z_final+1, c):
                grid = self.agent.environment.get_grid(i)
                if grid[stair_pos[0]][stair_pos[1]] == 5:#tornou-se fogo
                    return False
            return True
        
        
        async def classify_floor(self, floor):
            ''' 
            definition of emergency state of floor
            se <10%             -> safe
            se >= 10%           -> danger low
            se >= 45%           -> danger high
            se >= 87% em chamas -> no go  (ver se vale a pena dar save pela janela, 
                                            só o fazer se area >= 81,
                                            ou occ está "protegido por obstáculos")
            '''
            grid = self.agent.environment.get_grid(floor)
            rows, cols = len(grid), len(grid[0])
            c = count = 0
            for i in rows:
                for j in cols:
                    c += 1
                    if grid[i][j] == 5:
                        if self.agent.environment.obstacles[str(i, j)] == 'fire':
                            count += 1

            if count==c: self.agent.environment.dead_floors.append[floor]
            return count*100//c

        async def occ_in_floor(self):
            '''
            counts n of occ per floor given higher priority to those with less movement
            '''
            #para cada occ, ver em q andar está e somar 
            #type[-1, 0, 1, 2] vall atribuid [0, 7, 4.5, 1]
            value = {-1: 0, 0: 7, 1: 4.5, 2: 1}
            count = [0 for i in range(len(self.agent.environment.get_num_of_floors()))]
            all_occ_loc = self.agent.environment.get_all_occupants_loc() #{id: x, y, z}
            for id, loc in all_occ_loc:
                count[loc[2]] += value[self.agent.environment.get_occupant_state(id)]
                
            return count
        
        async def occ_non_destruct(self):
            '''
            per floor returns the nº of occupants per area non destructed
            '''
            occ_count=self.occ_in_floor()
            f_count = [0 for i in range(self.agent.environment.get_num_of_floors())]

            for z in range(self.agent.environment.get_num_of_floors()):
                f_count[z] = [z,occ_count[z]/(1-self.classify_floor(z))]

            return f_count
        
        async def safe_floors(self):
            '''
            retorna os andares mais seguros ordenados por nível de destruição(no momento em q a função foi chamada)
            '''
            f = []
            for z in range(self.agent.environment.get_num_of_floors()):
                p = self.classify_floor(z)
                if p<45:
                    f.append([z,p])

            return sorted(f, key=lambda x: x[1])
        
        async def choose_floors(self):
            '''
            ver nº mazimo de andares que possam ser salvos simultaneamente 
                -> por cada 15 ER uma janela pode ser aberta
                    (uma ambulância, uma mangueira, um carro escada) 5 Er por cada 

            a janela q eu vou querer abrirvai ser a q têm maior ratio (escadas não são queimadas)
            '''
            #assume q nunca se vai chamar mais ER do q o necessário
            n_windows = (self.agent.environment.get_all_er_locs()%15)+1
            f_count = self.occ_non_destruct() #[z, ratio]
            
            sorted_coords = [occ_f for occ_f in sorted(f_count, key = lambda x: x[1])]

            while n_windows<0:
                if len(self.agent.environment.get_windows_loc(sorted_coords[0][0]))>0:
                    #dizer aos ER para abrirem janela de floor
                    n_windows -= 1
                    sorted_coords=sorted_coords[1:] #remover o 1º elemento da lista
            ...
            
        '''
        se o fogo tiver afetado todas as entradas/saídas possíveis
        ou existirem andares sem acesso direto a saidas(no início antes de ER irem para lá)
        escolher o melhor nº mínimo de janelas para serem transformadas em exits
        e quais as melhores janelas
        '''

        async def call_ER(self):
            occs = self.agent.environmet.get_all_occupants_state()
            prmd = ff = 0
            
            for _, type in occs:
                if type <2 and type>-1:
                    prmd += 1
                ff+=1

            prmd = prmd//6 - int(0.2*prmd//6) +1
            ff = ff//5 - int(0.2*ff//5) +1
            nER = prmd+ff//5 + 5 if prmd+ff//5!=0 else prmd+ff%5
            nER = np.max(nER, self.agent.environmet.get_num_of_floors()*3)

            return int(nER*0.3), int(nER*0.7)+1
    
        async def alternative_exit(self):
            #exits = self.agent.environmet.get_all_exits_loc()
            if len(self.agent.environmet.get_all_exits_loc()) == 0:
                best_floors = self.safest_floors()
                if len(best_floors) == 0:
                    return None
                ...
            ...

        def alocate_responders(self):
            occ_destruct = self.occ_non_destruct() 
            er = self.agent.environment.get_er_type_count() #{1: [id], 2: [id]}
            num_type1_responders = len(er["1"])  #that are yet to be alocated
            num_type2_responders = len(er["2"]) 

            # Step 1: Minimum allocation: 1 of each type per occupied floor
            c = 0

            for floor, _ in enumerate(occ_destruct):
                if num_type1_responders>0 and num_type2_responders>0:
                    er["1"][c].floor_alocated(floor) #retirar id in pos c
                    er["2"][c].floor_alocated(floor)
                    c+=1
                    num_type1_responders -=1
                    num_type2_responders -=1

            # Step 2: Proportional allocation of remaining responders

            sum_occ_destruct = sum(occ_destruct)
            c1 = c2 = c
            if sum_occ_destruct!=0:
                for floor, occ in enumerate(occ_destruct):
                    for i in range(int((occ / sum_occ_destruct) * num_type1_responders)):
                        er["1"][c1].floor_alocated(floor)
                        c1+=1
                        
                    for i in range(int((occ / sum_occ_destruct) * num_type2_responders)):
                        er["1"][c2].floor_alocated(floor)
                        c2+=1
                        

            num_type1_responders -= c1-c
            num_type2_responders -= c2-c

            # Step 3: Round and adjust to match remaining responders

            while num_type1_responders>0 or num_type2_responders>0:
                for floor in range(self.agent.environment.get_num_of_floors()):
                    if num_type1_responders>0:
                        er["1"][c1].floor_alocated(floor)
                        c1+=1
                        num_type1_responders -= 1
                    if num_type2_responders>0:
                        er["1"][c2].floor_alocated(floor)
                        c2+=1
                        num_type2_responders -= 1
            return 
            
