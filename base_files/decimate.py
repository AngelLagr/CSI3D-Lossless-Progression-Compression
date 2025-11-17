#!/usr/bin/env python3

import numpy as np

from .mesh import MeshTopology
from .obja_parser import ObjaWriter


class Decimater:
    """
    Very simple 'decimater' that does not really decimate:
    it just rewrites the mesh into OBJA format.

    This is a good smoke test for the whole pipeline:
    - parse OBJ -> MeshTopology
    - write OBJA with ObjaWriter
    """

    def __init__(self):
        self.mesh: MeshTopology | None = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def parse_file(self, path: str):
        """
        Load a Wavefront OBJ file and build the mesh topology.
        """
        self.mesh = MeshTopology.from_obj_file(path)

    # ------------------------------------------------------------------
    # "Decimation" / output
    # ------------------------------------------------------------------
    def contract(self, output):
        """
        Write the current mesh to OBJA format using ObjaWriter.

        For now, this is a no-op "decimation": we output all vertices
        and faces as-is. Once everything works, you can plug in your
        real decimation/progression code here.
        """
        if self.mesh is None:
            raise RuntimeError("Mesh not loaded. Call parse_file() first.")

        writer = ObjaWriter(output, random_color=True)

        # 1) Collect vertices in a stable order and index them
        vertices = list(self.mesh.get_vertices())
        index_by_vertex = {v: idx for idx, v in enumerate(vertices)}

        # Write vertices
        for idx, v in enumerate(vertices):
            x, y, z = v.position
            writer.add_vertex(idx, (x, y, z))

        # 2) Collect unique faces and write them
        seen_faces = set()
        face_index = 0

        for v in vertices:
            faces = self.mesh.get_faces(v)
            for f in faces:
                if f in seen_faces:
                    continue
                seen_faces.add(f)

                a, b, c = f.vertices

                # Minimal object with attributes a, b, c as expected by ObjaWriter
                class FaceObj:
                    pass

                face_obj = FaceObj()
                face_obj.a = index_by_vertex[a]
                face_obj.b = index_by_vertex[b]
                face_obj.c = index_by_vertex[c]

                writer.add_face(face_index, face_obj)
                face_index += 1
