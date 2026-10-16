"""Timed admission regressions. Synthetic frames are never benchmark evidence."""
import importlib.util
import json
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
    # Keep real full driver traces as a positive control, replacing only the
    # receipt kind and frame timings with explicitly synthetic performance data.
    raw = json.loads((ROOT / f'docs/acceptance/mechanisms/receipts/motion-proof-{tuple_name}-v7.json').read_text())
    raw['kind'] = 'measurement'
    start = raw['measurement_start_ms']
    finish = start + raw['duration_ms']
    raw['frames'] = [start - 1] + [start + n * 16 for n in range(int(raw['duration_ms'] // 16) + 1)]
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
