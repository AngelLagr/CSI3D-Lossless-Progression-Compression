# PCLTTM/obja_writer.py

from .mesh import MeshTopology

def write_obja_from_mesh(mesh: MeshTopology, path: str) -> None:
    vertices = sorted(mesh.get_vertices())
    indices = {v: i for i, v in enumerate(vertices)}  # 0-based pour l’instant

    with open(path, "w") as f:
        # 1) sommets
        for v in vertices:
            x, y, z = v.position
            f.write(f"v {x} {y} {z}\n")

        # 2) faces uniques
        seen = set()
        for v in vertices:
            for face in mesh.get_faces(v):
                if face is None:
                    continue
                vs = tuple(face.vertices)
                key = frozenset(vs)
                if key in seen:
                    continue
                seen.add(key)

        for face_verts in seen:
            sorted_verts = sorted(face_verts, key=lambda vv: indices[vv])
            i, j, k = [indices[vv] + 1 for vv in sorted_verts]  # +1 car JS fait -1
            f.write(f"f {i} {j} {k}\n")
