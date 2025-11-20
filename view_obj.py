import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def load_obj(path):
    vertices = []
    faces = []

    with open(path, 'r') as f:
        for line in f:
            if line.startswith('v '):
                _, x, y, z = line.strip().split()
                vertices.append((float(x), float(y), float(z)))
            elif line.startswith('f '):
                parts = line.strip().split()[1:]
                face = [int(p.split('/')[0]) - 1 for p in parts]
                faces.append(face)

    return vertices, faces


# --------------------------
#      MAIN
# --------------------------
obj_path = "compression_step_2.obj"   # <-- mets ton fichier ici
vertices, faces = load_obj(obj_path)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot faces
for face in faces:
    x = [vertices[i][0] for i in face]
    y = [vertices[i][1] for i in face]
    z = [vertices[i][2] for i in face]
    ax.plot(x + [x[0]], y + [y[0]], z + [z[0]])

# Plot vertices + labels
for i, (x, y, z) in enumerate(vertices):
    ax.scatter(x, y, z, s=10)
    ax.text(x, y, z, f"{i}: ({x:.2f}, {y:.2f}, {z:.2f})", fontsize=6)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.show()
