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
        valence: int,
        left_tag: str,
        right_tag: str,
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
        # -- validations --
        assert 3 <= valence <= 6, "valence non comprise dans [3, 6]"
        assert len(patch_oriented_vertex) == valence, \
            "valence et taille de patch_oriented_vertex incompatibles"
        
        # -- propagation des tags sur le bord --
        new_tags = self.tag_propagation(patch_oriented_vertex, left_tag, right_tag)

        # -- triangulation combinatoire (table) --
        triangles = self.triangulate_table(patch_oriented_vertex, new_tags,valence)

        return triangles, new_tags

  
    def tag_propagation(
        patch_oriented_vertex: List[int],
        left_tag: str,
        right_tag: str,
    ) -> Dict[int, str]:
        # l'idée est d'alterner les + et les -, mais le coté droit de la gate d'entré est toujours prioritaire
    # là ou l'aternance doit etre respecté et le moins est prioritaire sur le +
        new_tags: Dict[int,str] = {}
        L, R = patch_oriented_vertex[0], patch_oriented_vertex[-1]
        new_tags[R] = right_tag
        new_tags[L] = left_tag

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
            for i in reversed(patch_oriented_vertex[1:-1]):
                tag = alternance[tag]
                new_tags[i] = tag
        else:
            tag = start_tag
            for i in patch_oriented_vertex[1:-1]:
                tag = alternance[tag]
                new_tags[i] = tag


        return new_tags

    def _left(i: int, n: int) -> int:
        return (i - 1) % n

    def _right(i: int, n: int) -> int:
        return (i + 1) % n

    def triangulate_table(
        self,
        patch_oriented_vertex: List[int],
        new_tags: Dict[int, str],
        valence: int,
    ) -> List[Face]:
            # On construit la table, donc on parcourt tous les sommets du patch orienté
    # d'abord on regarde si le nombre de sommet tagués moins ou tagués plus est différents
    # si c'est le cas on minimise la valance du coté droit de la gate
    # Sinon
    # On regarde si il y a un sommet taggé '-', si c'est le cas, on relie les deux autres extrémités
    # Sinon on relie le premier sommet avec le troisieme sommet du polygone
        tag  = {i: new_tags[patch_oriented_vertex[i]] for i in range(valence)}
        
        triangles: List[Face] = []

        def left(i):  return (i-1) % len(patch_oriented_vertex)
        def right(i): return (i+1) % len(patch_oriented_vertex)

        nb_plus = sum(tag == '+' for tag in new_tags.values())
        nb_minus = sum(tag == '-' for tag in new_tags.values())

        # fonction pour vérifier si il y a des sommets "-" dans le   polynome
        def sommet_triangle() -> int:
            for i,c in enumerate(patch_oriented_vertex):
                if tag[c] == '-' :
                    return i
            return 0

        if nb_minus > nb_plus:
            ancr = 'left'
        else :
            ancr = 'right'

        if valence==3:
            triangles.append(Face(patch_oriented_vertex[0], patch_oriented_vertex[1], patch_oriented_vertex[2]))
        elif valence==4 and ancr == 'left':
            triangles.append(Face(patch_oriented_vertex[0], patch_oriented_vertex[1], patch_oriented_vertex[2]), (patch_oriented_vertex[2], patch_oriented_vertex[3], patch_oriented_vertex[0]))
        elif valence==5 and ancr == 'left':
            t1 = Face(patch_oriented_vertex[0], patch_oriented_vertex[1], patch_oriented_vertex[3])
            t2 = Face(patch_oriented_vertex[1], patch_oriented_vertex[2], patch_oriented_vertex[3])
            t3 = Face(patch_oriented_vertex[3], patch_oriented_vertex[4], patch_oriented_vertex[0])
            triangles.append(t1, t2, t3)
        elif valence==6 and ancr== 'left':
            t1 = Face(patch_oriented_vertex[0], patch_oriented_vertex[1], patch_oriented_vertex[2])
            t2 = Face(patch_oriented_vertex[2], patch_oriented_vertex[3], patch_oriented_vertex[4])
            t3 = Face(patch_oriented_vertex[0], patch_oriented_vertex[2], patch_oriented_vertex[4])
            t4 = Face(patch_oriented_vertex[0], patch_oriented_vertex[4], patch_oriented_vertex[5])
            triangles.append(t1, t2, t3, t4)
        else :
            while len(patch_oriented_vertex) > 3:
                i = sommet_triangle()
                a, b, c = patch_oriented_vertex[left(i)], patch_oriented_vertex[i], patch_oriented_vertex[right(i)]
                triangles.append(Face(a,b,c))
                del patch_oriented_vertex[i]
            triangles.append(Face(patch_oriented_vertex[0], patch_oriented_vertex[1], patch_oriented_vertex[2]))

        # Réutilisation des indices réels 
        triangles = [Face(patch_oriented_vertex[i], patch_oriented_vertex[j], patch_oriented_vertex[k]) for (i,j,k) in triangles]
        return triangles
    
    
