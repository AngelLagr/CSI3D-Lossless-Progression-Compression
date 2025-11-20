from collections import deque
from copy import deepcopy
import random
from typing import Dict, List, Optional, Set, Tuple

from .data_structures import Vertex, Face, Gate, Patch
from .obja_parser import ObjaReader, ObjaWriter


# ============================================================================
# MESH TOPOLOGY HELPERS
# ============================================================================

"""
Manages mesh topology information: valences, adjacency, neighborhoods.

TODO: Handle normal orientation and faces' vertices order.
"""


class MeshTopology:
    class State:
        def __init__(self):
            # Hash(Vertex) -> Set(Vertex)
            self.vertex_connections = dict()
            # Hash(Edge: (Vertex_from, Vertex_to)) ->
            #   (3rd vertex of left face [from->to], 3rd vertex of right face [to->from])
            self.orientations = dict()

        # We make two hypotheses for difference():
        # - self is one step more compressed than previous_state
        # - self is included in previous_state, and there's more vertices in previous_state
        # - Missing edges in previous_state are edges to remove
        # return (vertex_connections_to_add, edges_to_remove)
        def compression_difference(self, previous_state: "MeshTopology.State") -> Tuple[Dict, Dict]:
            vertex_connections_to_add = dict()
            edges_to_remove = dict()

            vertex_to_add = previous_state.vertex_connections.keys() - self.vertex_connections.keys()
            for v in vertex_to_add:
                vertex_connections_to_add[v] = previous_state.vertex_connections[v]

            for edge in self.orientations.keys().difference(previous_state.orientations.keys()):
                if (edge[1], edge[0]) not in edges_to_remove:
                    edges_to_remove[edge] = self.orientations[edge]
            
            return (vertex_connections_to_add, edges_to_remove)
    # ----------------------------------------------------------------------
    # Constructors
    # ----------------------------------------------------------------------

    @staticmethod
    def from_obj_file(file_path: str) -> "MeshTopology":
        """
        Build a MeshTopology from an OBJ(A) file.

        Expects ObjaReader to yield Vertex and Face objects.
        """
        reader = ObjaReader()
        mesh = MeshTopology()
        for elem in reader.parse_file(file_path):
            if isinstance(elem, Vertex):
                mesh.add_vertex(elem)
            elif isinstance(elem, Face):
                for edge in elem.edges():
                    mesh.add_edge(*edge)
                    mesh.set_orientation(edge, (elem.next_vertex(edge) , None))
        return mesh

    def __init__(self):
        self.active_state = MeshTopology.State()
        # Seed committed_states with an initial empty state so commit() always has a "previous" state.
        self.committed_states = deque([deepcopy(self.active_state)])

    # ----------------------------------------------------------------------
    # Transaction helpers (commit / rollback)
    # ----------------------------------------------------------------------

    def commit(self) -> Tuple[Dict, Dict]:
        """
        Save current active_state as a new committed state and return the diff
        with the previously committed state.
        """
        last_state = self.committed_states[-1]
        diff = self.active_state.compression_difference(last_state)
        self.committed_states.append(deepcopy(self.active_state))
        return diff

    def rollback(self) -> bool:
        """
        Restore the previous committed state (if any).
        Never removes the initial baseline state.
        """
        if len(self.committed_states) > 1:
            # Pop current snapshot and revert to the one before it.
            self.committed_states.pop()
            self.active_state = deepcopy(self.committed_states[-1])
            return True
        return False
        # else: nothing to rollback

    # ----------------------------------------------------------------------
    # Vertex management
    # ----------------------------------------------------------------------

    def add_vertex(
        self,
        vertex: Vertex,
        connected_to: Optional[List[Vertex]] = None,
    ):
        """
        Add a vertex to the mesh and optionally connect it to a list of neighbors.
        """
        if connected_to is None:
            connected_to = []

        if vertex not in self.active_state.vertex_connections:
            vertex.mesh = self
            self.active_state.vertex_connections[vertex] = set()
            for conn in connected_to:
                self.add_edge(vertex, conn)

    def can_remove_vertex(self, vertex: Vertex) -> bool:
        """
        A vertex can be removed only if all its neighbors will still have valence > 3 after removal.
        """
        if vertex not in self.active_state.vertex_connections:
            return False

        return all(
            len(self.active_state.vertex_connections[neighbor]) > 3
            for neighbor in self.active_state.vertex_connections[vertex]
        )

    def remove_vertex(self, vertex: Vertex, force: bool = False):
        """
        Remove a vertex and its incident edges, cleaning up orientations.
        """
        if self.can_remove_vertex(vertex) is False and not force:
            return

        if vertex not in self.active_state.vertex_connections:
            return

        # Remove vertex from all neighbors
        neighbors = list(self.active_state.vertex_connections[vertex])
        for neighbor in neighbors:
            if neighbor in self.active_state.vertex_connections:
                self.active_state.vertex_connections[neighbor].discard(vertex)

            # Clean up edge orientations if present
            if (vertex, neighbor) in self.active_state.orientations:
                del self.active_state.orientations[(vertex, neighbor)]
            if (neighbor, vertex) in self.active_state.orientations:
                del self.active_state.orientations[(neighbor, vertex)]

        # Finally remove the vertex itself
        del self.active_state.vertex_connections[vertex]

    # ----------------------------------------------------------------------
    # Edge management
    # ----------------------------------------------------------------------

    def add_edge(self, fromV: Vertex, toV: Vertex) -> bool:
        """
        Add an undirected edge between fromV and toV.
        Orientation must be set later explicitly via set_orientation().
        """
        if (
            fromV not in self.active_state.vertex_connections
            or toV not in self.active_state.vertex_connections
        ):
            return False    
        self.active_state.vertex_connections[fromV].add(toV)
        self.active_state.vertex_connections[toV].add(fromV)
        return True

    def can_remove_edge(self, fromV: Vertex, toV: Vertex) -> bool:
        """
        An edge can be removed if both vertices have valence > 3 (unless force=True).
        """
        return (
            fromV in self.active_state.vertex_connections
            and toV in self.active_state.vertex_connections[fromV]
            and len(self.active_state.vertex_connections[fromV]) > 3
            and len(self.active_state.vertex_connections[toV]) > 3
        )

    def _remove_edge_vertices(self, fromV: Vertex, toV: Vertex, force: bool = False):
        """
        Internal helper: actual implementation of edge removal, using vertex endpoints.
        """
        if self.can_remove_edge(fromV, toV) is False and not force:
            return

        # Clean up orientation for this edge if exists
        if (fromV, toV) in self.active_state.orientations:
            del self.active_state.orientations[(fromV, toV)]
        if (toV, fromV) in self.active_state.orientations:
            del self.active_state.orientations[(toV, fromV)]

        # Remove from adjacency lists
        if fromV in self.active_state.vertex_connections:
            self.active_state.vertex_connections[fromV].discard(toV)
        if toV in self.active_state.vertex_connections:
            self.active_state.vertex_connections[toV].discard(fromV)

    def remove_edge(
        self,
        edge_or_gate,
        maybe_toV: Optional[Vertex] = None,
        force: bool = False,
    ):
        """
        Remove an edge. Supports two calling styles:

        - remove_edge(fromV, toV, force=False)
        - remove_edge(gate, force=False)  where gate.edge = (fromV, toV)
        """
        # Case: remove_edge(gate, force=...)
        if isinstance(edge_or_gate, Gate):
            fromV, toV = edge_or_gate.edge
            self._remove_edge_vertices(fromV, toV, force=force)
            return

        # Case: remove_edge(fromV, toV, force=...)
        fromV = edge_or_gate
        toV = maybe_toV
        if fromV is None or toV is None:
            return
        self._remove_edge_vertices(fromV, toV, force=force)

    # ----------------------------------------------------------------------
    # Orientation helpers
    # ----------------------------------------------------------------------

    """
        Set the orientation of an edge by specifying the "left" face's third vertex.

        from_to: (fromV, toV)
        third_vertex: vertex of the face (fromV, toV, third_vertex) for the left side.
        """
    def set_orientation(self, from_to: Tuple[Vertex, Vertex], left_right: Tuple[Vertex, Vertex]) -> bool:
        
        fromV, toV = from_to
        if (fromV not in self.active_state.vertex_connections
            or toV not in self.active_state.vertex_connections):
            return False
        
        
        third_vertex, other_vertex = left_right
        if third_vertex is None:
            third_vertex = self.active_state.orientations.get(from_to, (None, None))[0]
        if other_vertex is None:
            other_vertex = self.active_state.orientations.get(from_to, (None, None))[1]
        
        opposite_side = (toV, fromV)
        #if from_to in self.active_state.orientations:
        #    print("Current orientation:", self.active_state.orientations[from_to])
        #if opposite_side in self.active_state.orientations:
        #    print("Current opposite orientation:", self.active_state.orientations[opposite_side])

        self.active_state.orientations[from_to] = (third_vertex, other_vertex)
        self.active_state.orientations[opposite_side] = (other_vertex, third_vertex)

        #print("Set orientation:", from_to, "->", self.active_state.orientations[from_to])
        #print("Set opposite orientation:", opposite_side, "->", self.active_state.orientations[opposite_side])
        temp1 = self.active_state.orientations.get((toV, third_vertex), (None, None))
        temp2 = self.active_state.orientations.get((third_vertex, fromV), (None, None))
        temp3 = self.active_state.orientations.get((other_vertex, toV), (None, None))
        temp4 = self.active_state.orientations.get((fromV, other_vertex), (None, None))
        self.active_state.orientations[(toV, third_vertex)] = (fromV, temp1[1])
        self.active_state.orientations[(third_vertex, fromV)] = (toV, temp2[1])
        if other_vertex is not None:
            self.active_state.orientations[(other_vertex, toV)] = (fromV, temp3[1])
            self.active_state.orientations[(fromV, other_vertex)] = (toV, temp4[1])
        
        #The other side
        temp5 = self.active_state.orientations.get((third_vertex,toV), (None, None))
        temp6 = self.active_state.orientations.get((fromV,third_vertex), (None, None))
        temp7 = self.active_state.orientations.get((toV,other_vertex), (None, None))
        temp8 = self.active_state.orientations.get((other_vertex,fromV), (None, None))
        self.active_state.orientations[(third_vertex,toV)] = (temp5[0], fromV)
        self.active_state.orientations[(fromV,third_vertex)] = (temp6[0],toV )
        if other_vertex is not None:
            self.active_state.orientations[(toV,other_vertex)] = (temp7[0],fromV)
            self.active_state.orientations[(other_vertex,fromV)] = (temp8[0],toV)
        
        return True

    def get_connected_vertices(self, vertex: Vertex) -> Set[Vertex]:
        """
        Return the set of vertices adjacent to the given vertex.
        """
        if vertex not in self.active_state.vertex_connections:
            return set()

        return self.active_state.vertex_connections[vertex]

    # Return (None, None) if the edge is not oriented
    def get_oriented_vertices(
        self,
        oriented_edge: Tuple[Vertex, Vertex]
    ) -> Tuple[Optional[Vertex], Optional[Vertex]]:
        if oriented_edge not in self.active_state.orientations:
            return (None, None)

        return self.active_state.orientations[oriented_edge]

    # Left face is the one in the orientation of from -> to, right is to -> from
    def get_oriented_faces(
        self,
        from_to: Tuple[Vertex, Vertex]
    ) -> Tuple[Optional[Face], Optional[Face]]:
        left_vertex, right_vertex = self.get_oriented_vertices(from_to)
        v1, v2 = from_to
        return (
            Face((v1, v2, left_vertex), self) if left_vertex is not None else None,
            Face((v2, v1, right_vertex),
                 self) if right_vertex is not None else None,
        )

    # ----------------------------------------------------------------------
    # Face / patch helpers
    # ----------------------------------------------------------------------

    def get_faces(self, fromV: Vertex) -> Set[Face]:
        """
        Return all faces around a vertex, based on oriented edges.
        """
        if fromV not in self.active_state.vertex_connections:
            return set()

        faces: Set[Face] = set()
        valence = self.get_valence(fromV)
        neighbors = self.active_state.vertex_connections[fromV]

        for toV in neighbors:
            if valence == len(faces):
                break

            connected_faces = self.get_oriented_faces((fromV, toV))
            if connected_faces == (None, None):
                print("Warning: Missing face for edge", (fromV, toV))
                continue

            for face in connected_faces:
                if face is not None:
                    faces.add(face)
                else:
                    print("MeshTopology: incomplete face information detected.")

        return faces

    # Warning: faces are returned in a non-deterministic order
    def get_patch(self, vertex: Vertex) -> Optional[Patch]:
        if vertex not in self.active_state.vertex_connections:
            return None
        faces = self.get_faces(vertex)
        return Patch(vertex, faces, self)

    # ----------------------------------------------------------------------
    # Basic metrics
    # ----------------------------------------------------------------------

    def get_valence(self, vertex: Vertex) -> int:
        return len(self.active_state.vertex_connections.get(vertex, set()))

    def get_vertices(self) -> Set[Vertex]:
        return set(self.active_state.vertex_connections.keys())

    # ----------------------------------------------------------------------
    # Gate selection (for decimation)
    # ----------------------------------------------------------------------

    # Get the first available gate in the mesh
    def get_random_gate(self) -> Optional[Gate]:
        if len(self.active_state.vertex_connections) == 0:
            return None

        # Arbitrary upper limit on trials
        MAX_TRIALS = len(self.active_state.vertex_connections) * 2
        for _ in range(MAX_TRIALS):
            v1 = random.sample(
                list(self.active_state.vertex_connections.keys()), 1
            )[0]
            if len(self.active_state.vertex_connections[v1]) == 0:
                continue

            v2 = random.sample(
                list(self.active_state.vertex_connections[v1]), 1
            )[0]
            adjacent_vertex = self.get_oriented_vertices((v1, v2))
            # Try left side
            if adjacent_vertex[0] is not None and self.can_remove_vertex(adjacent_vertex[0]):
                return Gate((v1, v2), adjacent_vertex[0], self)
            # Try right side
            if adjacent_vertex[1] is not None and self.can_remove_vertex(adjacent_vertex[1]):
                return Gate((v2, v1), adjacent_vertex[1], self)

        return None

    # ----------------------------------------------------------------------
    # Simple OBJ exporter (for debug)
    # ----------------------------------------------------------------------

    def export_to_obj(self, path: str) -> None:
        """
        Export the current mesh topology to a simple OBJ file.

        Vertices come from vertex_connections keys.
        Faces are reconstructed from the oriented faces around each vertex,
        WE HAVE TO RESPECT THE ORIENTATION GIVEN BY THE MESH
        """
        # Collect vertices
        vertices = sorted(self.get_vertices())
        indices = {v: i + 1 for i, v in enumerate(vertices)}

        with open(path, "w") as file_obj:
            # ---- write vertices ----
            for v in vertices:
                x, y, z = v.position
                file_obj.write(f"v {x} {y} {z}\n")

            # ---- collect unique faces preserving orientation ----
            # Use a mapping from frozenset(vertices) -> oriented tuple(vertices)
            # so we deduplicate faces while keeping the original vertex order
            written_faces = set()  # frozenset({v1,v2,v3}) -> (v1, v2, v3)

            for v in vertices:
                for face in self.get_faces(v):
                    if face is None or face in written_faces:
                        continue

                    file_obj.write("f " + " ".join(str(indices[v]) for v in face.vertices) + "\n")
                    written_faces.add(face)
