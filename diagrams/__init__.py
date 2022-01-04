# Design goals:
# - Add an abstraction layer over PyCairo
# - Replace the imperative API with a more declarative design (maybe similar to the `diagrams` library from Haskell)
#
# TODO
# - [ ] Update width and height of image to fit all the contents
# - [ ] Allow change of backend for the `render` function

import math

from dataclasses import dataclass
from typing import List, Tuple

import cairo


Matrix = cairo.Matrix


class Transform:
    def __call__(self) -> Matrix:
        raise NotImplemented


class Identity(Transform):
    def __call__(self):
        return cairo.Matrix()


class ReflectX(Transform):
    def __call__(self):
        matrix = cairo.Matrix()
        matrix = matrix.scale(-1, 1)
        return matrix


class ReflectY(Transform):
    def __call__(self):
        matrix = cairo.Matrix()
        matrix = matrix.scale(1, -1)
        return matrix


class Rotate(Transform):
    def __init__(self, θ: float):
        self.θ = θ

    def __call__(self):
        return cairo.Matrix.init_rotate(self.θ)


class Translate(Transform):
    def __init__(self, dx: float, dy: float):
        self.dx = dx
        self.dy = dy

    def __call__(self):
        matrix = cairo.Matrix()
        matrix.translate(self.dx, self.dy)
        return matrix


class Compose(Transform):
    def __init__(self, t, u):
        self.t = t
        self.u = u

    def __call__(self):
        # return self.t().multiply(self.u())
        return self.u().multiply(self.t())


class Color:
    def to_float(self):
        raise NotImplemented


@dataclass
class RGB(Color):
    r: int
    g: int
    b: int

    def to_float(self) -> Tuple[float, float, float]:
        return self.r / 255, self.g / 255, self.b / 255


class Primitive:
    def __init__(self):
        self.transform = Identity()
        # style
        self.fill_color = None
        self.stroke_color = (0.0, 0.0, 0.0)
        self.stroke_width = 0.01

    def rotate(self, θ) -> "Primitive":
        self.transform = Compose(Rotate(θ), self.transform)
        return self

    def translate(self, dx: float, dy: float) -> "Primitive":
        self.transform = Compose(Translate(dx, dy), self.transform)
        return self

    def set_fill_color(self, color: Color) -> "Primitive":
        self.fill_color = color.to_float()
        return self

    def set_stroke_color(self, color: Color) -> "Primitive":
        self.stroke_color = color.to_float()
        return self

    def set_stroke_width(self, width: float) -> "Primitive":
        self.stroke_width = width
        return self

    def render_shape(self, ctx):
        raise NotImplemented

    def render(self, ctx):
        matrix = self.transform()

        ctx.save()
        ctx.transform(matrix)

        self.render_shape(ctx)

        # style
        if self.fill_color:
            ctx.set_source_rgb(*self.fill_color)
            ctx.fill_preserve()

        ctx.set_source_rgb(*self.stroke_color)
        ctx.set_line_width(self.stroke_width)
        ctx.stroke()

        ctx.restore()

    def overlay(self, other: "Primitive") -> "Diagram":
        return Diagram([self, other])


class Circle(Primitive):
    def __init__(self, radius: float):
        super().__init__()
        self.radius = radius
        self.center = complex(0.0, 0.0)

    def render_shape(self, ctx):
        ctx.arc(self.center.real, self.center.imag, self.radius, 0, 2 * math.pi)


class Rectangle(Primitive):
    def __init__(self, height: float, width: float):
        super().__init__()
        self.width = width
        self.height = height
        self.center = complex(0, 0)

    def render_shape(self, ctx):
        left = self.center.real - self.width / 2
        top = self.center.imag - self.height / 2
        ctx.rectangle(left, top, self.width, self.height)


class Diagram:
    def __init__(self, shapes: List[Primitive]):
        self.shapes = shapes

    @classmethod
    def empty(cls):
        return cls([])

    @classmethod
    def concat(cls, iterable):
        return sum(iterable, cls.empty())

    def add_primitive(self, shape: Primitive) -> "Diagram":
        self.shapes = self.shapes + [shape]
        return self

    def __add__(self, other: "Diagram") -> "Diagram":
        return Diagram(self.shapes + other.shapes)

    def translate(self, dx, dy):
        return self.fmap(lambda shape: shape.translate(dx, dy))

    def fmap(self, f) -> "Diagram":
        return Diagram([f(shape) for shape in self.shapes])

    def render(self, path):
        WIDTH, HEIGHT = 512, 512
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)

        ctx = cairo.Context(surface)
        ctx.scale(WIDTH, HEIGHT)

        for shape in self.shapes:
            shape.render(ctx)

        surface.write_to_png(path)
