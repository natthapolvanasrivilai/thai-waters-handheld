"""Draw the two A3 rail footprints from a native, reopened plate 1 slice."""
from argparse import ArgumentParser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from rail_paths import DX, DY, RAILS, footprints, regions, window


def font(size):
    for name in ("arial.ttf","DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name,size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw(gcode, destination):
    layers=footprints(gcode)
    canvas=Image.new("RGB",(1280,595),"#ffffff")
    pen=ImageDraw.Draw(canvas)
    pen.text((35,22),"A3 rail deposition in the housing",font=font(37),fill="#183246")
    pen.text((37,75),"Bambu Studio plate 1  /  Receiver-down  /  Plan view at the indicated layer top",font=font(20),fill="#455969")
    for idx,(z,title,detail) in enumerate([(6.4,"Sparse core","Shell and internal infill"),
                 (6.6,"Next solid layer","Orange shows spans over infill gaps"),
                 (7.8,"Seating surface","Both channels open at the north end")]):
        x=35+idx*421
        pen.text((x,123),f"{title}   ·   {z:.1f} mm",font=font(23),fill="#183246")
        pen.rounded_rectangle((x,163,x+380,480),radius=8,fill="#eff4f4")
        def coords(points):
            return [(x+37+(px-DX-15)*21,192+(0-(py-DY))*21) for px,py in points]
        def paint(geom,color):
            for body in regions(geom):
                pen.polygon(coords(body.exterior.coords),fill=color)
                for ring in body.interiors:
                    pen.polygon(coords(ring.coords),fill="#eff4f4")
        for _,cx in RAILS:
            region=window(cx-1.5,-12,cx+1.5,0)
            solid=layers[z]["model"].intersection(region)
            paint(solid,"#256970")
            if idx==1:
                # Paint only the unbacked subset, so sparse gaps are visible.
                for gap in regions(solid.difference(layers[6.4]["model"])):
                    pen.polygon(coords(gap.exterior.coords),fill="#d18a36")
        pen.text((x,496),detail,font=font(19),fill="#183246")
    pen.text((37,554),"Swept native bead widths. Both rails use the same drawing scale. Nominal rail footprint 3 × 12 mm.",font=font(19),fill="#455969")
    canvas.save(destination)


if __name__=="__main__":
    cli=ArgumentParser(description=__doc__)
    cli.add_argument("gcode",type=Path)
    cli.add_argument("output",type=Path)
    args=cli.parse_args()
    draw(args.gcode,args.output)
