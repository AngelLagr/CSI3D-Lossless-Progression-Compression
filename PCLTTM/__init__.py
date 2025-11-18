from typing import List, Optional, Dict, Set

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

<<<<<<< HEAD
    def __initial_gate_for_test(self) -> Gate:
        initial_left_vertex = Vertex((3,0,0), self.mesh)
        initial_right_vertex = Vertex((4,2,0), self.mesh)
        initial_front_vertex = Vertex((2,2,0), self.mesh)
=======
    def __initial_gate_for_crude_sphere_5(self) -> Gate:
        initial_left_vertex = Vertex((6, 0, 3), self.mesh)
        initial_right_vertex = Vertex((2, 6, 3), self.mesh)
        initial_front_vertex = Vertex((0, 0, 10), self.mesh)
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)

    def __initial_gate_for_crude_sphere_6(self) -> Gate:
        initial_left_vertex = Vertex((6, 0, 3), self.mesh)
        initial_right_vertex = Vertex((3, 5, 3), self.mesh)
        initial_front_vertex = Vertex((0, 0, 10), self.mesh)
>>>>>>> a560321fab0fe04129a312967d866b2b173e9df6
        return Gate((initial_left_vertex, initial_right_vertex), initial_front_vertex, self.mesh)


    def compress(self) -> None:
        if self.mesh is None:
            raise ValueError("Mesh not loaded. Please parse a file first.")

        # ------------------------------------------------------------------
        # Initial gate selection
        # ------------------------------------------------------------------
        #initial_gate = self.mesh.get_random_gate()
<<<<<<< HEAD
        initial_gate = self.__initial_gate_for_test()
=======
        initial_gate = self.__initial_gate_for_crude_sphere_6()
