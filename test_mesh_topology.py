

from PCLTTM.mesh import MeshTopology


def main():
    mesh = MeshTopology.from_obj_file("example/suzanne.obj")

    print("Number of vertices:", len(list(mesh.get_vertices())))

    # pick one vertex
    v = next(iter(mesh.get_vertices()))
    print("Sample vertex:", v)
    print("Valence:", mesh.get_valence(v))
    print("Connected vertices:", mesh.get_connected_vertices(v))
    print("Faces around vertex:", mesh.get_faces(v))

    # optional: export back to OBJ just to see it works without crashing
    mesh.export_to_obj("example/suzanne_roundtrip.obj")
    print("Exported example/suzanne_roundtrip.obj")


if __name__ == "__main__":
    main()
