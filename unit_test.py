from PCLTTM.data_structures.face import Face
from PCLTTM.data_structures.vertex import Vertex

def test_vertex_ordering():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))

    s1 = sorted({v1, v2, v3})
    s2 = sorted([v3, v2, v1])
    return s1 == s2

def test_face_hashing():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))
    f1 = Face((v1, v2, v3))
    f2 = Face((v3, v2, v1))
    f3 = Face((v2, v1, v3))

    k1 = hash(f1)
    k2 = hash(f2)
    k3 = hash(f3)

    return k1 == k2 and k2 == k3

def test_vertex_in_set():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((2, 2, 3))
    v3 = Vertex((1, 2, 3))

    s = set()
    s.add(v1)
    s.add(v2)
    s.add(v3)

    return len(s) == 2

def test_face_in_set():
    v1 = Vertex((1, 2, 3))
    v2 = Vertex((1, 3, 4))
    v3 = Vertex((2, 1, 3))
    v4 = Vertex((4, 3, 1))

    f1 = Face((v1, v2, v3))
    f2 = Face((v2, v1, v4))
    f3 = Face((v3, v2, v1))
    f4 = Face((v2, v1, v3))

    s = set()
    s.add(f1)
    s.add(f2)
    s.add(f3)
    s.add(f4)

    return len(s) == 2

def main():
    print("Vertex ordering: ", test_vertex_ordering())
    print("Face hashing: ", test_face_hashing())
    print("Vertex in set: ", test_vertex_in_set())
    print("Face in set: ", test_face_in_set())



if __name__ == '__main__':
    main()