>>>>>>> a560321fab0fe04129a312967d866b2b173e9df6
          
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
        visited_gates: Set[Gate] = set()

        iteration = 1
        while FiFo:
            #print("Remaining gates in FiFo:", len(FiFo))
            current_gate = FiFo.pop(0)

            left_vertex, right_vertex = current_gate.edge
            center_vertex = current_gate.front_vertex

            vertex_state = self.state_flags.get(center_vertex, StateFlag.Free)

            # ------------------------------------------------------------------
            # IMPORTANT: skip gates whose front vertex is already conquered
            # ------------------------------------------------------------------
            if vertex_state == StateFlag.Conquered:
                # This gate lies behind the conquest front, ignore it.
                continue

            # Optional: avoid processing the exact same gate twice
            if current_gate in visited_gates:
                continue
            visited_gates.add(current_gate)

            # valence is taken from the mesh topology
            valence = center_vertex.valence()

            print(
                valence, "valence ", center_vertex,
                "state:", vertex_state, left_vertex, right_vertex
            )

            can_remove = self.mesh.can_remove_vertex(center_vertex)

            # ------------------------------------------------------------------
            # PROPER PATCH / DECIMATION (for free vertices)
            # ------------------------------------------------------------------
            if (
                vertex_state == StateFlag.Free
                and valence in [3, 4, 5, 6]
                and can_remove
            ):
                # Original logic: get patch around the center vertex
                patch = self.mesh.get_patch(center_vertex)
                print("Processing patch for vertex:", center_vertex, "valence:", valence, "with faces:")
                for f in patch.faces:
                    print("\t- ", f)

                if patch is None or patch.valence() == 0:
                    # Degenerate case: treat as null patch, but do NOT propagate
                    print("NULL PATCH (empty) for vertex:", center_vertex)
                    self.set_vertex_state(center_vertex, StateFlag.Conquered)
                    continue

                # Get output gates and ring vertices
                out_gates = patch.output_gates(current_gate.edge)
                print(len(out_gates), "gates in the patch")

                patch_vertices = patch.surrounding_vertices(current_gate.edge)

                print("Remove patch central vertex:", center_vertex)
                # Perform local retriangulation
                self.retriangulator.retriangulate(
                    self.mesh, valence, current_gate, patch_vertices
                )

                # Mark boundary vertices as conquered and enqueue gates
                for gate in out_gates[:-1]:
                    v1, v2 = gate.edge
                    self.set_vertex_state(v1, StateFlag.Conquered)
                    self.set_vertex_state(v2, StateFlag.Conquered)
                    FiFo.append(gate)

                # Center vertex is now conquered (removed / retriangulated)
                self.set_vertex_state(center_vertex, StateFlag.Conquered)

            # ------------------------------------------------------------------
            # NULL PATCH (for free vertices that cannot be decimated cleanly)
            # ------------------------------------------------------------------
            else:
                # We are here with a vertex that is still Free but not suitable
                # for normal decimation (wrong valence or cannot be removed).
                print("NULL PATCH for vertex:", center_vertex)
                self.set_vertex_state(center_vertex, StateFlag.Conquered)

                # Get oriented neighbors to propagate the "front"
                oriented_v1 = self.mesh.get_oriented_vertices(
                    (left_vertex, center_vertex)
                )
                oriented_v2 = self.mesh.get_oriented_vertices(
                    (center_vertex, right_vertex)
                )

                # Left side
                if oriented_v1[0] is not None:
                    next_v = oriented_v1[0]
                    # Only propagate if the next front vertex is still Free
                    if self.state_flags.get(next_v, StateFlag.Free) == StateFlag.Free:
                        gate1 = Gate(
                            (left_vertex, center_vertex),
                            next_v,
                            self.mesh
                        )
                        FiFo.append(gate1)

                # Right side
                if oriented_v2[1] is not None:
                    next_v = oriented_v2[1]
                    if self.state_flags.get(next_v, StateFlag.Free) == StateFlag.Free:
                        gate2 = Gate(
                            (center_vertex, right_vertex),
                            next_v,
                            self.mesh
                        )
                        FiFo.append(gate2)
            self.mesh.export_to_obj(f"decimation_step_{iteration}.obj")
            iteration += 1

        #self._cleaning_phase(initial_gate, visited_gates)

        # Debug: export the result

    def _cleaning_phase(self, initial_gate, visited_gates) -> None:
                # ==================================================================
        # CLEANING PHASE (optional refinement)
        # ==================================================================
        FiFo = [initial_gate]
        visited_gates.clear()

        while FiFo:
            print("Remaining gates in FiFo (cleaning phase):", len(FiFo))
            current_gate = FiFo.pop(0)

            if current_gate in visited_gates:
                continue
            visited_gates.add(current_gate)

            left_vertex, right_vertex = current_gate.edge
            center_vertex = current_gate.front_vertex

            valence = center_vertex.valence()
            vertex_state = self.state_flags.get(center_vertex, StateFlag.Free)

            # Only attempt cleaning on still-free vertices
            if vertex_state != StateFlag.Free:
                continue

            can_remove = self.mesh.can_remove_vertex(center_vertex)

            if valence == 3 and can_remove:
                patch = self.mesh.get_patch(center_vertex)
                if patch is None or patch.valence() == 0:
                    self.set_vertex_state(center_vertex, StateFlag.Conquered)
                    continue

                out_gates = patch.output_gates(current_gate.edge)
                patch_vertices = patch.surrounding_vertices(current_gate.edge)

                self.retriangulator.retriangulate(
                    self.mesh, valence, current_gate, patch_vertices
                )

                for gate in out_gates:
                    v1, v2 = gate.edge
                    self.set_vertex_state(v1, StateFlag.Conquered)
                    self.set_vertex_state(v2, StateFlag.Conquered)
                    FiFo.append(gate)

                self.set_vertex_state(center_vertex, StateFlag.Conquered)

            else:
                # No special cleaning, just propagate conquest
                self.set_vertex_state(center_vertex, StateFlag.Conquered)

                oriented_v1 = self.mesh.get_oriented_vertices(
                    (left_vertex, center_vertex)
                )
                oriented_v2 = self.mesh.get_oriented_vertices(
                    (center_vertex, right_vertex)
                )

                if oriented_v1[0] is not None:
                    next_v = oriented_v1[0]
                    if self.state_flags.get(next_v, StateFlag.Free) == StateFlag.Free:
                        gate1 = Gate(
                            (left_vertex, center_vertex),
                            next_v,
                            self.mesh
                        )
                        FiFo.append(gate1)

                if oriented_v2[1] is not None:
                    next_v = oriented_v2[1]
                    if self.state_flags.get(next_v, StateFlag.Free) == StateFlag.Free:
                        gate2 = Gate(
                            (center_vertex, right_vertex),
                            next_v,
                            self.mesh
                        )
                        FiFo.append(gate2)
