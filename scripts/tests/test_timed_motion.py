"""Timed admission regressions. Synthetic frames are never benchmark evidence."""
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / 'spikes/982/renderer'
sys.path.insert(0, str(RENDERER))
spec = importlib.util.spec_from_file_location('timed_summary', RENDERER / 'summarize.py')
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


def complete_synthetic(tuple_name='wayland'):
    # Preserve historical pose/gesture coverage; synthesize performance and new
    # sample clocks in memory only. These are not recaptured browser receipts.
    raw = json.loads((ROOT / f'docs/acceptance/mechanisms/receipts/motion-proof-{tuple_name}-v7.json').read_text())
    raw['kind'] = 'measurement'
    raw['warmup_start_ms'] = raw['inputs'][0]['at']
    for phase, scale in (('warmup', 500), ('measurement', 1000)):
        rows = [row for row in raw['inputs'] if row['phase'] == phase]
        origin = raw['warmup_start_ms'] if phase == 'warmup' else raw['measurement_start_ms']
        for i, row in enumerate(rows):
            row['sampled_at'] = origin + row['seconds'] * scale if i < len(rows)-1 else row['at']

    start = raw['measurement_start_ms']
    finish = start + raw['duration_ms']
    raw['frames'] = [start - 1] + [start + n * 16 for n in range(int(raw['duration_ms'] // 16) + 1)]
    if raw['frames'][-1] < finish:
        raw['frames'].append(finish)
    return raw


def clock_synthetic(start=49374.0, delay=0.001):
    raw = dict(kind='measurement', warmup_start_ms=0, warmup_ms=30000,
               measurement_start_ms=start, measurement_end_ms=start+60000,
               duration_ms=60000+delay, invalid=[], errors=[], inputs=[], gestures=[])
    for phase, origin, scale in (('warmup', 0, 500), ('measurement', start, 1000)):
        previous, dragging = [0, 0, 1], False
        for seconds in (0, 5, 15, 25, 35, 45, 55, 60):
            from motion_evidence import pose as protocol_pose
            pose = protocol_pose(seconds)
            sampled = origin + seconds*scale
            at = (origin + delay) + seconds*scale
            if seconds == 60 and phase == 'warmup' and delay:
                at = math.nextafter(at, -math.inf)
            def event(kind, xy):
                raw['gestures'].append(dict(at=at, type=kind, x=xy[0], y=xy[1]))
            pan, zoom = pose[:2] != previous[:2], pose[2] != previous[2]
            if zoom and dragging:
                event('pointercancel', previous); dragging = False
            if pan:
                if not dragging:
                    event('pointerdown', previous); dragging = True
                event('pointermove', pose)
            elif dragging:
                event('pointercancel', previous); dragging = False
            raw['inputs'].append(dict(at=at, sampled_at=sampled, phase=phase, seconds=seconds, requested=pose))
            previous = pose
        if dragging: event('pointercancel', previous)
    finish = raw['inputs'][-1]['at']
    raw['duration_ms'] = finish-start
    raw['frames'] = [start-1] + [start+n*16 for n in range(3751)]
    if raw['frames'][-1] < finish:
        raw['frames'].append(finish)
    return raw


def stalled_synthetic():
    # Coordinator counterexample: 59s missed work, then enough fast frames to
    # make nearest-rank p95=16ms. Do not replace this with a max-stall assertion.
    return dict(kind='measurement', frames=[0, 59000] + list(range(59016, 60009, 16)),
                invalid=[], errors=[], duration_ms=60008, warmup_ms=30000,
                measurement_start_ms=0, measurement_end_ms=60000,
                inputs=[dict(at=0, phase='measurement', seconds=0, requested=[0, 0, 1]),
                        dict(at=59000, phase='measurement', seconds=59, requested=[0, 30, .975]),
                        dict(at=60008, phase='measurement', seconds=60, requested=[0, 0, 1])], gestures=[])


class TimedMotionTests(unittest.TestCase):
    def test_complete_trace_positive_both_tuples(self):
        for tuple_name in ('wayland', 'x11'):
            with self.subTest(tuple_name=tuple_name):
                result = summary.summarize(complete_synthetic(tuple_name), 'synthetic')
                self.assertTrue(result['pass_run'], result)

    def test_valid_fractional_clock_start(self):
        raw = complete_synthetic()
        delta = 49374.001 - raw['measurement_start_ms']
        for key in ('warmup_start_ms', 'measurement_start_ms', 'measurement_end_ms'):
            raw[key] += delta
        raw['measurement_end_ms'] = raw['measurement_start_ms'] + 60000
        raw['frames'] = [value + delta for value in raw['frames']]
        for row in raw['inputs'] + raw['gestures']:
            row['at'] += delta
            if 'sampled_at' in row:
                row['sampled_at'] += delta
        self.assertNotEqual(raw['measurement_end_ms'] - raw['measurement_start_ms'], 60000)
        result = summary.summarize(raw, 'synthetic-fractional-start')
        self.assertTrue(result['pass_run'], result)
        self.assertAlmostEqual(result['p95_ms'], 16, places=6)

    def test_fractional_first_input_span_boundary_both_phases(self):
        raw = clock_synthetic()
        self.assertEqual(raw['inputs'][-1]['at'], 109374.00099999999)
        measurement = [r for r in raw['inputs'] if r['phase']=='measurement']
        self.assertLess(measurement[-1]['at']-measurement[0]['at'], 60000)
        self.assertTrue(summary.summarize(raw, 'fractional-input-span')['pass_run'])
        # A real shortfall remains invalid, rather than broadening the duration.
        raw['inputs'][-1]['at'] -= .01
        self.assertFalse(summary.summarize(raw, 'short-span')['valid'])

    def test_fractional_span_untimed_checker(self):
        from motion_evidence import verified_trace
        raw = clock_synthetic()
        historical = json.loads((ROOT / 'docs/acceptance/mechanisms/receipts/motion-proof-wayland-v7.json').read_text())
        raw['checkpoints'] = historical['checkpoints']
        raw['frames'] = []
        verified_trace(raw)
        raw['inputs'][-1]['at'] -= .01
        with self.assertRaisesRegex(ValueError, 'span'):
            verified_trace(raw)

    def test_sample_clock_and_dispatch_causality(self):
        raw = clock_synthetic(delay=0)
        self.assertTrue(summary.summarize(raw, 'control')['pass_run'])
        # Complete logical poses, coherent gestures, ordered/spanning post clocks;
        # only the old unchecked relationship to the computation clock is false.
        for row in raw['inputs']:
            if row['phase']=='measurement' and 0 < row['seconds'] < 60:
                old = row['at']
                row['at'] = raw['measurement_start_ms']+59000+row['seconds']*10
                for event in raw['gestures']:
                    if event['at']==old: event['at']=row['at']
        result = summary.summarize(raw, 'inconsistent-clock')
        self.assertFalse(result['valid'])
        self.assertIn('causality', result['workload_error'])
        raw = clock_synthetic(delay=0)
        raw['inputs'][2]['sampled_at'] -= 1
        result = summary.summarize(raw, 'wrong-sample')
        self.assertFalse(result['valid'])
        self.assertIn('Logical seconds', result['workload_error'])
        raw = clock_synthetic(delay=0)
        # 4 seconds inside synchronous dispatch is legal: next sample is later.
        row = raw['inputs'][9]
        old = row['at']; row['at'] += 4000
        for event in raw['gestures']:
            if event['at']==old: event['at']=row['at']
        self.assertTrue(summary.summarize(raw, 'legitimate-dispatch-stall')['pass_run'])
        raw['inputs'][9]['sampled_at'] = float('nan')
        self.assertFalse(summary.summarize(raw, 'nonfinite-sample')['valid'])

    def test_coordinator_stall_rejected(self):
        result = summary.summarize(stalled_synthetic(), 'synthetic')
        self.assertEqual(result['p95_ms'], 16)
        self.assertEqual(result['max_ms'], 59000)
        self.assertFalse(result['valid'])
        self.assertFalse(result['pass_run'])

    def test_five_run_gate_and_stalled_five(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / f'run-{n}.json' for n in range(5)]
            for raw, expected in ((complete_synthetic(), True), (stalled_synthetic(), False)):
                for path in paths:
                    path.write_text(json.dumps(raw))
                result = subprocess.run([sys.executable, '-B', str(RENDERER / 'summarize.py'), *map(str, paths)], check=True, capture_output=True, text=True)
                self.assertEqual(json.loads(result.stdout)['gate_pass'], expected)
            paths[0].write_text(json.dumps(complete_synthetic()))
            result = subprocess.run([sys.executable, '-B', str(RENDERER / 'summarize.py'), str(paths[0])], check=True, capture_output=True, text=True)
            self.assertFalse(json.loads(result.stdout)['gate_pass'])

    def test_missing_segments_each_phase(self):
        for phase in ('warmup', 'measurement'):
            for segment in range(6):
                raw = complete_synthetic()
                raw['inputs'] = [row for row in raw['inputs'] if not (row['phase'] == phase and segment * 10 < row['seconds'] < (segment + 1) * 10)]
                with self.subTest(phase=phase, segment=segment):
                    self.assertFalse(summary.summarize(raw, 'synthetic')['valid'])

    def test_trace_and_gesture_mutations(self):
        def changed_pose(raw): raw['inputs'][3]['requested'][0] += 1
        def nonfinite_time(raw): raw['inputs'][3]['at'] = float('nan')
        def backwards_time(raw): raw['inputs'][3]['at'] = -1
        def missing_gestures(raw): raw['gestures'] = []
        def missing_cancel(raw): raw['gestures'].pop()
        def wrong_gesture(raw): raw['gestures'][2]['x'] += 1
        def wrong_phase(raw): raw['inputs'][0]['phase'] = 'measurement'
        def invalid_clock(raw): raw['duration_ms'] = float('inf')
        for mutate in (changed_pose, nonfinite_time, backwards_time, missing_gestures, missing_cancel, wrong_gesture, wrong_phase, invalid_clock):
            raw = complete_synthetic()
            mutate(raw)
            with self.subTest(mutation=mutate.__name__):
                self.assertFalse(summary.summarize(raw, 'synthetic')['valid'])

    def test_frame_nonfinite_rejected(self):
        raw = complete_synthetic()
        raw['frames'][2] = float('nan')
        with self.assertRaises(ValueError):
            summary.summarize(raw, 'synthetic')

    def test_fixed_p95_bar_without_max_stall_bar(self):
        raw = complete_synthetic()
        start = raw['measurement_start_ms']
        finish = start + raw['duration_ms']
        raw['frames'] = [start - 1, start] + [start + n for n in range(59000, int(raw['duration_ms']), 16)] + [finish]
        result = summary.summarize(raw, 'synthetic-complete-workload-with-frame-stall')
        self.assertTrue(result['pass_run'], result)
        self.assertEqual(result['max_ms'], 59000)
        raw['frames'] = [start - 1] + [start + n for n in range(0, int(raw['duration_ms']), 40)] + [finish]
        result = summary.summarize(raw, 'synthetic-slow')
        self.assertTrue(result['valid'], result)
        self.assertEqual(result['p95_ms'], 40)
        self.assertFalse(result['pass_run'])


if __name__ == '__main__':
    unittest.main()
