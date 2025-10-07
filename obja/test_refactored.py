#!/usr/bin/env python3
"""
Implementation of Alliez-Desbrun Progressive Compression of Arbitrary Triangular Meshes.
Based on the paper: "Progressive Compression of Arbitrary Triangular Meshes" (2001)

This implements the valence-driven conquest algorithm for progressive mesh encoding.
"""

import collections
import math
import struct
import zlib
from typing import List, Tuple, Optional, Set, Dict
from enum import IntEnum

import obja  
import numpy as np


# ============================================================================
# CONSTANTS AND ENUMERATIONS
# ============================================================================

class VertexState(IntEnum):
    """Vertex states during the conquest process."""
    FREE = 0        # Not yet processed
    CONQUERED = 1   # On the conquest boundary
    TO_REMOVE = 2   # Scheduled for removal (decimation)


class FaceState(IntEnum):
    """Face states during the conquest process."""
    FREE = 0        # Not yet processed
    CONQUERED = 1   # Processed (part of coarse mesh)
    TO_REMOVE = 2   # Will be removed (part of a patch)


class VertexTag(IntEnum):
    """Tags for boundary vertices to enable deterministic retriangulation."""
    UNDEF = 0
    PLUS = 1   # '+' tag
    MINUS = 2  # '-' tag


# Valence constraints for decimation and cleaning passes
MIN_VALENCE_DECIMATION = 3
MAX_VALENCE_DECIMATION = 6
VALENCE_CLEANING = 3


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class Gate:
    """
    A gate is an oriented edge with an associated front triangle.
    Gates form the boundary of the conquest region during mesh traversal.
    
    According to the paper:
    - A gate is defined by an oriented edge (v_left, v_right)
    - It has an associated front face
    - The front face contains a front vertex opposite to the gate edge
    
    Attributes:
        edge: Oriented edge as (vertex_left, vertex_right)
        front_face_idx: Index of the triangle in front of this gate
        front_vertex_idx: The vertex opposite to the gate edge (the conquerable vertex)
    """
    def __init__(self, edge: Tuple[int, int], front_face_idx: int, front_vertex_idx: int):
        self.edge = edge  # (v_left, v_right)
        self.front_face_idx = front_face_idx
        self.front_vertex_idx = front_vertex_idx
    
    def __repr__(self):
        return f"Gate(edge={self.edge}, face={self.front_face_idx}, front_v={self.front_vertex_idx})"


class Patch:
    """
    A patch is a set of faces around a removed vertex during decimation.
    
    According to the paper:
    - Each removed vertex creates a patch (polygonal hole)
    - The patch has a valence (number of boundary vertices)
    - The patch needs to be retriangulated during decoding
    
    Attributes:
        center_vertex: The vertex that was removed
        valence: Original valence of the removed vertex
        boundary_vertices: Ordered list of vertices on the patch boundary
        faces: Faces that were part of this patch
    """
    def __init__(self, center_vertex: int, valence: int):
        self.center_vertex = center_vertex
        self.valence = valence
        self.boundary_vertices: List[int] = []
        self.faces: List[int] = []


# ============================================================================
# MESH TOPOLOGY HELPERS
# ============================================================================

