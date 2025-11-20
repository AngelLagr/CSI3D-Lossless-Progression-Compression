import numpy as np
from PCLTTM import PCLTTM
import copy
def main():
    """
    Runs the program on the model given as parameter.
    """
    np.seterr(invalid='raise')
    
    model = PCLTTM()
    model.parse_file('example/icosphere.obj')
    
    num_vertex = len(model.mesh.get_vertices()) if model.mesh is not None else 0
    iteration_compress = 0

    model_iter = copy.deepcopy(model)
    initial_gate = model_iter.mesh.get_random_gate()
    new_num_vertex = -1
    while  new_num_vertex != num_vertex :
        
        iteration_compress += 1
        model_iter.compress(iteration_compress, initial_gate)
        model_iter.mesh.export_to_obj(f"compression_step_{iteration_compress}.obj")
        num_vertex = new_num_vertex
        new_num_vertex = len(model_iter.mesh.get_vertices())
        if new_num_vertex == 4:
            break
        model_iter = PCLTTM()
        model_iter.parse_file(f'compression_step_{iteration_compress}.obj')
        initial_gate = model_iter.mesh.get_random_gate()
        print(f"After iteration {iteration_compress}, number of vertices: {new_num_vertex}, old: {num_vertex}")
    print("Compression complete.")





if __name__ == '__main__':
    main()