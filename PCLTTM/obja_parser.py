#!/usr/bin/env python3

import random
from .data_structures import Face, Vertex


"""
    OBJA file reader & writer.
"""


class ObjaReader:
    """
    Simple OBJ/OBJA-style reader that yields Vertex and Face objects.
    Vertices are stored in a list so faces can reference them by index.
    """

    def __init__(self):
        self.commands = {}
        self._define_commands()
        self.line = 0
        # list of parsed vertices so face indices can reference them
        self.vertices: list[Vertex] = []

    def _define_commands(self):
        self.commands["v"] = self._parse_vertex
        self.commands["f"] = self._parse_face

    def parse_file(self, path: str):
        """
        Parse a .obj/.obja file and yield Vertex / Face objects.
        """
        with open(path, "r") as file:
            for line in file:
                ret = self.__parse_line(line)
                if ret is not None:
                    yield ret

    # ------------------------------------------------------------------ #
    # Command handlers
    # ------------------------------------------------------------------ #

    def _parse_vertex(self, *args):
        """
        'v x y z' -> Vertex
        """
        if len(args) != 3:
            raise ValueError(
                f"Vertex command requires 3 arguments (line {self.line})"
            )

        try:
            x = float(args[0])
            y = float(args[1])
            z = float(args[2])
        except Exception as e:
            raise ValueError(
                f"Invalid vertex coordinates on line {self.line}: {args}"
            ) from e

        v = Vertex((x, y, z))
        self.vertices.append(v)
        return v

    def _parse_face(self, *args):
        """
        'f i j k' -> Face of 3 vertices.

        Indices in OBJ are 1-based; we convert to 0-based to index our
        self.vertices list.
        """
        if len(args) != 3:
            raise ValueError(
                f"Face command requires 3 arguments (line {self.line})"
            )

        verts = []
        for tok in args:
            # Support formats like '3', '3/1', '3/1/2' etc.
            idx_str = tok.split('/')[0]
            try:
                idx = int(idx_str)
            except Exception as e:
                raise ValueError(
                    f"Invalid face index on line {self.line}: {tok}"
                ) from e

            if idx == 0 or idx > len(self.vertices):
                raise IndexError(
                    f"Face index out of range on line {self.line}: {idx}"
                )

            verts.append(self.vertices[idx - 1])

        # Create a Face using actual Vertex objects
        return Face(tuple(verts))

    # ------------------------------------------------------------------ #
    # Main line dispatcher
    # ------------------------------------------------------------------ #

    def __parse_line(self, line: str):
        """
        Parses a line of an OBJ/OBJA file.
        Ignores empty lines and comments.
        """
        self.line += 1

        # Strip comments
        line = line.split('#', 1)[0].strip()
        if not line:
            return None

        split = line.split()
        command = split[0]

        if command in self.commands:
            if len(split) > 1:
                # Pass remaining tokens as *args to the handler
                return self.commands[command](*split[1:])
            else:
                return self.commands[command]()

        # Unknown command => ignore silently
        return None


class ObjaWriter:
    """
    The type for a model that outputs as OBJA.

    NOTE: This writer assumes:
    - `add_vertex(index, vertex)` is called with a coordinate triple
      (x, y, z) or something indexable like that.
    - `add_face(index, face)` is called with an object that has
      attributes `.a`, `.b`, `.c` which are **vertex indices**
      consistent with the `index` used in `add_vertex`.
    """

    def __init__(self, output, random_color: bool = False):
        """
        Initializes the index mapping dictionaries.

        :param output: a file-like object to write to.
        :param random_color: if True, writes random face colors (fc lines).
        """
        self.vertex_mapping: dict[int, int] = {}
        self.face_mapping: dict[int, int] = {}
        self.output = output
        self.random_color = random_color

    # ------------------------------------------------------------------ #
    # Vertex handling
    # ------------------------------------------------------------------ #

    def add_vertex(self, index: int, vertex):
        """
        Adds a new vertex to the model with the specified index.

        `vertex` is expected to be something like a 3-tuple (x, y, z)
        or an object supporting vertex[0], vertex[1], vertex[2].
        """
        self.vertex_mapping[index] = len(self.vertex_mapping)
        print(
            "v {} {} {}".format(vertex[0], vertex[1], vertex[2]),
            file=self.output,
        )

    def edit_vertex(self, index: int, vertex):
        """
        Changes the coordinates of a vertex.

        If vertices have not yet been remapped, prints the original index;
        otherwise uses the internal 1-based mapped index.
        """
        if len(self.vertex_mapping) == 0:
            print(
                "ev {} {} {} {}".format(
                    index, vertex[0], vertex[1], vertex[2]
                ),
                file=self.output,
            )
        else:
            print(
                "ev {} {} {} {}".format(
                    self.vertex_mapping[index] + 1,
                    vertex[0],
                    vertex[1],
                    vertex[2],
                ),
                file=self.output,
            )

    # ------------------------------------------------------------------ #
    # Face handling
    # ------------------------------------------------------------------ #

    def add_face(self, index: int, face):
        """
        Adds a face to the model.

        `face` is expected to have attributes `.a`, `.b`, `.c` which are
        vertex indices (the same indices used in add_vertex).
        """
        self.face_mapping[index] = len(self.face_mapping)
        print(
            "f {} {} {}".format(
                self.vertex_mapping[face.a] + 1,
                self.vertex_mapping[face.b] + 1,
                self.vertex_mapping[face.c] + 1,
            ),
            file=self.output,
        )

        if self.random_color:
            print(
                "fc {} {} {} {}".format(
                    len(self.face_mapping),
                    random.uniform(0, 1),
                    random.uniform(0, 1),
                    random.uniform(0, 1),
                ),
                file=self.output,
            )

    def edit_face(self, index: int, face):
        """
        Changes the indices of the vertices of the specified face.
        """
        print(
            "ef {} {} {} {}".format(
                self.face_mapping[index] + 1,
                self.vertex_mapping[face.a] + 1,
                self.vertex_mapping[face.b] + 1,
                self.vertex_mapping[face.c] + 1,
            ),
            file=self.output,
        )