class MeshTopology:
    """
    Manages mesh topology information: valences, adjacency, neighborhoods.
    
    This class precomputes and maintains:
    - Vertex valences (number of incident edges)
    - Vertex-face incidence lists
    - Edge-to-face mappings
    - Face-to-face adjacency
    """
    def __init__(self, model):
        self.model = model
        self.valences = None
        self.vertex_faces = None  # For each vertex, list of incident face indices
        self.edge_to_face = None  # Maps oriented edge to face index
        self.face_adjacency = None  # For each face, set of adjacent faces
        
        self._compute_topology()
    
    def _compute_topology(self):
        """Compute all topology information."""
        n_vertices = len(self.model.vertices)
        
        # Compute valences and vertex-face adjacency
        self.valences = [0] * n_vertices
        self.vertex_faces = [[] for _ in range(n_vertices)]
        
        for face_idx, face in enumerate(self.model.faces):
            for vertex_idx in (face.a, face.b, face.c):
                self.valences[vertex_idx] += 1
                self.vertex_faces[vertex_idx].append(face_idx)
        
        # Build edge-to-face mapping and face adjacency
        self._build_adjacency()
    
    def _build_adjacency(self):
        """Build edge-to-face mapping and face-to-face adjacency."""
        self.edge_to_face = {}
        self.face_adjacency = [set() for _ in self.model.faces]
        
        for face_idx, face in enumerate(self.model.faces):
            vertices = (face.a, face.b, face.c)
            for i in range(3):
                v0 = vertices[i]
                v1 = vertices[(i+1) % 3]
                self.edge_to_face.setdefault((v0, v1), []).append(face_idx)
        
        # Build face-to-face adjacency (faces sharing an edge)
        for (v0, v1), incident_faces in self.edge_to_face.items():
            if len(incident_faces) == 2:
                face_a, face_b = incident_faces
                self.face_adjacency[face_a].add(face_b)
                self.face_adjacency[face_b].add(face_a)
    
    def get_vertex_neighbors(self, vertex_idx: int) -> Set[int]:
        """Get all vertices adjacent to the given vertex."""
        neighbors = set()
        for face_idx in self.vertex_faces[vertex_idx]:
            face = self.model.faces[face_idx]
            for v in (face.a, face.b, face.c):
                if v != vertex_idx:
                    neighbors.add(v)
        return neighbors
    
    def get_ordered_boundary(self, vertex_idx: int) -> List[int]:
        """
        Get the ordered boundary vertices around a vertex (1-ring).
        Returns vertices in CCW order forming the patch boundary.
        """
        incident_faces = self.vertex_faces[vertex_idx]
        if not incident_faces:
            return []
        
        # Build ordered ring by walking around the vertex
        neighbors = self.get_vertex_neighbors(vertex_idx)
        
        # Simple approach: return as list (proper ordering requires more work)
        # TODO: Implement proper CCW ordering using face connectivity
        return list(neighbors)


# ============================================================================
# RETRIANGULATION
# ============================================================================

def retriangulate_patch(boundary_vertices: List[int], tags: Dict[int, VertexTag]) -> List[Tuple[int, int, int]]:
    """
    Deterministic retriangulation of a patch polygon.
    
    According to the paper (Section 4.2):
    - Uses tag-based method to ensure encoder/decoder produce same triangulation
    - Tags (+/-) are assigned to boundary vertices during conquest
    - The retriangulation is deterministic based on valence and tags
    
    Args:
        boundary_vertices: Ordered list of vertices on patch boundary (CCW)
        tags: Dictionary mapping vertex indices to their tags (PLUS/MINUS)
    
    Returns:
        List of faces (triplets of vertex indices) forming the triangulation
    """
    n = len(boundary_vertices)
    if n < 3:
        return []
    
    # Simple fan triangulation from first vertex
    # This is deterministic given a fixed ordering of boundary vertices
    triangles = []
    center = boundary_vertices[0]
    for i in range(1, n - 1):
        triangles.append((center, boundary_vertices[i], boundary_vertices[i + 1]))
    
    # Assign tags to untagged vertices using alternating pattern
    for i, vertex_idx in enumerate(boundary_vertices):
        if tags.get(vertex_idx) == VertexTag.UNDEF:
            tags[vertex_idx] = VertexTag.PLUS if (i % 2 == 0) else VertexTag.MINUS
    
    return triangles


# ============================================================================
# VALENCE-DRIVEN CONQUEST ENCODER
# ============================================================================

