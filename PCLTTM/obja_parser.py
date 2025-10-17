#!/usr/bin/env python3

import numpy as np

from data_structures import Face, Vertex


"""
    The OBJA file reader.
"""
class ObjaReader:

    def __init__(self):
        self.commands = dict()
        self._define_commands()

    def _define_commands(self):
        self.commands["v"] = self._parse_vertex
        self.commands["f"] = self._parse_face

    def parse_file(self, path):
        with open(path, "r") as file:
            for line in file.readlines():
                ret = self.__parse_line(line)
                if ret is not None:
                    yield ret 

    def _parse_vertex(self, *args):
        if len(args) != 3:
            raise ValueError("Vertex command requires 3 arguments")
        return Vertex(args)

    def _parse_face(self, *args):
        if len(args) != 3:
            raise ValueError("Face command requires 3 arguments")
        return Face(args)

    def __parse_line(self, line):
        """
        Parses a line of obja file.
        """
        self.line += 1

        split = line.split()

        if len(split) == 0:
            return
        
        command = split[0]
        if command in self.commands:
            if len(split) > 1:
                return self.commands[command](split[1:])
            else:
                return self.commands[command]()

class ObjaWriter:
    """
    The type for a model that outputs as obja.
    """

    def __init__(self, output, random_color=False):
        """
        Initializes the index mapping dictionaries.
        """
        self.vertex_mapping = dict()
        self.face_mapping = dict()
        self.output = output
        self.random_color = random_color

    def add_vertex(self, index, vertex):
        """
        Adds a new vertex to the model with the specified index.
        """
        self.vertex_mapping[index] = len(self.vertex_mapping)
        print('v {} {} {}'.format(vertex[0], vertex[1], vertex[2]), file=self.output)

    def edit_vertex(self, index, vertex):
        """
        Changes the coordinates of a vertex.
        """
        if len(self.vertex_mapping) == 0:
            print('ev {} {} {} {}'.format(index, vertex[0], vertex[1], vertex[2]), file=self.output)
        else:
            print('ev {} {} {} {}'.format(self.vertex_mapping[index] + 1, vertex[0], vertex[1], vertex[2]),
                  file=self.output)

    def add_face(self, index, face):
        """
        Adds a face to the model.
        """
        self.face_mapping[index] = len(self.face_mapping)
        print('f {} {} {}'.format(
            self.vertex_mapping[face.a] + 1,
            self.vertex_mapping[face.b] + 1,
            self.vertex_mapping[face.c] + 1,
        ),
            file=self.output
        )

        if self.random_color:
            print('fc {} {} {} {}'.format(
                len(self.face_mapping),
                random.uniform(0, 1),
                random.uniform(0, 1),
                random.uniform(0, 1)),
                file=self.output
            )

    def edit_face(self, index, face):
        """
        Changes the indices of the vertices of the specified face.
        """
        print('ef {} {} {} {}'.format(
            self.face_mapping[index] + 1,
            self.vertex_mapping[face.a] + 1,
            self.vertex_mapping[face.b] + 1,
            self.vertex_mapping[face.c] + 1
        ),
            file=self.output
        )