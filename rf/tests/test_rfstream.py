"""
Tests for rfstream module.
"""
import unittest

from obspy import read, read_events
from obspy.core import AttribDict
from obspy.core.util import NamedTemporaryFile
from rf import read_rf, RFStream, rfstats
from rf.rfstream import (obj2stats, _HEADERS, _FORMATHEADERS, _STATION_GETTER,
                         _EVENT_GETTER)


_HEADERS_TEST_IO = (50.3, -100.2, 400.3,
                    -20.32, 10., 12.4, 6.5, -40.432,
                    20.643, 57.6, 90.1, 10.2, 10.,
                    10., -20, 150,
                    'Ps', 15.7, 2.5)

_HEADERS_NOT_DETERMINED_BY_RFSTATS = ('moveout', 'box_pos', 'box_length')


def write_test_header(stream):
    for tr in stream:
        st = tr.stats
        for head, val in zip(_HEADERS, _HEADERS_TEST_IO):
            if head in ('onset', 'event_time'):
                val = st.starttime + val
            st[head] = val


class RFStreamTestCase(unittest.TestCase):

    def setUp(self):
        self.event = read_events()[0]
        self.station = AttribDict({'latitude': 41.818 - 66.7,
                                   'longitude': 79.689,
                                   'elevation': 365.4})

    def test_read_rf(self):
        self.assertIsInstance(read_rf(), RFStream)

    def test_io_header(self):
        def test_io_format(format):
            stream1 = stream.copy()
            suffix = '.' + format.upper()
            if format == 'sh':
                format = 'q'
                suffix = '.QHD'
            with NamedTemporaryFile(suffix=suffix) as ft:
                fname = ft.name
                stream1.write(fname, format.upper())
                stream2 = read_rf(fname)
            st1 = stream1[0].stats
            st2 = stream2[0].stats
            for head in _HEADERS:
                self.assertAlmostEqual(st1[head], st2[head], 4, msg=head)
            self.assertEqual(stream1[0].id, stream2[0].id)
        stream = RFStream(read())[:1]
        for tr in stream:
            tr.stats.location = '11'
        write_test_header(stream)
        for format in _FORMATHEADERS:
            test_io_format(format)

    def test_io_header_no_eventtime(self):
        def test_io_format(format):
            stream1 = stream.copy()
            suffix = '.' + format.upper()
            if format == 'sh':
                format = 'q'
                suffix = '.QHD'
            with NamedTemporaryFile(suffix=suffix) as ft:
                fname = ft.name
                stream1.write(fname, format.upper())
                stream2 = read_rf(fname)
            st2 = stream2[0].stats
            self.assertNotIn('event_time', st2)
        stream = read()[:1]
        for format in _FORMATHEADERS:
            test_io_format(format)

    def test_obj2stats(self):
        stats = obj2stats(event=self.event, station=self.station)
        for head, _ in _STATION_GETTER + _EVENT_GETTER:
            self.assertIn(head, stats)

    def test_rfstats(self):
        stats = rfstats(station=self.station, event=self.event, pp_depth=100.)
        for head in _HEADERS:
            if head not in _HEADERS_NOT_DETERMINED_BY_RFSTATS:
                self.assertIn(head, stats)
        # event is exactly north from station and around 66.7 degrees away
        self.assertTrue(abs(stats.distance - 66.7) < 1.)
        self.assertTrue(abs(stats.back_azimuth % 360.) < 0.1)
        self.assertTrue(abs(stats.slowness - 6.4) < 0.1)

    def test_trim2(self):
        stream = read_rf()
        starttimes = [tr.stats.starttime for tr in stream]
        stream.trim2(50, 100, 'starttime')
        for t0, tr in zip(starttimes, stream):
            self.assertEqual(tr.stats.starttime - t0, 50)
            self.assertEqual(tr.stats.endtime - t0, 100)

    def test_slice2(self):
        stream = read_rf()
        event_times = [tr.stats.starttime for tr in stream]
        stream = stream.slice2(-50, 100, 'event_time')
        for t0, tr in zip(event_times, stream):
            self.assertEqual(tr.stats.starttime - t0, -50)
            self.assertEqual(tr.stats.endtime - t0, 100)

#    def test_simple(self):
#        stream = read_rf()
#        stream._write_test_header()
#        stream.rf()
#        stream.moveout()
#        stream.ppoint(50)
#        self.assertEqual(len(stream[0]), len(read_rf()[0]))

    def test_rf(self):
        pass


def suite():
    return unittest.makeSuite(RFStreamTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
