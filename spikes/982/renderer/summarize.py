#!/usr/bin/env python3
"""Nearest-rank summaries; admit the workload before applying the fixed p95 bar."""
import json
import math
import sys
from pathlib import Path
from motion_evidence import finite, requested_pose


def verified_timed_trace(raw):
    """Validate timed workload coverage, without introducing a max-stall bar."""
    if raw.get('kind') != 'measurement':
        raise ValueError('Timed measurement receipt required')
    for key in ('warmup_start_ms', 'warmup_ms', 'duration_ms', 'measurement_start_ms', 'measurement_end_ms'):
        if not finite(raw.get(key)):
            raise ValueError('Finite timing clocks required')
    start, end = raw['measurement_start_ms'], raw['measurement_end_ms']
    if raw['warmup_ms'] < 30000 or raw['duration_ms'] < 60000 or abs(end - start - 60000) > 1e-6:
        raise ValueError('Full 30-second warmup and 60-second measurement required')
    inputs = raw.get('inputs')
    gestures = raw.get('gestures')
    if not isinstance(inputs, list) or not inputs or not isinstance(gestures, list):
        raise ValueError('Complete timed inputs and gestures required')
    prior_at = -math.inf
    for row in inputs:
        if not isinstance(row, dict) or row.get('phase') not in ('warmup', 'measurement'):
            raise ValueError('Invalid input phase')
        requested_pose(row)
        if not finite(row.get('at')) or row['at'] < prior_at or row['seconds'] < 0:
            raise ValueError('Finite ordered input clocks required')
        sampled = row.get('sampled_at')
        if not finite(sampled) or sampled + 1e-6 < prior_at or sampled > row['at'] + 1e-6:
            raise ValueError('Input sampling/dispatch causality violated')
        prior_at = row['at']
    phases = [row['phase'] for row in inputs]
    if phases != sorted(phases, key=lambda phase: phase == 'measurement'):
        raise ValueError('Warmup must precede measurement')
    for phase, duration in (('warmup', 30000), ('measurement', 60000)):
        rows = [row for row in inputs if row['phase'] == phase]
        if not rows or rows[0]['seconds'] != 0 or rows[-1]['seconds'] != 60:
            raise ValueError('Both complete six-segment sequences required')
        if any(min(60, b['seconds']) < min(60, a['seconds']) for a, b in zip(rows, rows[1:])):
            raise ValueError('Ordered protocol poses required')
        if any(not any(n * 10 < row['seconds'] < (n + 1) * 10 for row in rows) for n in range(6)):
            raise ValueError('Missing exercised timed input segment')
        if rows[-1]['at'] - rows[0]['at'] + 1e-6 < duration:
            raise ValueError('Input trace does not span its required clock')
        origin = raw['warmup_start_ms'] if phase == 'warmup' else start
        scale = duration / 60
        for index, row in enumerate(rows):
            sampled = row.get('sampled_at')
            if index == 0:
                consistent = abs(sampled - origin) <= 1e-6
            elif index == len(rows) - 1:
                # The final explicit pose is clamped after the stop predicate.
                consistent = sampled + 1e-6 >= origin + duration
            else:
                consistent = abs(sampled - origin - row['seconds'] * scale) <= 1e-6
            if not consistent:
                raise ValueError('Logical seconds disagree with phase sample clock')
        if phase == 'measurement' and (rows[0]['at'] + 1e-6 < start or rows[-1]['at'] + 1e-6 < end):
            raise ValueError('Measurement input clocks disagree with timing window')

    # Replay the driver's pan/cancel state machine. Each gesture must belong to
    # its input interval and coordinates, rather than merely contributing a count.
    cursor = 0
    dragging = False
    previous = [0, 0, 1]
    lower = -math.inf
    phase = 'warmup'

    def event(kind, coordinates, upper):
        nonlocal cursor, lower
        if cursor >= len(gestures):
            raise ValueError('Missing timed gesture')
        item = gestures[cursor]
        if not isinstance(item, dict) or item.get('type') != kind:
            raise ValueError('Gesture continuity violated')
        if any(not finite(item.get(key)) for key in ('at', 'x', 'y')):
            raise ValueError('Finite gesture coordinates and clocks required')
        if not lower <= item['at'] <= upper or any(abs(item[key] - value) > 1e-8 for key, value in zip(('x', 'y'), coordinates)):
            raise ValueError('Gesture differs from its timed input')
        lower = item['at']
        cursor += 1

    for row in inputs:
        upper = row['at']
        if row['phase'] != phase:
            if dragging:
                event('pointercancel', previous[:2], upper)
            previous, dragging, phase = [0, 0, 1], False, row['phase']
        current = row['requested']
        pan = current[:2] != previous[:2]
        zoom = current[2] != previous[2]
        if zoom and dragging:
            event('pointercancel', previous[:2], upper)
            dragging = False
        if pan:
            if not dragging:
                event('pointerdown', previous[:2], upper)
                dragging = True
            event('pointermove', current[:2], upper)
        elif dragging:
            event('pointercancel', previous[:2], upper)
            dragging = False
        previous, lower = current, upper
    if dragging:
        event('pointercancel', previous[:2], math.inf)
    if cursor != len(gestures):
        raise ValueError('Unexpected timed gestures')


def summarize(raw, name):
    frames = raw.get('frames', [])
    if not isinstance(frames, list) or len(frames) < 2 or any(not finite(x) for x in frames):
        raise ValueError('Missing/nonfinite frame capture')
    intervals = [b - a for a, b in zip(frames, frames[1:])]
    if any(x <= 0 or not math.isfinite(x) for x in intervals):
        raise ValueError('Nonmonotonic frame capture')
    ordered = sorted(intervals)
    rank = lambda q: ordered[max(0, math.ceil(q * len(ordered)) - 1)]
    workload_error = None
    try:
        verified_timed_trace(raw)
        if abs(frames[-1] - raw['measurement_start_ms'] - raw['duration_ms']) > 1e-6:
            raise ValueError('Frame capture disagrees with measurement duration')
        if frames[0] > raw['measurement_start_ms'] or frames[1] < raw['measurement_start_ms']:
            raise ValueError('Frames must bracket measurement start')
    except ValueError as error:
        workload_error = str(error)
    valid = workload_error is None and raw.get('invalid') == []
    return dict(file=name, valid=valid, workload_error=workload_error, frames=len(frames),
                p50_ms=rank(.5), p95_ms=rank(.95), max_ms=max(intervals),
                intervals_over_33_3_ms=sum(x > 33.3 for x in intervals),
                missed_60hz_frames=sum(max(0, math.floor(x / (1000 / 60)) - 1) for x in intervals),
                errors=raw.get('errors'), pass_run=valid and raw.get('errors') == [] and rank(.95) <= 33.3)


if __name__ == '__main__':
    results = [summarize(json.loads(Path(name).read_text()), name) for name in sys.argv[1:]]
    print(json.dumps(dict(runs=results, gate_pass=len(results) == 5 and all(r['pass_run'] for r in results)), indent=2))