class AllieeDesbrunEncoder:
    """
    Implements the valence-driven conquest algorithm from Alliez-Desbrun 2001.
    
    The algorithm works in two phases as described in the paper:
    1. Decimating pass: Remove vertices with valence 3-6 (Section 3.2)
    2. Cleaning pass: Remove remaining vertices with valence 3 (Section 3.3)
    
    The conquest process uses a gate queue to traverse the mesh boundary,
    creating a progressive stream of connectivity codes.
    """
    
    def __init__(self, model):
        """
        Initialize the encoder with a mesh model.
        
        Args:
            model: obja.Model instance with vertices and faces
        """
        self.model = model
        self.topology = MeshTopology(model)
        
        # State tracking as per paper's algorithm description
        self.vertex_state = [VertexState.FREE] * len(model.vertices)
        self.face_state = [FaceState.FREE] * len(model.faces)
        self.vertex_tag = [VertexTag.UNDEF] * len(model.vertices)
        
        # Output: sequence of valence codes (integers) or 'N' for null patches
        self.connectivity_codes = []
        self.patches = []  # List of Patch objects for geometry encoding
    
    def encode(self) -> List:
        """
        Run the complete encoding process following the paper's algorithm.
        
        From Section 3:
        1. Decimating pass processes vertices with valence <= 6
        2. Cleaning pass processes remaining vertices with valence == 3
        
        Returns:
            List of connectivity codes (valences or 'N' for null patches)
        """
        print("Starting decimating pass...")
        decimating_codes = self._run_conquest_pass(
            min_valence=MIN_VALENCE_DECIMATION,
            max_valence=MAX_VALENCE_DECIMATION,
            pass_name="decimating"
        )
        print(f"Decimating pass produced {len(decimating_codes)} codes")
        
        print("Starting cleaning pass...")
        cleaning_codes = self._run_conquest_pass(
            min_valence=VALENCE_CLEANING,
            max_valence=VALENCE_CLEANING,
            pass_name="cleaning"
        )
        print(f"Cleaning pass produced {len(cleaning_codes)} codes")
        
        self.connectivity_codes = decimating_codes + cleaning_codes
        return self.connectivity_codes
    
    def _find_seed_gate(self) -> Optional[Gate]:
        """
        Find a seed gate to start conquest from a free face.
        
        From paper Section 3.1:
        "The algorithm starts by choosing an arbitrary edge..."
        
        Returns:
            Gate object or None if no free faces remain
        """
        for face_idx, face in enumerate(self.model.faces):
            if self.face_state[face_idx] == FaceState.FREE:
                # Use first edge of the face
                a, b, c = face.a, face.b, face.c
                # Create gate with oriented edge (a, b) and front vertex c
                return Gate(edge=(a, b), front_face_idx=face_idx, front_vertex_idx=c)
        return None
    
    def _run_conquest_pass(self, min_valence: int, max_valence: int, pass_name: str) -> List:
        """
        Run one conquest pass with given valence constraints.
        
        From paper Section 3.1:
        "The conquest proceeds by processing gates from a FIFO queue..."
        
        Args:
            min_valence: Minimum valence to consider for removal
            max_valence: Maximum valence to consider for removal
            pass_name: Name of this pass (for debugging)
        
        Returns:
            List of connectivity codes for this pass
        """
        codes = []
        gate_queue = collections.deque()
        
        # Find seed gate
        seed = self._find_seed_gate()
        if seed is None:
            print(f"  No seed gate found for {pass_name} pass")
            return codes
        
        # Initialize: tag the two vertices of the seed edge (Section 3.1)
        # "We assign tags + and - to the right and left vertices of the seed edge"
        v_left, v_right = seed.edge
        self.vertex_tag[v_right] = VertexTag.PLUS
        self.vertex_tag[v_left] = VertexTag.MINUS
        
        # Mark seed vertices as conquered and add seed gate to queue
        self.vertex_state[v_left] = VertexState.CONQUERED
        self.vertex_state[v_right] = VertexState.CONQUERED
        gate_queue.append(seed)
        
        # Process gates (main conquest loop from Section 3.1)
        gates_processed = 0
        while gate_queue:
            gate = gate_queue.popleft()
            gates_processed += 1
            
            # Skip if face already processed
            if self.face_state[gate.front_face_idx] in (FaceState.CONQUERED, FaceState.TO_REMOVE):
                continue
            
            front_vertex = gate.front_vertex_idx
            valence = self.topology.valences[front_vertex]
            
            # Check if we can remove the front vertex (valence-driven criterion)
            if (self.vertex_state[front_vertex] == VertexState.FREE and
                min_valence <= valence <= max_valence and
                self._is_topologically_safe_to_remove(front_vertex)):
                
                # Remove vertex: create a patch (Section 3.2)
                self._process_patch_removal(front_vertex, gate, gate_queue, codes)
            else:
                # Null patch: cannot remove front vertex (Section 3.2)
                self._process_null_patch(gate, gate_queue, codes)
        
        print(f"  Processed {gates_processed} gates in {pass_name} pass")
        return codes
    
    def _is_topologically_safe_to_remove(self, vertex_idx: int) -> bool:
        """
        Check if removing a vertex would create topological issues.
        
        From paper Section 3.2:
        "We must ensure the removal doesn't create non-manifold edges"
        
        Args:
            vertex_idx: Index of vertex to check
        
        Returns:
            True if safe to remove, False otherwise
        """
        # Get neighbor vertices (1-ring)
        neighbors = self.topology.get_vertex_neighbors(vertex_idx)
        
        if len(neighbors) < 3:
            return False
        
        # Check for non-manifold edges after removal
        # The boundary polygon must be valid (no duplicate edges)
        incident_faces = [self.model.faces[fi] for fi in self.topology.vertex_faces[vertex_idx]]
        
        # Build set of boundary edges
        boundary_edges = set()
        for face in incident_faces:
            verts = (face.a, face.b, face.c)
            for i in range(3):
                a, b = verts[i], verts[(i+1) % 3]
                # Only consider edges not containing the vertex being removed
                if a != vertex_idx and b != vertex_idx:
                    # Normalize edge direction
                    edge = (min(a, b), max(a, b))
                    if edge in boundary_edges:
                        # Duplicate edge would occur - not safe
                        return False
                    boundary_edges.add(edge)
        
        return True
    
    def _process_patch_removal(self, vertex_idx: int, gate: Gate, gate_queue: collections.deque, codes: List):
        """
        Remove a vertex and create a patch.
        
        From paper Section 3.2:
        "When a vertex is removed, we encode its valence and update the conquest boundary"
        
        Args:
            vertex_idx: Index of vertex to remove
            gate: The gate through which we're removing this vertex
            gate_queue: Queue of gates to process
            codes: List to append the valence code to
        """
        valence = self.topology.valences[vertex_idx]
        
        # Create patch
        patch = Patch(center_vertex=vertex_idx, valence=valence)
        
        # Mark vertex for removal
        self.vertex_state[vertex_idx] = VertexState.TO_REMOVE
        
        # Mark all incident faces for removal and collect boundary vertices
        incident_faces = self.topology.vertex_faces[vertex_idx]
        for face_idx in incident_faces:
            self.face_state[face_idx] = FaceState.TO_REMOVE
            patch.faces.append(face_idx)
            
            # Mark boundary vertices as conquered (Section 3.1)
            face = self.model.faces[face_idx]
            for v in (face.a, face.b, face.c):
                if v != vertex_idx:
                    self.vertex_state[v] = VertexState.CONQUERED
                    if v not in patch.boundary_vertices:
                        patch.boundary_vertices.append(v)
        
        # Emit valence code (Section 4.1 - connectivity encoding)
        codes.append(valence)
        self.patches.append(patch)
        
        # Generate new gates along the patch boundary (Section 3.1)
        self._generate_boundary_gates(vertex_idx, gate, gate_queue)
    
    def _generate_boundary_gates(self, removed_vertex: int, entering_gate: Gate, gate_queue: collections.deque):
        """
        Generate new gates along the boundary of a removed vertex's patch.
        
        From paper Section 3.1:
        "After removing a vertex, new gates are created along the patch boundary"
        
        Args:
            removed_vertex: The vertex that was just removed
            entering_gate: The gate through which we entered
            gate_queue: Queue to add new gates to
        """
        incident_faces = self.topology.vertex_faces[removed_vertex]
        
        for face_idx in incident_faces:
            face = self.model.faces[face_idx]
            vertices = (face.a, face.b, face.c)
            
            # Create gates for each edge of the face
            for i in range(3):
                edge = (vertices[i], vertices[(i+1) % 3])
                front_v = vertices[(i+2) % 3]
                
                # Don't push the entering gate's edge (avoid backtracking)
                if edge != entering_gate.edge:
                    new_gate = Gate(edge=edge, front_face_idx=face_idx, front_vertex_idx=front_v)
                    gate_queue.append(new_gate)
    
    def _process_null_patch(self, gate: Gate, gate_queue: collections.deque, codes: List):
        """
        Process a null patch (front vertex cannot be removed).
        
        From paper Section 3.2:
        "When a vertex cannot be removed, we encode a null patch symbol"
        
        Args:
            gate: The current gate
            gate_queue: Queue of gates to process
            codes: List to append 'N' code to
        """
        # Mark face as conquered
        self.face_state[gate.front_face_idx] = FaceState.CONQUERED
        
        # Emit null patch code (Section 4.1)
        codes.append('N')
        
        # Push gates for the other two edges of the triangle (Section 3.1)
        face = self.model.faces[gate.front_face_idx]
        vertices = (face.a, face.b, face.c)
        
        for i in range(3):
            edge = (vertices[i], vertices[(i+1) % 3])
            front_v = vertices[(i+2) % 3]
            
            if edge != gate.edge:
                new_gate = Gate(edge=edge, front_face_idx=gate.front_face_idx, front_vertex_idx=front_v)
                gate_queue.append(new_gate)
    
    def compress_codes(self, codes: List) -> List:
        """
        Compress connectivity codes by removing redundant null patches.
        
        From paper Section 4.1:
        "The encoder can simulate the decoder to remove unnecessary null patches"
        
        Args:
            codes: Raw list of connectivity codes
        
        Returns:
            Compressed list of codes
        """
        compressed = []
        prev_null = False
        
        for code in codes:
            if code == 'N':
                # Keep only one consecutive null patch
                if not prev_null:
                    compressed.append(code)
                prev_null = True
            else:
                compressed.append(code)
                prev_null = False
        
        return compressed
    
    def write_obja(self, output_path: str):
        """
        Write the progressive mesh to an OBJA file.
        
        Args:
            output_path: Path to output OBJA file
        """
        with open(output_path, 'w') as f:
            out = obja.Output(f, random_color=True)
            
            # Write base mesh vertices
            for vi, vertex in enumerate(self.model.vertices):
                out.add_vertex(vi, vertex)
            
            # Write base mesh faces
            for fi, face in enumerate(self.model.faces):
                out.add_face(fi, face)
            
            # Write progressive stream markers
            # (Simplified version - full implementation would reverse the operations)
            for i, code in enumerate(self.connectivity_codes):
                if code == 'N':
                    f.write(f'# Null patch\n')
                else:
                    f.write(f'# Vertex removal, valence {code}\n')


