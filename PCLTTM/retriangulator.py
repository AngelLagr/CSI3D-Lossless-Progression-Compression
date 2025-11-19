from typing import List, Tuple, Dict

from PCLTTM.data_structures.patch import Patch
from .data_structures.face import Face
from .data_structures.vertex import Vertex
from .data_structures.gate import Gate
from .data_structures.constants import RetriangulationTag


class Retriangulator:
    """
    Retriangulation 'table' (figure 9) d'un patch polygonal (valence 3..6)
    - EntrÃ©e : liste orientÃ©e CCW des sommets du patch: [L, ..., R]
    - Tags aux extrÃ©mitÃ©s (L,R) : '-', '+'
    - Propagation des tags par alternance, prioritÃ© au cÃ´tÃ© droit en cas d'Ã©galitÃ©.
    - Triangulation par ear-clipping : prioritÃ© aux sommets taguÃ©s '-'.
    """

    def __init__(self):
        self.retriangulation_tags = dict()  # Hash(Vertex) -> Retriangulation tag (+ or -)

    def retriangulate(
        self,
        mesh,
        valence: int, current_gate: Gate,
        patch_oriented_vertex: List[Vertex],
    ) -> Tuple[List[Face], Dict[int, str]]:
        """
        Args:
            valence: nombre de sommets du patch (3..6)
            left_tag, right_tag: '-' ou '+'
            patch_oriented_vertex: liste CCW des sommets du patch,
                                   [L, v1, ..., vk, R]
        Returns:
            (triangles, new_tags)
            - triangles: liste de triangles en indices *globaux*
            - new_tags: dict {sommet_global: tag '+'|'-'} propagÃ©s sur le bord
        """
        assert 3 <= valence <= 6, "valence non comprise dans [3, 6]"
        assert len(patch_oriented_vertex) == valence, \
            "valence et taille de patch_oriented_vertex incompatibles"

        left_vertex, right_vertex = current_gate.edge
        left_tag = self.retriangulation_tags.get(
            left_vertex, RetriangulationTag.Default)
        right_tag = self.retriangulation_tags.get(
            right_vertex, RetriangulationTag.Default)

        if left_tag == RetriangulationTag.Default or right_tag == RetriangulationTag.Default:
            raise RuntimeError("Retriangulation tags must be defined for gate edge vertices")

        front_vertex = current_gate.front_vertex

        starting_tag = right_tag  
        # Little edge case where on impair valence when the left and right tags are different we need to start from the opposite tag
        if valence in [3, 5] and left_tag != right_tag and starting_tag == RetriangulationTag.Plus:
            starting_tag = RetriangulationTag.Minus
        self.tag_propagation(mesh, [v for v in patch_oriented_vertex if v not in current_gate.edge], starting_tag)

        self.triangulate_table(
            mesh, front_vertex, patch_oriented_vertex, left_tag, right_tag,  valence)

    def tag_propagation(self, mesh, vertex_to_tag: List[Vertex], starting_tag: RetriangulationTag):
        # l'idée est d'alterner les + et les -, mais le côté droit de la gate d'entrée est toujours prioritaire.
        # Normalise les tags d'entrée pour éviter les valeurs Default qui provoquent un KeyError.
        tags = [RetriangulationTag.Minus, RetriangulationTag.Plus]
        index = tags.index(starting_tag) if starting_tag in tags else 0
        for vertex in vertex_to_tag:
            index = (index + 1) % len(tags)
            if self.retriangulation_tags[vertex] == RetriangulationTag.Default:
                self.retriangulation_tags[vertex] = tags[index]
        
    def triangulate_table(
        self, mesh, front_vertex: Vertex,
        patch_oriented_vertex: List[Vertex],
        left_tag, right_tag,
        valence: int,
    ) -> List[Face]:
        # On construit la table, donc on parcourt tous les sommets du patch orientÃ©
        # d'abord on regarde si le nombre de sommet taguÃ©s moins ou taguÃ©s plus est diffÃ©rents
        # si c'est le cas on minimise la valance du cotÃ© droit de la gate
        # Sinon
        # On regarde si il y a un sommet taggÃ© '-', si c'est le cas, on relie les deux autres extrÃ©mitÃ©s
        # Sinon on relie le premier sommet avec le troisieme sommet du polygone

        mesh.remove_vertex(front_vertex, force=True)
        if valence < 3 or valence > 6:
            return []

        pov = patch_oriented_vertex  # alias court
        print(pov)
        # python 3.10+ pattern matching
        match (left_tag, right_tag):
            case (RetriangulationTag.Plus, RetriangulationTag.Minus):
                match valence:
                    case 3:
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                    case 4:
                        # prioritÃ© au '-' de droite â†’ diagonale (1,3)
                        mesh.add_edge(pov[1], pov[3])
                        mesh.set_orientation((pov[1], pov[3]), pov[0])
                    case 5:
                        # prioritÃ© au '-' de droite â†’ Ã©ventail depuis 4
                        mesh.add_edge(pov[4], pov[1])
                        mesh.add_edge(pov[1], pov[3])
                        mesh.set_orientation((pov[3], pov[1]), pov[2])
                        mesh.set_orientation((pov[4], pov[1]), pov[3])
                    case 6:
                        # prioritÃ© au '-' de droite â†’ Ã©ventail depuis 5
                        mesh.add_edge(pov[5], pov[1])
                        mesh.add_edge(pov[3], pov[1])
                        mesh.add_edge(pov[5], pov[3])
                        mesh.set_orientation((pov[1], pov[5]), pov[0])
                        mesh.set_orientation((pov[5], pov[3]), pov[4])
                        mesh.set_orientation((pov[3], pov[1]), pov[2])
                    case _:
                        pass
            case (RetriangulationTag.Minus, RetriangulationTag.Plus):
                match valence:
                    case 3:
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                    case 4:
                        # prioritÃ© au '-' de gauche â†’ diagonale (0,2)
                        mesh.add_edge(pov[0], pov[2])
                        mesh.set_orientation((pov[0], pov[2]), pov[3])
                    case 5:
                        # prioritÃ© au '-' de gauche â†’ Ã©ventail depuis 0
                        mesh.add_edge(pov[1], pov[3])
                        mesh.add_edge(pov[0], pov[3])
                        mesh.set_orientation((pov[0], pov[3]), pov[4])
                        mesh.set_orientation((pov[3], pov[1]), pov[2])
                    case 6:
                        # prioritÃ© au '-' de gauche â†’ Ã©ventail depuis 0
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[2], pov[4])
                        mesh.add_edge(pov[0], pov[4])
                        mesh.set_orientation((pov[0], pov[4]), pov[2])
                        mesh.set_orientation((pov[2], pov[0]), pov[4])
                        mesh.set_orientation((pov[4], pov[2]), pov[0])
                    case _:
                        pass
            case (RetriangulationTag.Plus, RetriangulationTag.Plus):
                match valence:
                    case 3:
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                    case 4:
                        # gate ++ OU gate -- : prioritÃ© cÃ´tÃ© droit â†’ diagonale (1,3)
                        mesh.add_edge(pov[0], pov[2])
                        mesh.set_orientation((pov[0], pov[2]), pov[3])
                    case 5:
                        # ++ ou -- : prioritÃ© cÃ´tÃ© droit â†’ Ã©ventail depuis 4
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[4], pov[2])
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                        mesh.set_orientation((pov[4], pov[2]), pov[3])
                    case 6:
                        # ++ ou -- : prioritÃ© cÃ´tÃ© droit â†’ Ã©ventail depuis 5
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[2], pov[4])
                        mesh.add_edge(pov[0], pov[4])
                        mesh.set_orientation((pov[0], pov[4]), pov[5])
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                        mesh.set_orientation((pov[4], pov[2]), pov[3])
                    case _:
                        pass
            case _:  # (RetriangulationTag.Minus, RetriangulationTag.Minus)
                match valence:
                    case 3:
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                    case 4:
                        mesh.add_edge(pov[1], pov[3])
                        mesh.set_orientation((pov[1], pov[3]), pov[0])
                    case 5:
                        mesh.add_edge(pov[1], pov[4])
                        mesh.add_edge(pov[1], pov[3])
                        mesh.set_orientation((pov[2], pov[4]), pov[0])
                        mesh.set_orientation((pov[3], pov[1]), pov[2])
                    case 6:
                        mesh.add_edge(pov[5], pov[1])
                        mesh.add_edge(pov[3], pov[1])
                        mesh.add_edge(pov[5], pov[3])
                        mesh.set_orientation((pov[1], pov[5]), pov[0])
                        mesh.set_orientation((pov[5], pov[3]), pov[4])
                        mesh.set_orientation((pov[3], pov[1]), pov[2])
                    case _:
                        pass
