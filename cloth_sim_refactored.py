# Code refactored by ChatGPT.
# My original code worked well, yes, but was quite messy as I wrote it years ago so I had ChatGPT clean it up

from kivy.core.window import Window
from kivy.factory import Factory as F
from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder

from pymunk import *
from pymunk.constraints import *

"""
2D Cloth/Net Simulation
-----------------------
This script simulates a cloth/net in 2D using Pymunk for physics and Kivy for rendering.
The net is held by two static anchors that you can move around with the mouse.
"""

# --- Physics setup ---
space = Space()
space.gravity = 0, -700

# --- Simulation parameters ---
line_thickness = 4.0      # Cloth line thickness
xcount, ycount = 30, 30   # Cloth grid resolution
width, height = 200, 100  # Cloth dimensions
x, y = Window.center[0] - width / 2, Window.center[1] - height / 2 - 30

is_stretchy = True        # Stretchy cloth (True) vs rigid net (False)
stiffness = 5000.0        # Spring stiffness
damping = 300             # Spring damping

# Window.clearcolor = 1, .2, .3, 1.
Window.clearcolor = .1, .1, .1, 1.
Window.maximize()


# --- Cloth generation ---
def gen_points():
    """Generate initial points arranged in a rectangular grid."""
    points = []
    dx, dy = width / xcount, height / ycount
    for i in range(xcount + 1):
        for j in range(ycount + 1):
            xp, yp = x + dx * i, y + dy * j
            points.append([xp, yp])
    return points


def add_segs_body(points, mass=2):
    """Add physics bodies at each point and connect them with segments."""
    bodies = []
    for i, p in enumerate(points[:-1]):
        b = Body(mass, 100)
        b.position = p
        c = Circle(b, 1)
        c.friction = 1.
        c.elasticity = .1
        space.add(b, c)
        bodies.append(b)

        # Add neighbouring segments for visualization
        if i != 0:
            r = i % ycount
            if ycount * (r + 1) + r == i:
                p1 = points[i + ycount + 1]
                space.add(Segment(b, p, p1, 1))
        elif i in range((ycount + 1) * (xcount), len(points)):
            p1 = points[i + 1]
            space.add(Segment(b, p, p1, 1))
        else:
            p1, p2 = points[i + ycount + 1], points[i + 1]
            space.add(Segment(b, p, p1, 1))
            space.add(Segment(b, p, p2, 1))

    # Last body
    b_last = Body(mass, 100)
    b_last.position = points[-1]
    space.add(b_last)
    bodies.append(b_last)
    return bodies


def add_joints(bodies):
    """Add joints between neighbouring bodies to form the cloth."""
    for i, b in enumerate(bodies[:-1]):
        r = i % ycount
        if i != 0 and ycount * (r + 1) + r == i:
            b1 = bodies[i + ycount + 1]
            connect(b, b1)
        elif i in range((ycount + 1) * xcount, len(points) - 1):
            b1 = bodies[i + 1]
            connect(b, b1)
        else:
            b1, b2 = bodies[i + ycount + 1], bodies[i + 1]
            connect(b, b1)
            connect(b, b2)


def connect(b1, b2):
    """Helper: connect two bodies with either PinJoint or DampedSpring."""
    if not is_stretchy:
        space.add(PinJoint(b1, b2))
    else:
        rl = (b1.position - b2.position).length * .92
        space.add(DampedSpring(b1, b2, (0, 0), (0, 0), rl, stiffness, damping))


def get_line_points(p):
    """Return zigzag path points for cloth rendering (both axes)."""
    pointsy, pointsx = [], []
    current, c, d = 0, 0, 1

    # Vertical zigzag
    for _ in range(len(p)):
        pointsy.extend(p[current])
        if c == ycount:
            current += ycount + 1
            c = 0
            d *= -1
            continue
        c += 1
        current += d

    curr, c, d = 0, 0, xcount + 1
    # Horizontal zigzag
    for _ in range(len(p)):
        pointsx.extend(p[curr])
        if c == xcount:
            curr += 1
            c = 0
            d *= -1
            continue
        c += 1
        curr += d

    return pointsx, pointsy


# --- Setup cloth ---
points = gen_points()
bodies = add_segs_body(points)
add_joints(bodies)

lp = get_line_points(points)

# Static anchors
sb1 = Body(body_type=Body.STATIC)
sb1.position = x - 50, y + height + 50

sb2 = Body(body_type=Body.STATIC)
sb2.position = x + width + 50, y + height + 50

# Attach cloth ends to anchors
space.add(PinJoint(bodies[ycount], sb1))
space.add(PinJoint(bodies[-1], sb2))

# Static ground + obstacle
seg = Segment(space.static_body, (x + 20, y - 5), (x + width - 20, y - 5), 5)
seg.friction, seg.elasticity = 1, .1

circle = Circle(space.static_body, 70)
circle.friction = 1
space.add(circle, seg)


# --- Canvas drawing ---
with Window.canvas:
    anch_l1 = F.Line(points=[*bodies[ycount].position, *sb1.position], width=2)
    anch_l2 = F.Line(points=[*bodies[-1].position, *sb2.position], width=2)
    F.Color(.9, .8, .1)
    line = F.Line(points=lp[0], width=line_thickness)
    line2 = F.Line(points=lp[1], width=line_thickness)
    F.Color(.5, .5, .5)
    F.Line(width=seg.radius, points=[*seg.a, *seg.b])
    F.Color(.5, .5, .1)
    moveable = F.Point(pointsize=4, points=[])
    moveable2 = F.Point(pointsize=4, points=[])
    title = F.Label(text="2d Net/Cloth Simulation With Python", font_size=29)
    title.center = Window.center[0], Window.height - 20

# Labels to display anchor positions
lbl1 = F.Label(text="Anchor 1: ", size_hint=[None, None])
lbl2 = F.Label(text="Anchor 2: ", size_hint=[None, None])
lbl1.pos, lbl2.pos = (0, Window.height - 100), (0, Window.height - 140)
Window.add_widget(lbl1)
Window.add_widget(lbl2)


# --- Update functions ---
def update(dt):
    """Update cloth rendering and physics simulation."""
    points = [b.position for b in bodies]
    lp = get_line_points(points)
    line.points, line2.points = lp[0], lp[1]
    anch_l1.points = [*bodies[ycount].position, *sb1.position]
    anch_l2.points = [*bodies[-1].position, *sb2.position]

    lbl1.text = f"Anchor 1: {list(sb1.position)}"
    lbl2.text = f"Anchor 2: {list(sb2.position)}"
    lbl1.size, lbl2.size = lbl1.texture_size, lbl2.texture_size

    # Step the physics simulation multiple times for stability
    [space.step(.009) for _ in range(4)]


def move_anchor(touch):
    """Drag the closest anchor to the mouse position."""
    mov_anch = min((sb1, sb2), key=lambda sb: (sb.position - Vec2d(*touch.pos)).length)
    mov_anch.position = touch.pos
    (moveable if mov_anch == sb1 else moveable2).points = touch.pos


# Bind events
Window.on_touch_move = move_anchor
Clock.schedule_interval(update, 1 / 50)


class SimApp(App):
    """Main Kivy application class."""
    pass


SimApp().run()

