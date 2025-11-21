from typing import List, Optional, Dict, Set, Tuple

from PCLTTM.data_structures.face import Face

from .retriangulator import Retriangulator
from .data_structures import Vertex, Gate
from .mesh import MeshTopology
from .data_structures.constants import StateFlag, RetriangulationTag


class PCLTTM:
    """
    Implements the valence-driven conquest algorithm from Alliez-Desbrun 2001.
    """

    def __init__(self):
        self.mesh: Optional[MeshTopology] = None
        # Hash(Vertex) -> StateFlag (Free, Conquered, ...)
        self.state_flags: Dict[Vertex, StateFlag] = {}
        self.retriangulator = Retriangulator()

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------

    def set_vertex_state(self, v: Vertex, state: StateFlag) -> None:
        self.state_flags[v] = state

    # ----------------------------------------------------------------------
    # Mesh loading
    # ----------------------------------------------------------------------

    def parse_file(self, file: str) -> None:
        """
        Parse an OBJ/OBJA file and initialize the mesh and states.
        """
        self.mesh = MeshTopology.from_obj_file(file)
        for v in self.mesh.get_vertices():
            self.state_flags[v] = StateFlag.Free
            # default retriangulation tag
            self.retriangulator.retriangulation_tags[v] = RetriangulationTag.Default

    # ----------------------------------------------------------------------
    # Main compression routine
    # ----------------------------------------------------------------------

    def __initial_gate_for_crude_sphere_4(self) -> Gate:
        initial_left_vertex = Vertex((6, 0, 3), self.mesh)
        initial_right_vertex = Vertex((0, 6, 3), self.mesh)
        initial_front_vertex = Vertex((0, 0, 10), self.mesh)
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)

    def __initial_gate_for_test(self) -> Gate:
        initial_left_vertex = Vertex((3,0,0), self.mesh)
        initial_right_vertex = Vertex((4,2,0), self.mesh)
        initial_front_vertex = Vertex((2,2,0), self.mesh)
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)

    def __initial_gate_for_crude_sphere_5(self) -> Gate:
        initial_left_vertex = Vertex((6, 0, 3), self.mesh)
        initial_right_vertex = Vertex((2, 6, 3), self.mesh)
        initial_front_vertex = Vertex((0, 0, 10), self.mesh)
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)

    def initial_gate_for_crude_sphere_6(self) -> Gate:
        initial_left_vertex = Vertex((6, 0, 3), self.mesh)
        initial_right_vertex = Vertex((3, 5, 3), self.mesh)
        initial_front_vertex = Vertex((0, 0, 10), self.mesh)
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)

   # Conditions where a vertex cannot be removed:
    # 1. Vertex whose removal leads to violation of the manifold property of the mesh, 
    #       i.e. when the corresponding remeshing process would create already existing edges.
    # 2. Vertex whose removal leads to a normal flipping locally.
    def _can_remove_vertex(self, v: Vertex, valence, current_gate, patch_vertices) -> bool:
        if self.mesh is None:
            return False
        import copy
        #mesh_aux = copy.deepcopy(self.mesh)
        
        ok = True
        # Check if we didn't create already existing edges
        ok = ok #and self.retriangulator.retriangulate(mesh_aux, valence, current_gate, patch_vertices)

        # Check if we didn't create flipped normals
        #ok = ?

        # destroy var mesh_aux
        #del mesh_aux

        return ok and self.mesh.can_remove_vertex(v)   


    def compress(self,iteration_compress,initial_gate) -> None:
        if self.mesh is None:
            raise ValueError("Mesh not loaded. Please parse a file first.")

        # ------------------------------------------------------------------
        # Initial gate selection
        # ------------------------------------------------------------------
        
        #initial_gate = self.__initial_gate_for_crude_sphere_6()
        #initial_gate = self.__initial_gate_for_test()
        if initial_gate is None:
            raise RuntimeError("Could not find an initial gate in the mesh.")

        # Tag the two vertices of the initial gate
        v_minus, v_plus = initial_gate.edge
        self.retriangulator.retriangulation_tags[v_minus] = RetriangulationTag.Minus
        self.retriangulator.retriangulation_tags[v_plus] = RetriangulationTag.Plus

        # ==================================================================
        # DECIMATION PHASE
        # ==================================================================
        FiFo: List[Gate] = [initial_gate]
        conquered_faces: Set[Face] = set()

        iteration = 1
        while FiFo:

            #print("Remaining gates in FiFo:", len(FiFo))
            current_gate = FiFo.pop(0)
            if current_gate.to_face() in conquered_faces:
                continue

            left_vertex, right_vertex = current_gate.edge
            center_vertex = current_gate.front_vertex

            vertex_state = self.state_flags.get(center_vertex, StateFlag.Free)

            # valence is taken from the mesh topology
            valence = center_vertex.valence()
            #print(valence, "valence ", center_vertex,
            #    "state:", vertex_state, left_vertex, right_vertex)
            
            patch = self.mesh.get_patch(center_vertex)
            patch_vertices = patch.surrounding_vertices(current_gate.edge)
            out_gates = []
            
            # ------------------------------------------------------------------
            # PROPER PATCH / DECIMATION (for free vertices)
            # ------------------------------------------------------------------
            if (vertex_state == StateFlag.Free and valence in [3, 4, 5, 6] 
                and self._can_remove_vertex(center_vertex, valence, current_gate, patch_vertices)):
                # Original logic: get patch around the center vertex
                #print("Processing patch for vertex:", center_vertex, "valence:", valence, "with faces:")
                for f in patch.faces:
                    conquered_faces.add(f)
                    #print("\t- ", f)

                # Get output gates and ring vertices
                out_gates = patch.output_gates(current_gate.edge)
                #print(len(out_gates), "gates in the patch")

                #print("Remove patch central vertex:", center_vertex)
                # Perform local retriangulation
                out = self.retriangulator.retriangulate(
                    self.mesh, valence, current_gate, patch_vertices
                )
                if not out: 
                    print(f"Error during retriangulation")

                # Mark boundary vertices as conquered and enqueue gates
                for vertex in patch_vertices:
                    self.set_vertex_state(vertex, StateFlag.Conquered)
                
                #self.mesh.export_to_obj(f"decimation_step_{iteration_compress}.obj")

            # ------------------------------------------------------------------
            # NULL PATCH (for free vertices that cannot be decimated cleanly)
            # ------------------------------------------------------------------
            else:
                if valence > 6:
                    self.retriangulator.retriangulation_tags[center_vertex] = RetriangulationTag.Plus
                # We are here with a vertex that is still Free but not suitable
                # for normal decimation (wrong valence or cannot be removed).
                #print("NULL PATCH for vertex:", center_vertex)
                conquered_faces.add(current_gate.to_face())
                out_gates = current_gate.to_face().output_gates(current_gate.edge)

            # Center vertex is now conquered (removed / retriangulated)
            self.set_vertex_state(center_vertex, StateFlag.Conquered)

            for gate in out_gates:
                FiFo.append(gate)

            iteration += 1
        # end while

        self.mesh.export_to_obj(f"decimation.obj")
        adjacent_vertex = self.mesh.get_oriented_vertices(initial_gate.edge)
        new_front_vertex = None
        if adjacent_vertex[0] is not None:
            new_front_vertex = adjacent_vertex[0]
        elif adjacent_vertex[1] is not None:
            new_front_vertex = adjacent_vertex[1]

        if new_front_vertex is not None:
            initial_gate.front_vertex = new_front_vertex 
            self._cleaning_phase(initial_gate)

        # # Check the two initial vertices
        # adjacent_vertex = self.mesh.get_oriented_vertices(initial_gate.edge)
        # new_front_vertex = None
        # if adjacent_vertex[0] is not None:
        #     new_front_vertex = adjacent_vertex[0]
        # elif adjacent_vertex[1] is not None:
        #     new_front_vertex = adjacent_vertex[1]
        # init_left, init_right = initial_gate.edge
        # if init_left.valence() == 3 :
        #     # retriangulate left vertex
        #     patch = self.mesh.get_patch(init_left)
        #     starting_edge = (initial_gate.edge[1], initial_gate.front_vertex)
        #     patch_vertices = patch.surrounding_vertices(starting_edge)
        #     self.retriangulator.retriangulate(
        #             self.mesh, init_left.valence(), Gate(starting_edge, init_left), patch_vertices
        #         )
        # if init_right.valence() == 3 :
        #     # retriangulate right vertex
        #     patch = self.mesh.get_patch(init_right)
        #     starting_edge = (initial_gate.front_vertex,initial_gate.edge[0])
        #     patch_vertices = patch.surrounding_vertices(starting_edge)
        #     self.retriangulator.retriangulate(
        #             self.mesh, init_right.valence(), Gate(starting_edge, init_right), patch_vertices
        #         )
        
        # Debug: export the result
        self.mesh.commit()

    
    def _cleaning_phase(self, initial_gate) -> None :
        if initial_gate is None:
            raise RuntimeError("Could not find an initial gate in the mesh.")

        # Tag the two vertices of the initial gate
        #v_minus, v_plus = initial_gate.edge
        #print("#############################CLEANING###################")
        # set all tags to Defaults
        #for v in self.retriangulator.retriangulation_tags.keys():
        #    self.retriangulator.retriangulation_tags[v] = RetriangulationTag.Default

        #self.retriangulator.retriangulation_tags[v_minus] = RetriangulationTag.Minus
        #self.retriangulator.retriangulation_tags[v_plus] = RetriangulationTag.Plus

        # Set all the vertex to free

        # ==================================================================
        # DECIMATION PHASE
        # ==================================================================
        FiFo: List[Gate] = [initial_gate]
        conquered_faces: Set[Face] = set()

        for v in self.state_flags.keys():
            self.state_flags[v] = StateFlag.Free

        while FiFo:
            #print("Remaining gates in FiFo:", len(FiFo))
            current_gate = FiFo.pop(0)
            if current_gate.to_face() in conquered_faces:
                continue

            left_vertex, right_vertex = current_gate.edge
            center_vertex = current_gate.front_vertex

            vertex_state = self.state_flags.get(center_vertex, StateFlag.Free)

            # valence is taken from the mesh topology
            valence = center_vertex.valence()
            #print(valence, "valence ", center_vertex,
            #    "state:", vertex_state, left_vertex, right_vertex)
            
            patch = self.mesh.get_patch(center_vertex)
            patch_vertices = patch.surrounding_vertices(current_gate.edge)
            out_gates = []

            # ------------------------------------------------------------------
            # PROPER PATCH / DECIMATION (for free vertices)
            # ------------------------------------------------------------------
            if (vertex_state == StateFlag.Free and valence == 3 
                and self._can_remove_vertex(center_vertex, valence, current_gate, patch_vertices)):
                # Original logic: get patch around the center vertex
                #print("Processing patch for vertex:", center_vertex, "valence:", valence, "with faces:")
                for f in patch.faces:
                    conquered_faces.add(f)
                    #print("\t- ", f)

                # Get output gates and ring vertices
                out_gates_aux = patch.output_gates(current_gate.edge)
                for g in out_gates_aux:
                    conquered_faces.add(g.to_face())
                    for g_out in g.to_face().output_gates(g.edge):
                        out_gates.append(g_out)
                #print(len(out_gates), "gates in the patch")

                #print("Remove patch central vertex:", center_vertex)
                # Perform local retriangulation
                self.retriangulator.retriangulate(
                    self.mesh, valence, current_gate, patch_vertices
                )

                # Mark boundary vertices as conquered and enqueue gates
                for vertex in patch_vertices:
                    self.set_vertex_state(vertex, StateFlag.Conquered)

            # ------------------------------------------------------------------
            # NULL PATCH (for free vertices that cannot be decimated cleanly)
            # ------------------------------------------------------------------
            else:
                # We are here with a vertex that is still Free but not suitable
                # for normal decimation (wrong valence or cannot be removed).
                #print("NULL PATCH for vertex:", center_vertex)
                conquered_faces.add(current_gate.to_face())
                out_gates = current_gate.to_face().output_gates(current_gate.edge)

            # Center vertex is now conquered (removed / retriangulated)
            self.set_vertex_state(center_vertex, StateFlag.Conquered)

            for gate in out_gates:
                FiFo.append(gate)
        # end while