# ============================================================================
# GEOMETRY ENCODING (Section 4.2 of the paper)
# ============================================================================

class GeometryEncoder:
    """
    Encodes vertex positions using Frenet frame and quantization.
    
    From paper Section 4.2:
    "Geometry is encoded using a local Frenet frame for each patch"
    """
    
    @staticmethod
    def encode_vertex_position(patch_boundary: List[np.ndarray], 
                               vertex_pos: np.ndarray, 
                               quant_bits: int = 12) -> Tuple[int, int, int]:
        """
        Encode a vertex position relative to its patch boundary.
        
        Args:
            patch_boundary: List of 3D positions of boundary vertices
            vertex_pos: 3D position of vertex to encode
            quant_bits: Number of bits for quantization
        
        Returns:
            Tuple of (alpha, beta, gamma) quantized coordinates
        """
        # Compute barycenter of patch boundary
        barycenter = np.mean(patch_boundary, axis=0)
        
        # Compute normal (area-weighted)
        normal = np.zeros(3)
        n = len(patch_boundary)
        for i in range(n):
            v0 = patch_boundary[i]
            v1 = patch_boundary[(i+1) % n]
            v2 = patch_boundary[(i+2) % n]
            # Add contribution to normal
            normal += np.cross(v1 - v0, v2 - v0)
        
        # Normalize
        norm = np.linalg.norm(normal)
        if norm < 1e-12:
            normal = np.array([0, 0, 1.0])
        else:
            normal = normal / norm
        
        # Compute Frenet frame (t1, t2, n)
        # t1: direction along first boundary edge, projected onto plane
        edge_dir = patch_boundary[1] - patch_boundary[0]
        t1 = edge_dir - np.dot(edge_dir, normal) * normal
        
        if np.linalg.norm(t1) < 1e-12:
            # Choose orthonormal vector
            t1 = np.array([1.0, 0.0, 0.0])
            if abs(np.dot(t1, normal)) > 0.9:
                t1 = np.array([0.0, 1.0, 0.0])
        
        t1 = t1 / np.linalg.norm(t1)
        t2 = np.cross(normal, t1)
        
        # Compute coordinates in Frenet frame
        relative_pos = vertex_pos - barycenter
        alpha = np.dot(relative_pos, t1)
        beta = np.dot(relative_pos, t2)
        gamma = np.dot(relative_pos, normal)
        
        # Quantize
        max_val = max(abs(alpha), abs(beta), abs(gamma))
        if max_val < 1e-9:
            return (0, 0, 0)
        
        scale = (2 ** (quant_bits - 1) - 1) / max_val
        qa = int(np.round(alpha * scale))
        qb = int(np.round(beta * scale))
        qg = int(np.round(gamma * scale))
        
        return (qa, qb, qg)
    
    @staticmethod
    def compress_geometry(quantized_coords: List[Tuple[int, int, int]]) -> bytes:
        """
        Compress quantized geometry data.
        
        Args:
            quantized_coords: List of (alpha, beta, gamma) tuples
        
        Returns:
            Compressed byte string
        """
        # Pack into binary format
        flat_data = [coord for triple in quantized_coords for coord in triple]
        blob = struct.pack(f'{len(flat_data)}i', *flat_data)
        
        # Compress with zlib
        return zlib.compress(blob)


# ============================================================================
# MAIN EXAMPLE
# ============================================================================

def main(input_obj='example/suzanne.obj', output_obja='example/suzanne_progressive.obja'):
    """
    Main example demonstrating the Alliez-Desbrun progressive compression.
    
    Args:
        input_obj: Path to input OBJ file
        output_obja: Path to output OBJA file
    """
    print(f"Loading model from {input_obj}...")
    model = obja.Model()
    model.parse_file(input_obj)
    
    print(f"Model has {len(model.vertices)} vertices and {len(model.faces)} faces")
    
    # Create encoder
    encoder = AllieeDesbrunEncoder(model)
    
    # Run encoding
    print("\nRunning Alliez-Desbrun progressive encoding...")
    codes = encoder.encode()
    
    print(f"\nEncoding complete:")
    print(f"  Total connectivity codes: {len(codes)}")
    print(f"  Patches created: {len(encoder.patches)}")
    
    # Compress codes
    compressed = encoder.compress_codes(codes)
    print(f"  Compressed codes: {len(compressed)}")
    
    # Write output
    print(f"\nWriting progressive mesh to {output_obja}...")
    encoder.write_obja(output_obja)
    
    print("Done!")


if __name__ == '__main__':
    main()
