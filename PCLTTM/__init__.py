import PCLTTM.data_structures.constants as constants
from data_structures import *
import mesh
import PCLTTM.obja_parser as obja_parser  

from typing import List, Tuple, Optional, Set, Dict, override


# ============================================================================
# ALGORITHM IMPLEMENTATION
# ============================================================================

class PCLTTM(obja_parser.Model):
    """
    Implements the valence-driven conquest algorithm from Alliez-Desbrun 2001.
    """
    def __init__(self, model):
        #example: self.gates = []
        pass

    @override
    def parse_line(self, line: str):
        pass
    
    
    def vertex_removal(self):
        _retriangulate_patch([], {})
        pass


    def _retriangulate_patch(boundary_vertices: List[int], tags: Dict[int, VertexTag]) -> List[Tuple[int, int, int]]:
        """
        Deterministic retriangulation of a patch polygon.
        
        According to the paper (Section 3.5 Fig.9):
        - Uses tag-based method to ensure encoder/decoder produce same triangulation
        - Tags (+/-) are assigned to boundary vertices during conquest
        - The retriangulation is deterministic based on valence and tags
        
        Args:
            boundary_vertices: Ordered list of vertices on patch boundary (CCW)
            tags: Dictionary mapping vertex indices to their tags (PLUS/MINUS)
        
        Returns:
            List of faces (triplets of vertex indices) forming the triangulation
        """
        n = len(boundary_vertices)
        if n < 3:
            return 
        
        

