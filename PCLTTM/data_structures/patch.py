from __future__ import annotations

from typing import List, Tuple, Optional

from .vertex import Vertex


class Patch:
    """
    Patch of faces around a center vertex.
    """

    def __init__(self, center_vertex: Vertex, faces: List["Face"], mesh=None):
        self.center_vertex = center_vertex
        self.faces: List["Face"] = faces
        self.mesh = mesh

        # Optional: used if you later want to store from which gate this patch was entered
        self.input_gate: Optional["Gate"] = None

    # ------------------------------------------------------------------
    # Patch related functions
    # ------------------------------------------------------------------

    def valence(self) -> int:
        """
        Number of incident faces (i.e. faces around the center vertex).
        """
        return len(self.faces)

    def barycenter(self) -> Optional[Vertex]:
        """
        Compute the barycenter of all vertices in the patch (including the center).

        Returns a *new* Vertex instance (not one of the existing ones),
        attached to the same mesh for convenience.
        """
        if not self.faces:
            return None

        vertices = {self.center_vertex}
        for f in self.faces:
            for v in f.vertices:
                vertices.add(v)

        n = len(vertices)
        if n == 0:
            return None

        sx = sy = sz = 0.0
        for v in vertices:
            x, y, z = v.position
            sx += x
            sy += y
            sz += z

        bx = sx / n
        by = sy / n
        bz = sz / n

        return Vertex((bx, by, bz), self.mesh)

    def local_coordinate_system(self):
        """
        Placeholder for a local coordinate system computation (normal + tangent basis).
        Implement later if needed.
        """
        return None

    def is_oriented(self) -> bool:
        """
        Returns True if an input gate was set (useful if you later use oriented patches).
        """
        return self.input_gate is not None

    def surrounding_vertices(
        self,
        starting_edge: Tuple[Vertex, Vertex]
    ) -> List[Vertex]:
        """
        Return the ordered ring of vertices around the center vertex,
        starting from starting_edge[0] and walking around the center.

        starting_edge = (v_start, v_next) where both are neighbors of center_vertex.
        """
        if starting_edge is None or None in starting_edge:
            return []

        if not self.faces:
            return []

        remaining_faces = set(self.faces)
        sequence: List[Vertex] = []

        current_vertex = starting_edge[0]

        # Safety guard to avoid infinite loops in corrupted meshes
        max_steps = len(remaining_faces)

        for _ in range(max_steps):
            # Find a face incident to both current_vertex and center_vertex
            face = next(
                (
                    f
                    for f in remaining_faces
                    if (current_vertex in f.vertices)
                    and (self.center_vertex in f.vertices)
                ),
                None,
            )

            if face is None:
                # No more connected faces around the center from current_vertex
                break

            # The "next" vertex is the third vertex of that face, not current_vertex nor center.
            next_vertex = face.next_vertex((current_vertex, self.center_vertex))
            if next_vertex is None:
                print("Warning: could not find next vertex in face:", face)
                break

            sequence.append(next_vertex)
            remaining_faces.remove(face)

            current_vertex = next_vertex

        return sequence

    def surrounding_edges(
        self,
        starting_edge: Tuple[Vertex, Vertex]
    ) -> List[Tuple[Vertex, Vertex]]:
        """
        Return the ordered list of edges (v_i, v_{i+1}) around the center vertex,
        aligned with surrounding_vertices().
        """
        if starting_edge is None or None in starting_edge:
            return []

        verts = self.surrounding_vertices(starting_edge)
        if not verts:
            return []

        edge_sequence: List[Tuple[Vertex, Vertex]] = []
        current_vertex = starting_edge[0]

        for next_vertex in verts:
            edge_sequence.append((current_vertex, next_vertex))
            current_vertex = next_vertex

        return edge_sequence

    # ------------------------------------------------------------------
    # Mesh related functions
    # ------------------------------------------------------------------

    def output_gates(
        self,
        starting_edge: Tuple[Vertex, Vertex]
    ) -> List["Gate"]:
        """
        For each boundary edge around the center vertex, find the face on
        the "outside" (the one that does *not* contain the center vertex)
        and create a Gate towards that outside vertex.

        This uses mesh.get_oriented_faces(edge), which should return (left_face, right_face).
        """
        if starting_edge is None or None in starting_edge:
            return []

        if self.mesh is None:
            return []

        # local import to avoid circular imports
        from .gate import Gate

        output_gates: List[Gate] = []

        for edge in self.surrounding_edges(starting_edge):
            oriented_faces = self.mesh.get_oriented_faces(edge)
            # oriented_faces is (Face | None, Face | None)
            for face in oriented_faces:
                if face is None:
                    continue
                if self.center_vertex in face.vertices:
                    # This face is still in the patch, not "outside"
                    continue

                next_vertex = face.next_vertex(edge)
                if next_vertex is None:
                    continue

                output_gates.append(Gate(edge, next_vertex, self.mesh))
                # We only want one outside face per edge
                break

        return output_gates[1:]  # Exclude the input gate

    # ------------------------------------------------------------------
    # Internal functions
    # ------------------------------------------------------------------

    def __hash__(self):
        return hash(self.center_vertex)

    def __repr__(self):
        return f"Patch(center={self.center_vertex}, faces={len(self.faces)})"
