from meshtool.filters.base_filters import PrintFilter
import collada


def printMeshInfo(mesh):
    indent = "  "

    print(f"Cameras: {len(mesh.cameras)}")
    for cam in mesh.cameras:
        print(indent, cam)

    print(f"Lights: {len(mesh.lights)}")
    for light in mesh.lights:
        print(indent, light)

    print(f"Materials: {len(mesh.materials)}")
    for material in mesh.materials:
        print(indent, material)

    print(f"Effects: {len(mesh.effects)}")
    for effect in mesh.effects:
        print(indent, effect)

    print(f"Images: {len(mesh.images)}")
    for image in mesh.images:
        print(indent, image)

    print(f"Geometries: {len(mesh.geometries)}")
    for geom in mesh.geometries:
        print(indent, geom)
        for srcid, src in geom.sourceById.items():
            if isinstance(src, collada.source.Source):
                print(indent, indent, f"{srcid},{src}")
        for prim in geom.primitives:
            print(indent, indent, prim)


def FilterGenerator():
    class PrintInfoFilter(PrintFilter):
        def __init__(self):
            super(PrintInfoFilter, self).__init__(
                "print_info", "Prints a bunch of information about the mesh to the console"
            )

        def apply(self, mesh):
            printMeshInfo(mesh)
            return mesh

    return PrintInfoFilter()


from meshtool.filters import factory

factory.register(FilterGenerator().name, FilterGenerator)
