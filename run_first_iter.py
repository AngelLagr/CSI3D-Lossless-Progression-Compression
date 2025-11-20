import numpy as np
from PCLTTM import PCLTTM

def main():
    """
    Runs the program on the model given as parameter.
    """
    np.seterr(invalid='raise')
    model = PCLTTM()
    model.parse_file('example/crude_sphere_6.obj')

    model.compress()


if __name__ == '__main__':
    main()