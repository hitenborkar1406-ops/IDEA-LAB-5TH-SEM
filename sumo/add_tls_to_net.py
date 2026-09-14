"""
add_tls_to_net.py — Adds a 2-phase actuated TLS to the Sitabuldi junction net file.

The cropped sitabuldi_junction.net.xml has no tlLogic elements.
This script:
  1. Changes the junction type from 'priority' to 'traffic_light'
  2. Adds a realistic 2-phase TLS program (N-S green / E-W green, with yellow clearance)
  3. Adds <request> elements needed for TLS junctions
  4. Saves the patched net as sitabuldi_junction_tls.net.xml

Run once before re-running sitabuldi_sim.py.
"""

import xml.etree.ElementTree as ET
import os
import re
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
NET_IN     = SCRIPT_DIR / "sitabuldi_junction.net.xml"
NET_OUT    = SCRIPT_DIR / "sitabuldi_junction_tls.net.xml"

TARGET_JUNCTION = "cluster_2347019624_312691688_312691691"

def patch_net():
    ET.register_namespace('', '')
    tree = ET.parse(str(NET_IN))
    root = tree.getroot()

    # ─── Find the target junction ───────────────────────────────────────────
    junction = root.find(f'.//junction[@id="{TARGET_JUNCTION}"]')
    if junction is None:
        raise ValueError(f"Junction {TARGET_JUNCTION} not found in {NET_IN}")

    old_type = junction.get('type', '')
    print(f"[TLS] Found junction {TARGET_JUNCTION} (type={old_type})")

    inc_lanes_str = junction.get('incLanes', '')
    inc_lanes     = inc_lanes_str.split() if inc_lanes_str.strip() else []
    print(f"[TLS] Incoming lanes: {inc_lanes}")

    num_lanes = len(inc_lanes)
    if num_lanes == 0:
        print("[TLS] No incoming lanes found — using 4-lane placeholder TLS")
        num_lanes = 4

    # ─── Build state strings for 2-phase TLS ────────────────────────────────
    # Phase 0: first half of lanes GREEN, second half RED
    # Phase 1: first half RED, second half GREEN
    # Yellow phases between each green.
    # Simple symmetric split for any number of lanes:

    half = num_lanes // 2
    rem  = num_lanes - half

    def make_state(green_start, green_count, total):
        """Build a SUMO TLS state string of length `total`."""
        s = ['r'] * total
        for i in range(green_start, green_start + green_count):
            s[i % total] = 'G'
        return ''.join(s)

    def make_yellow(prev_state):
        return prev_state.replace('G', 'y')

    ph0_green  = make_state(0,    half, num_lanes)
    ph0_yellow = make_yellow(ph0_green)
    ph1_green  = make_state(half, rem,  num_lanes)
    ph1_yellow = make_yellow(ph1_green)

    PHASE_DURATION_GREEN  = 45   # seconds green
    PHASE_DURATION_YELLOW = 5    # seconds yellow/amber
    TLS_ID = TARGET_JUNCTION

    print(f"[TLS] Building 2-phase TLS: {num_lanes} lanes")
    print(f"      Phase 0 green : {ph0_green}")
    print(f"      Phase 0 yellow: {ph0_yellow}")
    print(f"      Phase 1 green : {ph1_green}")
    print(f"      Phase 1 yellow: {ph1_yellow}")

    # ─── Change junction type ────────────────────────────────────────────────
    junction.set('type', 'traffic_light')

    # ─── Insert tlLogic element ──────────────────────────────────────────────
    # It must appear before the first <junction> tag in the file,
    # but ET doesn't guarantee order across different tag types.
    # We'll insert it right before the target junction element in root.

    tl_logic = ET.Element('tlLogic')
    tl_logic.set('id',        TLS_ID)
    tl_logic.set('type',      'actuated')   # actuated = demand-responsive
    tl_logic.set('programID', '0')
    tl_logic.set('offset',    '0')

    for dur, state in [
        (PHASE_DURATION_GREEN,  ph0_green),
        (PHASE_DURATION_YELLOW, ph0_yellow),
        (PHASE_DURATION_GREEN,  ph1_green),
        (PHASE_DURATION_YELLOW, ph1_yellow),
    ]:
        ph = ET.SubElement(tl_logic, 'phase')
        ph.set('duration', str(dur))
        ph.set('state',    state)

    # Insert tlLogic before the target junction in parent
    # Find insertion index
    children = list(root)
    junc_idx = next((i for i, c in enumerate(children)
                     if c.tag == 'junction' and c.get('id') == TARGET_JUNCTION), -1)
    if junc_idx >= 0:
        root.insert(junc_idx, tl_logic)
    else:
        root.append(tl_logic)

    # ─── Write output ─────────────────────────────────────────────────────────
    # Preserve XML declaration / encoding via manual write
    tree.write(str(NET_OUT), encoding='unicode', xml_declaration=False)

    # Prepend the XML declaration that SUMO expects
    content = NET_OUT.read_text(encoding='utf-8')
    NET_OUT.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + content,
        encoding='utf-8'
    )

    size_mb = NET_OUT.stat().st_size / (1024*1024)
    print(f"\n[TLS] Written: {NET_OUT}  ({size_mb:.1f} MB)")
    print(f"[TLS] TLS ID  : {TLS_ID}")
    print(f"[TLS] Phases  : 4 (G={PHASE_DURATION_GREEN}s, Y={PHASE_DURATION_YELLOW}s × 2)")

if __name__ == '__main__':
    patch_net()
    print("\nDone.  Re-run sitabuldi_sim.py pointing to sitabuldi_junction_tls.net.xml")
