from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.behaviour import OneShotBehaviour
from spade.behaviour import Event
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from environment import Environment
import time
import numpy as np


class ERAgent(Agent):
    def __init__(self, jid, password, environment:Environment, type):
        super().__init__(jid, password)
        self.environment = environment
        self.type = type
        ###### BOB WAS HERE ######
        self.helping = False #se está a transportar alguém
        self.occupants = {} # a dictionary, e.g., {id: [health, x, y, z]}
        self.busy = True
        self.building = self.environment.get_building()  #ou recebem o andar onde estão ou recebem a grid toda
        #self.occupant_info = None
        self.floor_alocated = -1


    async def add_patient(self, patient_inf):
        ''' to add to list of attendence'''
        #patient_inf -> [id, type, x, y, z]
        if not(patient_inf[0] in self.occupants):
            self.occupants[patient_inf[0]] = patient_inf[1:]

    async def modify_other_agent_occ(self, other_agent_id, patient_inf):
        """
        Modify another agent's self.occupants if the agent exists.
        Adds the occ info to the list for the specified `occ_id`.
        """
        # Retrieve the other agent using the registry
        other_agent = Agent.agents_registry.get(other_agent_id)

        # Check if the other agent exists
        if other_agent:
            if not(patient_inf[0] in other_agent.occupants):
                other_agent.occupants[patient_inf[0]] = [patient_inf[1:]]  # Create a new entry if occ_id is new
                print(f" {other_agent_id} will try to treat occ: {other_agent.occ}")
        else:
            print(f"Agent with ID {other_agent_id} not found.")

    async def setup(self):
        print(f"ER Agent {self.jid} of type {self.type} is starting...")
        await asyncio.sleep(0.5)


    class GoToBuilding(OneShotBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                print(f"ER Agent {self.agent.type} {self.agent.jid} received message from BMS and is coming to the rescue...")
                await asyncio.sleep(10)
                print("#####################################################")
                print(f"ER Agent {self.agent.jid} has arrived to the scene")
                self.agent.busy = False

            await asyncio.sleep(1)
            #print("ER Agents are now distributing themselves through the floors...")
            if str(self.agent.jid) == "eragent0@localhost":
                agents_per_floor, resto = self.distribute_by_floor()
                self.distribution(agents_per_floor, resto)

        def distribution(self, agents_per_floor, resto):
            z = 0
            for i in range(0,self.agent.environment.num_er,agents_per_floor):
                z1 = 0
                if z >= self.agent.environment.num_floors:
                    for j in range(i, i+resto):
                        er_id = f"eragent{j}@localhost"
                        floor = z1
                        self.agent.floor_alocated = floor
                        pos = self.possible_pos(floor)
                        print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                        self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                    z1 += 1
                    break
                #print(f"i: {i}")
                for j in range(i, i+agents_per_floor):
                    #print(f"j: {j}")
                    er_id = f"eragent{j}@localhost"
                    if i == j:
                        self.agent.environment.update_er_role(er_id, True)
                        #print(self.agent.environment.er_role[str(er_id)])
                        print(f"ER agent {er_id} is assigned captain of floor {z}")
                    floor = z
                    self.agent.floor_alocated = floor
                    pos = self.possible_pos(floor)
                    print(f"ER agent {er_id} is heading to position {pos[0],pos[1],floor}")
                    self.agent.environment.update_er_position(er_id, pos[0], pos[1], floor)
                z += 1

        def distribute_by_floor(self):
            #TODO: se as escadas no andar 'x' estão impedidas por um obstáculo, então os er agents podem apenas ser distribuidos pelos andares anteriores?
            # assumindo que bombeiros passam fogo...
            num_floors = self.agent.environment.num_floors
            num_er_agents = self.agent.environment.num_er
            #print(num_floors, num_er_agents)
            #se a divisão inteira de num_agents pelo num_floors tiver resto, os agents a mais ficam à espera de info?
            agents_per_floor = num_er_agents // num_floors
            resto = num_er_agents % num_floors
            #print(agents_per_floor)
            return agents_per_floor, resto

        def possible_pos(self, floor):
            grid = self.agent.environment.get_grid(floor)
            x, y = self.agent.environment.get_stairs_loc(floor)[0]
            x1 = [x-1, x+1]
            y1 = [y-1, y+1]
            for i in x1:
                for j in y1:
                    if grid[i][j] == 0:
                        return i,j
            return 0



    class CheckForHealthState(CyclicBehaviour):
        async def run(self):
            while(not self.agent.busy):
                await asyncio.sleep(1)
            await self.ask_health_state()
            await asyncio.sleep(10)

        async def ask_health_state(self):
            num_occupants = self.agent.environment.num_occupants
            for i in range(num_occupants):
                id = f"occupant{i}@localhost"
                if str(id) in self.agent.environment.occupants_loc.keys():
                    print(f"ER Agent {self.agent.jid} ks sending message to {id}")
                    msg = Message(to=f"occupant{i}@localhost")
                    msg.set_metadata("performative", "informative")
                    msg.body = "[ER] Please give me information on your health state"

                    await self.send(msg)


    class ReceiveHealthState(CyclicBehaviour):
        async def run(self):
            to_help_list = []
            while True:  # Continuously listen for messages
                await self.receive_health_state(to_help_list)
                #[id, healf, x, y, z]


        async def receive_health_state(self, to_help_list):
            '''
            se occ tiver no pick da health, não pede ajuda, só foge
            '''
            msg = await self.receive(timeout=10)  # Wait for a message with a 10-second timeout

            if msg:
                # Assuming msg.body contains the message text
                content = msg.body  # or msg.content, depending on the message library

                # Split the message by semicolons to isolate sections
                parts = content.split(";")

                try:
                    # Extract `id`
                    id_part = parts[0].split(":")[1].strip()

                    # Extract `position` (x, y, z) - splitting by `:` and `,`
                    position_part = parts[1].split(":")[1].strip()
                    x, y, z = map(int, position_part.strip("()").split(","))

                    # Extract `health state`
                    health_state_part = parts[2].split(":")[1].strip()
                    health_state = int(health_state_part)

                    # Create the array with agent data
                    occ = [id_part, health_state, x, y, z]

                    print(f"Agent data Received by ER Agent:\n - Id: {occ[0]};\n - Health State: {occ[1]};\n - Position:{occ[2],occ[3],occ[4]}")
                    to_help_list.append(occ)

                    if health_state==1: #agent é curável
                        cure_behaviour = self.Cure(occ, to_help_list)
                        self.agent.add_behaviour(cure_behaviour)

                except IndexError as e:
                    print("Failed to parse message. Make sure the message format is correct:", e)
                except ValueError as e:
                    print("Failed to convert data to integers. Check the data format:", e)



    class ToSaveOrNotToSave(OneShotBehaviour):
        # se paramed -> chegará beira da pessoa e invocar cura(dependedndo do estado demora x tempo)
        async def stagnation(self):
            """
            invocar quando er type==2 chega á beira do occ indicado
            Sets occ.elf_bar of the target agent to infinity.

            Parameters:
                occ (list): A list containing [occ_id, type, x, y, z]
            """
            if self.type == 1:
                # Assuming that occ_id can be used to access the agent instance
                occ_id = next(iter(self.occupants)) #o 1º id 
                            
                
                if occ_id is not None:
                    if self.occupants[occ_id][0] != -1:
                        #ainda se pode salvar 
                        timm = [6, 4, 2] #tempo de salvar proporcional ao nível do occ
                        await asyncio.sleep(self.occupants[occ_id][0])

                        # Set elf_bar of the target agent to infinity
                        occ_id.white_ribons()
                        print(f"Set elf_bar of agent {occ_id} to infinity.")

                        #remove form list to_save
                else:
                    print(f"Agent with id {occ_id} not found or dead.")

                self.occupants.pop(occ_id)#remover do dic


        # se ff -> o occ já foi visto por um médico(não sofre dano ao longo do tempo)
        async def clear_path(self, vetor):
            '''
            se houver um problema de dimenções pequenas eles podem fazer com que ele desapareça
            tem q ser no msm andar

            a função é chamada quando se encontra fogo no caminho 

            recebe o vetor da direção, e vê 7 casas à frente e só apaga o fogo se houver pelo menos 
            um quadrado não em chamas(apaga enguanto passa)
            '''
            #vetor = [1, -1] exemplo 
            x, y, z = self.agent.environment.get_er_loc(self.agent.jid)
            can = 1
            while [x+can*vetor[0], y+can*vetor[1], z] in self.agent.environment.obstacles[x+can*vetor[0], y+can*vetor[1], z]:
                can+=1
            if can!=7:
                self.make_wave(vetor)

        async def make_wave(self, vector):

            x, y, z = self.agent.environment.get_er_loc(self.agent.jid)

            can = 1
            while [x+can*vector[0], y+can*vector[1], z] in self.agent.environment.obstacles[x+can*vector[0], y+can*vector[1], z]:
                can+=1
                self.agent.environment.obstacles.pop(x+can*vector[0], y+can*vector[1], z)

            pass

        async def get_best_exit_rout(self):
            '''
            1-º se os andares entre o q está e a saída + proxima estiverem maus ou bons
            2-º é possível, no andar onde está chegar ás escadas/saida
            4-º qual é a janela acessível mais prox
            ask BMS to see if can easly exit building(the floors belloy are in danger)
            if not a good idea and no exterior stairs, use window
            '''
            pass


    class SaveThroughWindow(OneShotBehaviour):
        async def run(self):
            agent_id, health, x, y, z = self.agent_data

            if not self.exits_available and not self.stairs_available:
                print(f"Agent {agent_id} is preparing to save through the window...")

                #tentar encontrar janela acessível
                window_position = await self.find_accessible_window(x, y, z)
                if window_position:
                    print(f"Agent {agent_id} found an accessible window at {window_position}.")
                    await self.perform_save(agent_id, window_position)

                else:
                    print(f"No accessible windows found. Waiting for an exit or stairs.")
                    await self.agent.async_sleep(2)
            else:
                print(f"Agent {agent_id} is waiting for an available exit or stairs.")
                await self.agent.async_sleep(2)

        async def find_accessible_window(self, x, y, z):
            windows = self.agent.environment.windows_locations
            for window in windows:
                wx, wy = window
                if self.is_window_accessible(wx, wy, x, y):
                    return (wx, wy, z)
            return None

        def is_window_accessible(self, wx, wy, x, y):
            distance = ((wx - x) ** 2 + (wy - y) ** 2) ** 0.5
            return distance <= 1  #janela acessível se distância<=1..

        async def perform_save(self, agent_id, window_position):
            print(f"Agent {agent_id} is saving through the window at {window_position}...")
            await asyncio.sleep(3)
            print(f"Agent {agent_id} successfully saved the occupant through the window")
            self.kill()


    class AbductionOfOcc(OneShotBehaviour):

        ''' se houver um grupo de pessoas é fornecido antecipadamente por ??? dada uma lista de prioridade e
        por ordem cada ER vai buscar a pessoa q lhe foi referide'''

        async def can_hellp(self):
            #if is already helping or can help
            return not self.helping


        async def fuse(self, occupant_id):
            ''' se houver uma pessoa a 1 quadrado de distância ela é "acolhida" pelo ER que vai carregar o seu id '''

            # Check if the occupant exists in the occupants dictionary
            if occupant_id not in self.occupants:
                print(f"Occupant with ID {occupant_id} not found.")
                return

            self.helping = True

            # Retrieve occupant's info and print or store it as needed
            self.occupant_info = self.occupants[occupant_id]
            print("Abducting occupant:", self.occupant_info)

            # Update grid (e.g., setting position to `None` if using a 2D array or removing the key in a dict)
            self.environment.update_occupant_position(occupant_id, -1, -1, -1) #tentar assumir q está fora da grid

            # Optionally, remove occupant from the occupants dictionary
            del self.occupants[occupant_id]
            print(f"Occupant {occupant_id} removed from the occupants list.")


        ############################################################################
        ############################################################################
        ############################################################################


        async def poss_drop(self,x, y, grid):
            if x < 0 or y < 0 or x >= len(grid[0]) or y >= len(grid[0]):
                #fora da grid
                return False

            if (grid[x][y]!=0)or(grid[x][y]!=3):
                #obstaculo
                return False

            return True


        async def where_to_drop(self):
            x, y, z = self.agent.environment.get_er_loc(self.agent.jid)
            x1 = [x-1,x,x+1]
            y1 = [y-1,y,y+1]
            grid =  self.agent.environment.get_grid(z)

            for i in range(3):
                for j in range(3):
                    if self.poss_drop(x1[i],y1[j], grid):
                        return x1[i], y1[j], z

            return -1

        async def releace_hostege(self):
            #quando em segurança liberta a pessoa
            #se a pessoa está a 0 só quando na exit é q é dropada
            #se 1 quando numa área determinada como não afetada (DEC)
            #vai ter de procurar o sítio mais prox para dar drop

            # get_exit_loc(self,floor)
            # get_er_loc(self, er_id)
            x, y, z = self.agent.environment.get_er_loc(self.agent.jid)
            if not([x,y] in self.agent.environment.get_exit_loc(z)):
                #dropping action occurs faster than moving
                if self.where_to_drop() == -1:
                    return -1
                x1, y1, z1 = self.where_to_drop()
                self.environment.update_occupant_position(self.occupant_info, x1, y1, z1)

            #else deu drop na saída poss de occ não altera
            self.helping = False



    #to create a cap, to remove a cap, to comunicate t cap, to order non cap

    class KarenOfFloor(CyclicBehaviour):
        '''
        numa primeira fase cada ER é mandado para uma poss(guardar o ocal de salvamento?)
        o cap guarda a équipa de salvamento(todos os ER alocados para o andar)

        chama pelos occ
        recebe list de occ
        divide équipa presente para salvar occ
        vê se necessita de ajuda ou se tem a mais
        convoca para outros ER ou BMS se necessita de mais pessoas ou se pode dar
        unc de trocar de andar um ER (recive, send)
        tem func
        '''
        
        def __init__(self):
            super().__init__()
            self.can_give = {1: [], 2:[]}


        async def run(self):

            # Check if self.cap from the outer ER class is True
            if self.er_role(self.agent.jid):
                # Perform actions only if cap is True
                print("KarenOfFloor is active and performing tasks.")

                #continuamente 2 em 2 seg obter pessoas e ER da équipa
                #só saem da équipa com transfer
                #CheckForHealthState, ReceiveHealthState

                #team = {id: type}
                #to_save = (sempre q ff estejam a tratar do paciente/ele morra isto é alterado)
                '''
                can_give guarda a quantidade/id  e type de ER q podem ser descartados
                se houver algum outro cap a pedir por + ER é visto por grau de dis sendo quem está em andares
                de cima usado como forma de desempatar quando em msm dist

                criar função para aceitar troca(dizer a ER id que ele pertence a andar z_new)
                '''


            else:
                print("KarenOfFloor is inactive due to cap being False.")


        async def get_team(self):
            team = []
            _, _, z = self.agent.environment.get_er_loc(self.agent.jid)
            for agent in self.agent.environment.get_all_er_types():
                if agent.floor_alocated == z:
                    team.append(agent.id, agent.type)
            
            return team

        async def trafg_ER_to(self, p_in_need, ff_in_need, cap_in_need, id):
            ''' 
            enquanto puder transferir, transfere para o piso necessário
            '''
            if str(id) == self.agent.jid:
                #altera vall para onde er_id foi alocado
                #se get_team for constantemente atualizada não necessita de trafg_ER_from()
                #paramed
                _, _, z = self.agent.environment.get_er_loc(cap_in_need)
                while p_in_need>0 and len(self.can_give[1])>0:
                    id_team_member = self.can_give[1][0]
                    self.can_give[1].pop()
                    id_team_member.agent.floor_alocated = z
                    p_in_need -= 1

                #ff
                while p_in_need>0 and len(self.can_give[1])>0:
                    id_team_member = self.can_give[2][0]
                    self.can_give[2].pop()
                    id_team_member.agent.floor_alocated = z
                    ff_in_need -= 1

            ''' 
            se = 0 já está o prob resolvido
            se != continua a pedir aos mais prox
            se for a todos e nada é acrescentada a urgência para BMS se urgência >= z/2 -> são pedidos reforços  
            '''
            return p_in_need, ff_in_need


        def get_order_for_loors(self, pos):
            # Create a list of tuples (distance, index, element) for each element in lst
            #z_tot = self.agent.environment.num_floors()
            lst = [i for i in range(self.agent.environment.num_floors())]

            elements_with_distance = [
                (abs(i - pos), i, lst[i]) for i in range(len(lst))
            ]
            
            # Sort by distance, and in case of tie, by index
            elements_with_distance.sort(key=lambda x: (x[0], x[1]))

            # Extract the sorted elements only (ignoring distance and index)
            reordered_list = [element for _, _, element in elements_with_distance if _ != pos]

            return reordered_list


        async def call_for_suport(self, p_in_need, ff_in_need):
            ''' 
            ir por andares
            obter agentes do andar 
            ver o cap e mandar-lhe a msg
            '''
            z = self.agent.environment.er_loc[self.agent.ijd][2]
            zzz = self.get_order_for_loors()
            for z in zzz:
                agents_f = self.agent.environment.get_er_in_floor(z)
                for agent in agents_f:
                    if self.agent.environment.er_role[agent]:
                        p_in_need, ff_in_need = self.trafg_ER_to(self, p_in_need, ff_in_need, self.agen.jid, id)
                if p_in_need == 0 and ff_in_need == 0:
                    return -1
            return 1 #não conseguiu, ainda necessita de ajuda

        async def get_n_of(self, team, len_to_save):
            '''
            ver quantos menmbros da eq são paramed e quantos são ff

            se valores diff dos esperados gardar as alterações

            '''
            n_paramed = []
            n_ff = []
            for id in team:
                if team[id] == 2: n_paramed+=1
                if team[id] == 1: n_ff+=1

            '''
                        neste caso, pedir por ajuda
            -> paramédicos     type:1     n/ner >=7.5
            -> ff              type:2     n/ner >=5.5

            neste caso criar lista de possíveis transferÊncias
            -> paramédicos     type:1     n/ner <=3.5
            -> ff              type:2     n/ner <=1.5


            '''

            #paramed
            if len_to_save/n_paramed<=3.5:
                for id, type_ in team.items():
                    if type_ == 1:  
                        self.can_give[1].append(id)
                        #self.can_give.append([id, type_]) 
                        if len_to_save / n_paramed > 3.5: 
                            break  
            
            elif len_to_save/n_paramed>=7.5:
                p_in_need = 0
                for id, type_ in team.items():
                    if type_ == 1:  
                        p_in_need+=1
                        if len_to_save / n_paramed < 7.5: 
                            break

            #ff
            if len_to_save/n_ff<=1.5:
                for id, type_ in team.items():
                    if type_ == 2:  
                        self.can_give[2].append(id)
                        if len_to_save / n_ff > 1.5:  
                            break 

            elif len_to_save/n_paramed>=5.5:
                #in need
                ff_in_need = 0
                for id, type_ in team.items():
                    if type_ == 1:  
                        ff_in_need+=1
                        if len_to_save / n_paramed < 5.5: 
                            break

 
            if p_in_need>0 or ff_in_need>0:
                self.call_for_suport(p_in_need, ff_in_need) #manda ms a pedir pelo nº de pessoas q necessita


            return n_paramed, n_ff

        async def its_hero_time(self, team, to_save):
            '''
            usando a lista de pessoas  e os ER do andar
            (chamada sempre q é notado alterações de nº de ER ou DEC causa mt estrago)

            to_save = [[id, healf, x, y, z], [id, healf, x, y, z], [id, healf, x, y, z]]
            ordered by healf draws by dist
            team = {id: type}

            a pessoa(occ) pode morrer entretanto, se mt perto do -1 ignora ou, quando for ver ignorar pk está morto
            '''

            n_paramd, n_ff = self.get_n_of(team, len(to_save))
            n_p = n_paramd
            n_f = n_ff
            for id in team:
                if team[id] == 2:
                    n_p -= 1
                    for i in range(n_p, len(to_save), n_paramd):
                        self.modify_other_agent_occ(id, to_save[i])


                #se so(ainda por criar) deixar de ser membro da team trocal elif para else
                elif team[id] == 1:
                    n_f -= 1
                    for i in range(n_f, len(to_save), n_ff):
                        self.modify_other_agent_occ(id, to_save[i])


            #self.occupants = {} # a dictionary, e.g., {id: [health, x, y, z]}
