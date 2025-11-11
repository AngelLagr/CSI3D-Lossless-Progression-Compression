from typing import List, Tuple, Dict
from .data_structures.face import Face
from .data_structures.vertex import Vertex
from .data_structures.gate import Gate
from .data_structures.constants import RetriangulationTag
class Retriangulator:
    """
    Retriangulation 'table' (figure 9) d'un patch polygonal (valence 3..6)
    - Entrée : liste orientée CCW des sommets du patch: [L, ..., R]
    - Tags aux extrémités (L,R) : '-', '+'
    - Propagation des tags par alternance, priorité au côté droit en cas d'égalité.
    - Triangulation par ear-clipping : priorité aux sommets tagués '-'.
    """
    def __init__(self):
        self.retriangulation_tags = dict() # Hash(Vertex) -> Retriangulation tag (+ or -)

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
            - new_tags: dict {sommet_global: tag '+'|'-'} propagés sur le bord
        """
        assert 3 <= valence <= 6, "valence non comprise dans [3, 6]"
        assert len(patch_oriented_vertex) == valence, \
            "valence et taille de patch_oriented_vertex incompatibles"
        
        left_vertex, right_vertex = current_gate.edge
        left_tag = self.retriangulation_tags.get(left_vertex, RetriangulationTag.Default)
        right_tag = self.retriangulation_tags.get(right_vertex, RetriangulationTag.Default)

        front_vertex = current_gate.front_vertex
        
        self.tag_propagation(mesh, patch_oriented_vertex, left_tag, right_tag)

        self.triangulate_table(mesh, front_vertex, patch_oriented_vertex, left_tag, right_tag,  valence)

  
    def tag_propagation(self, mesh,
        patch_oriented_vertex: List[Vertex],
        left_tag: str,
        right_tag: str,
    ) -> Dict[int, str]:
        # l'idée est d'alterner les + et les -, mais le coté droit de la gate d'entré est toujours prioritaire
    # là ou l'aternance doit etre respecté et le moins est prioritaire sur le +

        # Pour chchoisir le coté prioritaire on regarde si le coté droit est différent du coté gauche
        # sinon on commence du coté droit
        alternance = {RetriangulationTag.Minus: RetriangulationTag.Plus, RetriangulationTag.Plus: RetriangulationTag.Minus}
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
        self, mesh, front_vertex : Vertex, 
        patch_oriented_vertex: List[int],
        left_tag, right_tag,
        valence: int,
    ) -> List[Face]:
            # On construit la table, donc on parcourt tous les sommets du patch orienté
    # d'abord on regarde si le nombre de sommet tagués moins ou tagués plus est différents
    # si c'est le cas on minimise la valance du coté droit de la gate
    # Sinon
    # On regarde si il y a un sommet taggé '-', si c'est le cas, on relie les deux autres extrémités
    # Sinon on relie le premier sommet avec le troisieme sommet du polygone

        mesh.remove_vertex(front_vertex)
        if valence < 3 or valence > 6:
            return []
        
        pov = patch_oriented_vertex  # alias court

        # python 3.10+ pattern matching
        match (left_tag, right_tag):
            case (RetriangulationTag.Plus, RetriangulationTag.Minus):
                match valence:
                    case 4:
                        # priorité au '-' de droite → diagonale (1,3)
                        mesh.add_edge(pov[1], pov[3])
                    case 5:
                        # priorité au '-' de droite → éventail depuis 4
                        mesh.add_edge(pov[4], pov[1])
                        mesh.add_edge(pov[1], pov[3])
                    case 6:
                        # priorité au '-' de droite → éventail depuis 5
                        mesh.add_edge(pov[5], pov[1])
                        mesh.add_edge(pov[3], pov[1])
                        mesh.add_edge(pov[5], pov[3])
                    case _:
                        pass
            case (RetriangulationTag.Minus, RetriangulationTag.Plus):
                match valence:
                    case 4:
                        # priorité au '-' de gauche → diagonale (0,2)
                        mesh.add_edge(pov[0], pov[2])
                    case 5:
                        # priorité au '-' de gauche → éventail depuis 0
                        mesh.add_edge(pov[1], pov[3])
                        mesh.add_edge(pov[0], pov[3])
                    case 6:
                        # priorité au '-' de gauche → éventail depuis 0
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[2], pov[4])
                        mesh.add_edge(pov[0], pov[4])
                    case _:
                        pass
            case (RetriangulationTag.Plus, RetriangulationTag.Plus):
                match valence:
                    case 4:
                        # gate ++ OU gate -- : priorité côté droit → diagonale (1,3)
                        mesh.add_edge(pov[0], pov[2])
                    case 5:
                        # ++ ou -- : priorité côté droit → éventail depuis 4
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[4], pov[2])
                    case 6:
                        # ++ ou -- : priorité côté droit → éventail depuis 5
                        mesh.add_edge(pov[0], pov[2])
                        mesh.add_edge(pov[2], pov[4])
                        mesh.add_edge(pov[0], pov[4])
                    case _:
                        pass
            case _: # (RetriangulationTag.Minus, RetriangulationTag.Minus)
                match valence:
                    case 4:
                        mesh.add_edge(pov[1], pov[3])
                    case 5:
                        mesh.add_edge(pov[1], pov[4])
                        mesh.add_edge(pov[1], pov[3])
                    case 6:
                        mesh.add_edge(pov[5], pov[1])
                        mesh.add_edge(pov[3], pov[1])
                        mesh.add_edge(pov[5], pov[3])
                    case _:
                        pass


    


       