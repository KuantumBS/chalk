from dataclasses import dataclass
from typing import Any

from colour import Color
from svgwrite import Drawing
from svgwrite.base import BaseElement

from chalk.backend.cairo import render_cairo_prims
from chalk.path import Path
from chalk.shape import Shape
from chalk.style import Style
from chalk.transform import P2, BoundingBox, origin
from chalk.types import Diagram, PyCairoContext, PyLatex, PyLatexElement
from chalk.visitor import A, ShapeVisitor

black = Color("black")


def tri() -> Diagram:
    return (
        Path.from_list_of_tuples([(1.0, 0), (0.0, -1.0), (-1.0, 0), (1.0, 0)])
        .stroke()
        .rotate_by(-0.25)
        .fill_color(Color("black"))
        .align_r()
        .line_width(0)
    )


def dart(cut: float = 0.2) -> Diagram:
    return (
        Path.from_list_of_tuples(
            [
                (0, -cut),
                (1.0, cut),
                (0.0, -1.0 - cut),
                (-1.0, +cut),
                (0, -cut),
            ]
        )
        .stroke()
        .rotate_by(-0.25)
        .fill_color(Color("black"))
        .align_r()
        .line_width(0)
    )


@dataclass
class ArrowHead(Shape):
    """Arrow Head."""

    arrow_shape: Diagram

    def get_bounding_box(self) -> BoundingBox:
        # Arrow head don't have a bounding box since we can't accurately know
        # the size until rendering
        eps = 1e-4
        self.bb = BoundingBox([origin, origin + P2(eps, eps)])
        return self.bb

    def accept(self, visitor: ShapeVisitor[A], **kwargs: Any) -> A:
        return visitor.visit_arrowhead(self, **kwargs)
