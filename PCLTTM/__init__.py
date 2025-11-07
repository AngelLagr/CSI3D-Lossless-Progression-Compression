from .retriangulator import Retriangulator
from .data_structures import * 
from typing import List, Tuple, Optional, Set, Dict, override
from .mesh import MeshTopology
from . import constants
# ============================================================================
# ALGORITHM IMPLEMENTATION
# ============================================================================

class PCLTTM():
    """
    Implements the valence-driven conquest algorithm from Alliez-Desbrun 2001.
    """

    def __init__(self):
        self.mesh: Optional[MeshTopology] = None

    def parse_file(self, file: str):
        self.mesh = MeshTopology.from_obj_file(file)
    
    def compress(self):
        if self.mesh is None:
            raise ValueError("Mesh not loaded. Please parse a file first.")

        initial_gate = self.mesh.get_initial_gate()


        ######################################################
        # DECIMATION PHASE
        ######################################################
        FiFo = [initial_gate]
        while FiFo != []:
            print("Remaining gates in FiFo:", len(FiFo))
            current_gate = FiFo.pop(0)
            left_vertex, right_vertex = current_gate.edge
            valence = current_gate.front_vertex.valence()
            print(valence,current_gate.front_vertex.state_flag(), self.mesh.can_remove_vertex(current_gate.front_vertex)) 
            if (valence in [3,4,5,6]) and (current_gate.front_vertex.state_flag() == constants.StateFlag.Free) and (self.mesh.can_remove_vertex(current_gate.front_vertex)):
                patch = self.mesh.get_patch(current_gate).output_gates()

                # conquer all the vertexes in the patch
                print(len(patch), "gates in the patch")
                for gate in patch:
                    (v1, v2) = gate.edge
                    self.mesh.set_vertex_state(v1, constants.StateFlag.Conquered)
                    self.mesh.set_vertex_state(v2, constants.StateFlag.Conquered)
                    FiFo.append(gate)
     
                Retriangulator.retriangulate(self.mesh, valence, current_gate, patch.oriented_vertices())

        ######################################################
        # CLEANING PHASE
        ######################################################
        FiFo = [initial_gate]
        while FiFo != []:
            print("Remaining gates in FiFo:", len(FiFo))

            current_gate = FiFo.pop(0)
            left_vertex, right_vertex = current_gate.edge
            valence = current_gate.front_vertex.valence()
            if (valence in [3]) and (current_gate.front_vertex.state_flag() == constants.StateFlag.Free) and (self.mesh.can_remove_vertex(current_gate.front_vertex)):
                # todo
                patch = self.mesh.get_patch(current_gate).output_gates()

                # conquer all the vertexes in the patch
                for gate in patch:
                    (v1, v2) = gate.edge
                    self.mesh.set_vertex_state(v1, constants.StateFlag.Conquered)
                    self.mesh.set_vertex_state(v2, constants.StateFlag.Conquered)
                    FiFo.append(gate)
                
                # todo
                Retriangulator.retriangulate(self.mesh, valence, current_gate, patch.oriented_vertices())


        # for debug just to see the result in the first step
        self.mesh.export_to_obj("output.obj")




                



    
        

