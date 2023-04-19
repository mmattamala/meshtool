import collada
import os.path
from itertools import chain
from meshtool.filters.base_filters import FilterException


def materialParameterAsFloat(value, default=None):
    if isinstance(value, collada.material.Map):
        return default
    elif isinstance(value, tuple):
        return sum(value) / float(len(value))
    elif isinstance(value, float):
        return value
    else:
        return default


def formatMaterialField(field_name, value, mesh=None, mtlfilename=None):
    if isinstance(value, collada.material.Map):
        rel_img_path = value.sampler.surface.image.path
        # This let's relative paths get worked out, but since
        # sometimes this data is not going into files (e.g. when it's
        # going into a zip), this approach only works sometimes. For
        # other situations, like zips, you are responsible for making
        # sure the path is setup properly.
        if mesh is not None and mesh.filename is not None and mtlfilename is not None:
            # First we need to get the real relative path to the
            # texture by combining relative path to source dae +
            # relative path from dae to texture
            rel_img_path = os.path.join(os.path.dirname(mesh.filename), rel_img_path)
            # Then, use that to convert it to be relative to the mtl file.
            rel_img_path = os.path.relpath(rel_img_path, os.path.dirname(mtlfilename))
        return "map_%s %s" % (field_name, rel_img_path)
    elif isinstance(value, tuple):
        return "%s %f %f %f" % (field_name, value[0], value[1], value[2])
    elif isinstance(value, float):
        return "%s %f" % (field_name, value)
    else:
        return None


def write_mtl(mesh, fmtl, mtlfilename=None):
    """Write Wavefront OBJ-style materials to a file-like object.

    :param collada.Collada mesh:
      The collada mesh to get materials from
    :param fmtl:
      A file-like object to write material information to.
    :param str mtlfilename:
      The path to the material file being written, if it is truly a
      file. This is used to ensure paths to textures are correct.
    """

    for mtl in mesh.materials:
        print("newmtl", mtl.id, file=fmtl)
        if mtl.effect.ambient is not None:
            print(formatMaterialField("Ka", mtl.effect.ambient, mesh, mtlfilename), file=fmtl)
        if mtl.effect.diffuse is not None:
            print(formatMaterialField("Kd", mtl.effect.diffuse, mesh, mtlfilename), file=fmtl)
        if mtl.effect.specular is not None:
            print(formatMaterialField("Ks", mtl.effect.specular, mesh, mtlfilename), file=fmtl)
        if mtl.effect.shininess is not None:
            print(formatMaterialField("Ns", mtl.effect.shininess, mesh, mtlfilename), file=fmtl)
        # d and Tr are both used for transparency
        if mtl.effect.transparent is not None:
            transparent_float = materialParameterAsFloat(mtl.effect.transparent, default=1.0)
            print(formatMaterialField("d", transparent_float, mesh, mtlfilename), file=fmtl)
            print(formatMaterialField("Tr", transparent_float, mesh, mtlfilename), file=fmtl)

        # Illumination model: 1 = diffuse, 2 = with specular
        illum_model = 1 if mtl.effect.shadingtype in ["lambert", "constant"] else 2
        print("illum", illum_model, file=fmtl)

        print("", file=fmtl)


def write_obj(mesh, mtlfilename, f):
    """Write Wavefront OBJ contents of mesh to a file-like object."""

    f.write("mtllib %s\n" % mtlfilename)

    # Iterate through all primitives in each geometry instance
    vert_offset = 1
    norm_offset = 1
    tc_offset = 1
    for boundgeom in mesh.scene.objects("geometry"):
        f.write("# %s - %s\n" % (boundgeom.original.name, boundgeom.original.id))
        for boundprim in boundgeom.primitives():
            # Determine the properties of these primitives we're going
            # to use
            emit_normals = boundprim.normal is not None
            emit_texcoords = boundprim.texcoordset is not None and len(boundprim.texcoordset) > 0
            if emit_texcoords and len(boundprim.texcoordset) > 1:
                raise FilterException("OBJ only supports one texture coordinate set.")

            # Write transformed vertices, normals, texcoords
            f.write("\n".join(map(lambda vert: "v %.7g %.7g %.7g" % tuple(vert), boundprim.vertex.tolist())))
            f.write("\n")

            if emit_normals:
                f.write("\n".join(map(lambda norm: "vn %.7g %.7g %.7g" % tuple(norm), boundprim.normal.tolist())))
                f.write("\n")

            if emit_texcoords:
                f.write("\n".join(map(lambda uv: "vt %.7g %.7g" % tuple(uv), boundprim.texcoordset[0].tolist())))
                f.write("\n")

            # Start using the right material
            if boundprim.material:
                f.write("usemtl %s\n" % boundprim.material.id)

            if emit_normals and emit_texcoords:
                format_string = "f %d/%d/%d %d/%d/%d %d/%d/%d"
                index_iter = zip(
                    boundprim.vertex_index + vert_offset,
                    boundprim.texcoord_indexset[0] + tc_offset,
                    boundprim.normal_index + norm_offset,
                )
            elif emit_normals:
                format_string = "f %d//%d %d//%d %d//%d"
                index_iter = zip(boundprim.vertex_index + vert_offset, boundprim.normal_index + norm_offset)
            elif emit_texcoords:
                format_string = "f %d/%d %d/%d %d/%d"
                index_iter = zip(boundprim.vertex_index + vert_offset, boundprim.texcoord_indexset[0] + tc_offset)
            else:
                format_string = "f %d %d %d"
                index_iter = zip(boundprim.vertex_index + vert_offset)

            # Write transformed primitives
            f.write("\n".join(map(lambda idx: format_string % tuple(chain.from_iterable(zip(*idx))), index_iter)))
            f.write("\n")

            # Finally, update offsets
            vert_offset += boundprim.vertex.shape[0]
            if emit_normals:
                norm_offset += boundprim.normal.shape[0]
            if emit_texcoords:
                tc_offset += boundprim.texcoordset[0].shape[0]

    f.write("\n")
