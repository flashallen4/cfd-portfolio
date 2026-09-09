#!/usr/bin/env python3
"""
Split the Ahmed body STL into two named solids for targeted meshing
treatment: 'main' (the bulk of the body) and 'corner' (the two rear
trihedral corners where the slant edge, side edge, and rear vertical
face converge).

Purpose: snappyHexMesh cannot apply different refinementSurfaces
levels or different nSurfaceLayers to different parts of a single
unnamed STL solid. A refinementRegions box only sets a MINIMUM level
and does not cap surface-driven refinement (confirmed empirically --
see mesh_development_log.md). To actually cap/disable layer addition
at the problematic rear corners specifically, those triangles must be
a separately named region in the STL.

Classification criterion (matches the spatial diagnosis in
mesh_development_log.md): a triangle is 'corner' if its centroid falls
within a small box around either rear trihedral corner. Everything
else is 'main'.
"""

import argparse
import numpy as np
import trimesh


def classify_and_split(input_stl: str, output_stl: str,
                        corner_x_min: float = 0.95,
                        corner_x_max: float = 1.06,
                        corner_y_inner: float = 0.14,
                        corner_y_outer: float = 0.21,
                        corner_z_min: float = 0.03,
                        corner_z_max: float = 0.35):
    """
    Load input_stl, classify triangles into 'main' or 'corner' based on
    centroid location, and write a multi-solid ASCII STL to output_stl.
    """
    mesh = trimesh.load(input_stl)
    centroids = mesh.triangles_center

    x, y, z = centroids[:, 0], centroids[:, 1], centroids[:, 2]

    in_x = (x >= corner_x_min) & (x <= corner_x_max)
    in_z = (z >= corner_z_min) & (z <= corner_z_max)
    in_y_pos = (y >= corner_y_inner) & (y <= corner_y_outer)
    in_y_neg = (y <= -corner_y_inner) & (y >= -corner_y_outer)

    corner_mask = in_x & in_z & (in_y_pos | in_y_neg)
    main_mask = ~corner_mask

    print(f"Total triangles: {len(mesh.faces)}")
    print(f"  Classified as 'corner': {corner_mask.sum()}")
    print(f"  Classified as 'main':   {main_mask.sum()}")

    if corner_mask.sum() == 0:
        raise ValueError(
            "No triangles classified as 'corner' -- classification "
            "box does not intersect the mesh. Check bounds against "
            "the actual STL bounding box before proceeding."
        )

    main_mesh = mesh.submesh([main_mask], append=True)
    corner_mesh = mesh.submesh([corner_mask], append=True)

    # Write as a multi-solid ASCII STL (manually, since trimesh's
    # STL exporter writes single-solid files by default).
    with open(output_stl, 'w') as f:
        for name, submesh in [('main', main_mesh), ('corner', corner_mesh)]:
            f.write(f"solid {name}\n")
            for tri in submesh.triangles:
                normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                norm_len = np.linalg.norm(normal)
                if norm_len > 1e-12:
                    normal = normal / norm_len
                else:
                    normal = np.array([0.0, 0.0, 0.0])
                f.write(f"  facet normal {normal[0]:.6e} {normal[1]:.6e} {normal[2]:.6e}\n")
                f.write("    outer loop\n")
                for vertex in tri:
                    f.write(f"      vertex {vertex[0]:.6e} {vertex[1]:.6e} {vertex[2]:.6e}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
            f.write(f"endsolid {name}\n")

    print(f"Wrote multi-solid STL to: {output_stl}")


def main():
    parser = argparse.ArgumentParser(description="Split Ahmed body STL into main/corner solids.")
    parser.add_argument("input_stl", help="Path to input STL (single solid)")
    parser.add_argument("output_stl", help="Path to output multi-solid STL")
    args = parser.parse_args()
    classify_and_split(args.input_stl, args.output_stl)


if __name__ == "__main__":
    main()
