from unittest import TestCase

from pdf_annotate.graphics import BeginText
from pdf_annotate.graphics import Bezier
from pdf_annotate.graphics import Close
from pdf_annotate.graphics import ContentStream
from pdf_annotate.graphics import CTM
from pdf_annotate.graphics import EndText
from pdf_annotate.graphics import Fill
from pdf_annotate.graphics import FillColor
from pdf_annotate.graphics import Font
from pdf_annotate.graphics import format_number
from pdf_annotate.graphics import Line
from pdf_annotate.graphics import Move
from pdf_annotate.graphics import Rect
from pdf_annotate.graphics import Restore
from pdf_annotate.graphics import Save
from pdf_annotate.graphics import Stroke
from pdf_annotate.graphics import StrokeAndFill
from pdf_annotate.graphics import StrokeColor
from pdf_annotate.graphics import StrokeWidth
from pdf_annotate.graphics import Text
from pdf_annotate.graphics import TextMatrix


class TestCommandEquality(TestCase):
    def test_static_commands(self):
        assert Stroke() == Stroke()
        assert Stroke() != Save()

    def test_tuple_commands(self):
        assert StrokeColor(1, 2, 3) == StrokeColor(1, 2, 3)
        assert Text('Hello') == Text('Hello')
        assert StrokeColor(1, 2, 3) != FillColor(1, 2, 3)


class TestContentStream(TestCase):
    # a list of (ContentStream, stream_string) pairs for testing parse/resolve
    FIXTURES = [
        (
            ContentStream([
                CTM([1, 0, 0, 1, 0, 0]),
                Font('Helvetica', 12),
                TextMatrix([1, 0, 0, 1, 20, 50]),
                BeginText(),
                Text('Sure, why not?'),
                EndText(),
            ]),
            (
                '1 0 0 1 0 0 cm /Helvetica 12 Tf '
                '1 0 0 1 20 50 Tm BT '
                '(Sure, why not?) Tj ET'
            )
        ),
        (
            ContentStream([
                Save(),
                StrokeWidth(2),
                StrokeColor(0, 0, 0),
                FillColor(1, 0, 0),
                Move(10, 10),
                Line(20, 20),
                Bezier(30, 30, 40, 40, 50, 50),
                Rect(50, 50, 10, 10),
                Close(),
                StrokeAndFill(),
                Stroke(),
                Fill(),
                Restore(),
            ]),
            (
                'q 2 w 0 0 0 RG 1 0 0 rg 10 10 m 20 20 l '
                '30 30 40 40 50 50 c 50 50 10 10 re '
                'h B S f Q'
            )
        ),
    ]

    def test_equality(self):
        assert ContentStream() == ContentStream()

        cs1 = ContentStream([Save(), FillColor(1, 0, 0)])
        cs2 = ContentStream([Save(), FillColor(1, 0, 0)])
        assert cs1 == cs2

    def test_content_stream_not_equal_to_string(self):
        assert ContentStream() != ''
        assert ContentStream([Save()]) != 'q'

    def test_parse_resolve(self):
        for cs, stream_string in self.FIXTURES:
            assert cs.resolve() == stream_string
            assert cs == ContentStream.parse(stream_string)

    def test_content_stream(self):
        # Basically a smoke test for all the simple functions of ContentStream
        cs = ContentStream([Save(), StrokeWidth(2)])
        cs.add(StrokeColor(0, 0, 0))
        cs.add(FillColor(1, 0, 0))
        cs.extend([
            Move(10, 10),
            Line(20, 20),
            Bezier(30, 30, 40, 40, 50, 50),
            Rect(50, 50, 10, 10),
        ])
        cs = ContentStream.join(
            cs,
            ContentStream([
                Close(),
                StrokeAndFill(),
                Stroke(),
                Fill(),
                Restore(),
            ])
        )
        assert cs.resolve() == (
            'q 2 w 0 0 0 RG 1 0 0 rg 10 10 m 20 20 l '
            '30 30 40 40 50 50 c 50 50 10 10 re '
            'h B S f Q'
        )

    def test_text_content_stream(self):
        cs = ContentStream([
            CTM([1, 0, 0, 1, 0, 0]),
            Font('Helvetica', 12),
            TextMatrix([1, 0, 0, 1, 20, 50]),
            BeginText(),
            Text('Sure, why not?'),
            EndText(),
        ])
        assert cs.resolve() == (
            '1 0 0 1 0 0 cm /Helvetica 12 Tf '
            '1 0 0 1 20 50 Tm BT '
            '(Sure, why not?) Tj ET'
        )

    def test_transform_move(self):
        transformed = Move(1, 1).transform([2, 0, 0, 2, 5, 10]).resolve()
        assert transformed == '7 12 m'

    def test_transform_line(self):
        transformed = Line(1, 1).transform([2, 0, 0, 2, 5, 10]).resolve()
        assert transformed == '7 12 l'

    def test_transform_rect(self):
        transformed = Rect(1, 1, 2, 2).transform([2, 0, 0, 2, 5, 10]).resolve()
        assert transformed == '7 12 4 4 re'

    def test_transform_bezier(self):
        transformed = Bezier(1, 1, 2, 2, 3, 3).transform(
            [2, 0, 0, 2, 5, 10],
        ).resolve()
        assert transformed == '7 12 9 14 11 16 c'

    def test_transform_content_stream(self):
        cs = ContentStream([
            Save(),
            Move(1, 1),
            Restore(),
        ])
        transformed = cs.transform([2, 0, 0, 2, 5, 10]).resolve()
        assert transformed == 'q 7 12 m Q'


class TestFormatting(TestCase):

    def test_format_number(self):
        assert format_number(0.000000000000000001) == '0'
        assert format_number(-0.000000000000000002) == '0'
        assert format_number(2) == '2'
        assert format_number(-14) == '-14'
        assert format_number(-14.5) == '-14.5'
        assert format_number(15.0) == '15'
        assert format_number(1.54) == '1.54'
        assert format_number(0.5) == '0.5'
        assert format_number(3.14159265358979323) == '3.1415926536'

    def test_commands_get_number_formatting(self):
        # Regression test to make sure that all commands that output number
        # have sane formatting.
        stream = ContentStream([
            StrokeWidth(0.0),
            StrokeColor(0.0, 0.0, 0.0),
            FillColor(0.0, 0.0, 0.0),
            Rect(0.0, 0.0, 0.0, 0.0),
            Move(0.0, 0.0),
            Line(0.0, 0.0),
            Bezier(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
            CTM([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
            TextMatrix([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        ]).resolve()
        assert stream == (
            '0 w '
            '0 0 0 RG '
            '0 0 0 rg '
            '0 0 0 0 re '
            '0 0 m '
            '0 0 l '
            '0 0 0 0 0 0 c '
            '0 0 0 0 0 0 cm '
            '0 0 0 0 0 0 Tm'
        )
