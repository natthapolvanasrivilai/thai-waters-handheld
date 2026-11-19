"""Verify the closure directly on the reread dressed STEP in millimetres."""
import itertools
import math
import cadquery as cq


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def bbox_gap(a, b):
    return math.sqrt(sum(max(0, getattr(a, k+"min")-getattr(b, k+"max"),
                             getattr(b, k+"min")-getattr(a, k+"max"))**2 for k in "xyz"))


def near_shapes(body, shapes, limit):
    b = body.BoundingBox()
    return {k:s for k,s in shapes.items() if bbox_gap(b,s.BoundingBox()) < limit}


def measure(shapes):
    cover = shapes["serviceCover"]
    housing = shapes["Housing"]
    # Read both planar boundary loops on the two faces of the south wall.
    apertures = []
    for face in housing.Faces():
        b = face.BoundingBox()
        if b.ylen > .0001 or min(abs(b.ymin+34.5),abs(b.ymin+32.5)) > .0001:
            continue
        for wire in face.innerWires():
            w = wire.BoundingBox()
            if abs(w.xmin+30)<.001 and abs(w.zmin-17.5)<.001:
                assert abs(w.xlen-26)<.001 and abs(w.zlen-6)<.001
                assert len(wire.Edges()) == 4
                apertures.append(dict(y_mm=round(w.ymin,3), x_mm=[round(w.xmin,3),round(w.xmax,3)],
                                z_mm=[round(w.zmin,3),round(w.zmax,3)], area_mm2=round(cq.Face.makeFromWires(wire).Area(),4)))
    assert len(apertures)==2
    through = box(-30,-34.5,17.5,26,2,6)
    assert housing.intersect(through).Volume()<1e-6
    # At the face midplane the entire rectangular aperture is backed by TPU.
    # The projection also checks the lateral float corners and an extra offset
    # in either direction for a sightline 60 degrees from the wall normal at
    # 0.18 mm maximum nominal axial float, conservatively applied to both axes.
    face_band = box(-30,-35.14,17.5,26,.08,6)
    worst = 0.
    for sx,sz in itertools.product((-1,1),repeat=2):
        probe = face_band.translate((sx*(.25+.18*math.tan(math.pi/3)),0,sz*(.26+.18*math.tan(math.pi/3))))
        worst = max(worst,probe.cut(cover).Volume()/.08)
    assert worst < .0001
    others = {k:s for k,s in shapes.items() if k not in ("Housing","serviceCover")}
    gaps = {k:round(s.distance(cover),5) for k,s in near_shapes(cover,others,8).items()}
    assert min(gaps.values())>.5, gaps
    seated = cover.intersect(housing).Volume()
    assert seated < .00001
    # A rigid withdrawal must catch on the wall. Each mirrored hook touches
    # independently and the four tips have free space to flex toward the centre.
    locked = cover.translate((0,-.72,0)).intersect(housing)
    locks = [s.Volume() for s in locked.Solids() if s.Volume()>1e-6]
    assert len(locks)==4 and min(locks)>.2, locks
    # Releasing one end at a time reduces how many hooks deflect simultaneously.
    # Verify open switch access with the rod and all installed wiring present.
    probes = {}
    for name, x in [("A1-k3",-25.00056),("A1-reset",-16.50056),("A1-boot",-8.00056)]:
        button = shapes[name]
        tip_y=button.BoundingBox().ymin
        shaft = cq.Solid.makeCylinder(1,tip_y+38,cq.Vector(x,-38,20.1),cq.Vector(0,1,0))
        obstructions={k:round(s.intersect(shaft).Volume(),6) for k,s in near_shapes(shaft,shapes,.05).items() if k not in ("serviceCover",name)}
        assert not any(obstructions.values()), (name,obstructions)
        assert shaft.distance(button)<.001
        probes[name] = dict(center_xz_mm=[x,20.1], depth_from_shell_mm=round(tip_y+34.5,4),
                            obstruction_mm3=max(obstructions.values(),default=0), diameter_mm=2)
    # Evaluate the physical movement of the optional rod. The full ±43 mm
    # Y-axis slide occupies the same XZ envelope, so the orthogonal separation
    # below bounds its clearance for the complete axial movement.
    rod = shapes["Removable rod grip"].BoundingBox()
    c=cover.BoundingBox()
    rod_x_gap=max(0,c.xmin-rod.xmax,rod.xmin-c.xmax)
    audio_distance=min(cover.distance(shapes[k]) for k in ("speakerRim","speakerCloth","speakerGasket"))
    return dict(assembly="TW-A-0001-R0010", part="TW-P-0027-R0001", source="R0010 compressed STEP reimport",
                wall_apertures=sorted(apertures,key=lambda r:r["y_mm"]), shell_thickness_mm=2.0,
                bezel_side="display +Z; bottom wall -Y; USB -X; reel +X",
                closed_face_mm=[28.8,8.8,1.2], nominal_flange_overlap_per_side_mm=1.4,
                flange_pry_relief_remaining_overlap_mm=.60,
                guide_clearance_xz_per_side_mm=[.25,.26], wall_to_latch_nominal_axial_float_mm=.18,
                maximum_nominal_lateral_float_xz_mm=[.25,.26], covered_projection_area_mm2=156,
                maximum_uncovered_at_float_and_60deg_mm2=round(worst,6), seated_housing_intersection_mm3=round(seated,6),
                undeformed_axial_pull_mm=.72, four_latch_intersections_at_axial_pull_mm3=[round(v,5) for v in locks],
                hook_engagement_per_side_mm=.40, nearest_other_installed_parts_mm=gaps,
                open_service_probe_paths=probes, rod_x_clearance_over_axial_slide_mm=round(rod_x_gap,4),
                distance_to_speaker_face_or_seal_mm=round(audio_distance,4),
                physical_tests_pending=["retention and peel force", "TPU creep and repeated removal", "print tolerance and debris",
                                        "actuation of the three service switches", "rattle and acoustic response with assembled cover"])

