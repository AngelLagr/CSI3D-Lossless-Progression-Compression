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
        self.state_flags = dict() # Hash(Vertex) -> State flag (e.g., CONQUERED, TO_BE_CONQUERED, FREE)
        self.retriangulator = Retriangulator()
        

    def parse_file(self, file: str):
        self.mesh = MeshTopology.from_obj_file(file)
        for v in self.mesh.get_vertices():
            self.state_flags[v] = StateFlag.Free
    
    def compress(self):
        if self.mesh is None:
            raise ValueError("Mesh not loaded. Please parse a file first.")

        initial_gate = self.mesh.get_random_gate()

        self.retriangulator.retriangulation_tags[initial_gate.edge[0]] = RetriangulationTag.Plus
        self.retriangulator.retriangulation_tags[initial_gate.edge[1]] = RetriangulationTag.Minus

        ######################################################
        # DECIMATION PHASE
        ######################################################
        FiFo = [initial_gate]
        while FiFo != []:
            print("Remaining gates in FiFo:", len(FiFo))
            current_gate = FiFo.pop(0)
            left_vertex, right_vertex = current_gate.edge
            center_vertex = current_gate.front_vertex
            valence = center_vertex.valence()
            vertex_state = self.state_flags[current_gate.front_vertex]

            print(valence, vertex_state, self.mesh.can_remove_vertex(center_vertex)) 
            if (valence in [3,4,5,6]) and (vertex_state == constants.StateFlag.Free) and (self.mesh.can_remove_vertex(center_vertex)):
                patch = self.mesh.get_patch(center_vertex)

                # conquer all the vertexes in the patch
                out_gates = patch.output_gates(current_gate.edge)
                print(len(out_gates), "gates in the patch")
                for gate in out_gates:
                    (v1, v2) = gate.edge
                    self.state_flags[v1] = constants.StateFlag.Conquered
                    self.state_flags[v2] = constants.StateFlag.Conquered
                    FiFo.append(gate)

                patch_vertices = patch.surrounding_vertices(current_gate.edge)
                self.retriangulator.retriangulate(self.mesh, valence, current_gate, patch_vertices)

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
                    self.set_vertex_state(v1, constants.StateFlag.Conquered)
                    self.set_vertex_state(v2, constants.StateFlag.Conquered)
                    FiFo.append(gate)
                
                # todo
                Retriangulator.retriangulate(self.mesh, valence, current_gate, patch.oriented_vertices())


        # for debug just to see the result in the first step
        self.mesh.export_to_obj("output.obj")


                



    
        

