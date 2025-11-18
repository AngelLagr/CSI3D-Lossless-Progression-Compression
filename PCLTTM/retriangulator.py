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

    def standarize_retriangulation(self, patch: Patch) -> List[Face]:
        pass

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

        front_vertex = current_gate.front_vertex

        self.tag_propagation(mesh, patch_oriented_vertex, left_tag, right_tag)

        self.triangulate_table(
            mesh, front_vertex, patch_oriented_vertex, left_tag, right_tag,  valence)

    def tag_propagation(self, mesh,
                        patch_oriented_vertex: List[Vertex],
                        left_tag: str,
                        right_tag: str,
                        ) -> Dict[int, str]:
        # l'idée est d'alterner les + et les -, mais le côté droit de la gate d'entrée est toujours prioritaire.
        # Normalise les tags d'entrée pour éviter les valeurs Default qui provoquent un KeyError.
        alternance = {
            RetriangulationTag.Minus: RetriangulationTag.Plus,
            RetriangulationTag.Plus: RetriangulationTag.Minus,
        }

        # Normalisation: si un côté est Default, on lui donne un tag cohérent.
        # - Si les deux sont Default: priorité à droite => right: '-', left: '+'
        # - Si un seul est Default: on lui affecte l'alternance de l'autre pour garantir left != right
        if left_tag == RetriangulationTag.Default and right_tag == RetriangulationTag.Default:
            right_tag = RetriangulationTag.Minus
            left_tag = RetriangulationTag.Plus
        elif left_tag == RetriangulationTag.Default:
            # Garantit une alternance aux extrémités
            left_tag = alternance.get(right_tag, RetriangulationTag.Plus)
        elif right_tag == RetriangulationTag.Default:
            right_tag = alternance.get(left_tag, RetriangulationTag.Minus)

        # Choix du côté de départ selon la règle d'origine
        if left_tag != right_tag:
            if left_tag == RetriangulationTag.Minus:
                start_tag = left_tag
                start_side = 'left'
            else:
                start_tag = right_tag
                start_side = 'right'
        else:
            start_tag = right_tag
            start_side = 'right'

        if start_side == 'right':
            tag = start_tag
            for vertex in patch_oriented_vertex[1:-1]:
                tag = alternance[tag]
                self.retriangulation_tags[vertex] = tag
        else:
            tag = start_tag
            for vertex in reversed(patch_oriented_vertex[1:-1]):
                tag = alternance[tag]
                self.retriangulation_tags[vertex] = tag

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
                        mesh.set_orientation((pov[0], pov[4]), pov[5])
                        mesh.set_orientation((pov[2], pov[0]), pov[1])
                        mesh.set_orientation((pov[4], pov[2]), pov[3])
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
