from typing import List, Tuple, Dict
from data_structures.face import Face
from data_structures.vertex import Vertex
from data_structures.gate import Gate
class Retriangulator:
    """
    Retriangulation 'table' (figure 9) d'un patch polygonal (valence 3..6)
    - Entrée : liste orientée CCW des sommets du patch: [L, ..., R]
    - Tags aux extrémités (L,R) : '-', '+'
    - Propagation des tags par alternance, priorité au côté droit en cas d'égalité.
    - Triangulation par ear-clipping : priorité aux sommets tagués '-'.
    """

    def retriangulate(
        self,
        mesh,
        valence: int, current_gate: Gate,
        patch_oriented_vertex: List[int],
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
        left_tag, right_tag = left_vertex.retriangulation_tag(), right_vertex.retriangulation_tag()

        front_vertex = current_gate.front_vertex
        
        self.tag_propagation(mesh, patch_oriented_vertex, left_tag, right_tag)

        self.triangulate_table(mesh, front_vertex, patch_oriented_vertex, left_tag, right_tag,  valence)



  
    def tag_propagation(mesh,
        patch_oriented_vertex: List[int],
        left_tag: str,
        right_tag: str,
    ) -> Dict[int, str]:
        # l'idée est d'alterner les + et les -, mais le coté droit de la gate d'entré est toujours prioritaire
    # là ou l'aternance doit etre respecté et le moins est prioritaire sur le +

        # Pour chchoisir le coté prioritaire on regarde si le coté droit est différent du coté gauche
        # sinon on commence du coté droit
        alternance = {'-':'+', '+':'-'}
        if left_tag != right_tag:
            if left_tag == '-':
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
            for i in patch_oriented_vertex[1:-1]:
                tag = alternance[tag]
                mesh.set_retriangulation_tag(patch_oriented_vertex[i], tag)
             
        else:
            tag = start_tag
            for i in reversed(patch_oriented_vertex[1:-1]):
                tag = alternance[tag]
                mesh.set_retriangulation_tag(patch_oriented_vertex[i], tag)
            


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

        pov = patch_oriented_vertex  # alias court

        if valence == 3:
            # rien à ajouter
            pass

        elif valence == 4:
            if left_tag == '+' and right_tag == '-':
                # priorité au '-' de droite → diagonale (1,3)
                mesh.add_edge(pov[1], pov[3])
            elif left_tag == '-' and right_tag == '+':
                # priorité au '-' de gauche → diagonale (0,2)
                mesh.add_edge(pov[0], pov[2])
            elif left_tag == '+' and right_tag == '+':
                # gate ++ OU gate -- : priorité côté droit → diagonale (1,3)
                mesh.add_edge(pov[0], pov[2])
            else :
                mesh.add_edge(pov[1], pov[3])

        elif valence == 5:
            if left_tag == '-' and right_tag == '+':
                # priorité au '-' de gauche → éventail depuis 0
                mesh.add_edge(pov[1], pov[3])
                mesh.add_edge(pov[0], pov[3])
            elif left_tag == '+' and right_tag == '-':
                # priorité au '-' de droite → éventail depuis 4
                mesh.add_edge(pov[4], pov[1])
                mesh.add_edge(pov[1], pov[3])
            elif left_tag == '+' and right_tag == '+':
                # ++ ou -- : priorité côté droit → éventail depuis 4
                mesh.add_edge(pov[0], pov[2])
                mesh.add_edge(pov[4], pov[2])
            else:

                mesh.add_edge(mesh, pov[1], pov[4])
                mesh.add_edge(mesh, pov[1], pov[3])

        elif valence == 6:
            if left_tag == '-' and right_tag == '+':
                # priorité au '-' de gauche → éventail depuis 0
                mesh.add_edge(mesh, pov[0], pov[2])
                mesh.add_edge(mesh, pov[2], pov[4])
                mesh.add_edge(mesh, pov[0], pov[4])
            elif left_tag == '+' and right_tag == '-':
                # priorité au '-' de droite → éventail depuis 5
                mesh.add_edge(mesh, pov[5], pov[1])
                mesh.add_edge(mesh, pov[3], pov[1])
                mesh.add_edge(mesh, pov[5], pov[3])
            elif left_tag == '+' and right_tag == '+':
                # ++ ou -- : priorité côté droit → éventail depuis 5
                mesh.add_edge(mesh, pov[0], pov[2])
                mesh.add_edge(mesh, pov[2], pov[4])
                mesh.add_edge(mesh, pov[0], pov[4])
            else :
                mesh.add_edge(mesh, pov[5], pov[1])
                mesh.add_edge(mesh, pov[3], pov[1])
                mesh.add_edge(mesh, pov[5], pov[3])


    


       