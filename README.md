# maya-lip-joint-builder
Maya (Python) tool for building lip joint behavior from selected controls + animator friendly attributes

To utilize the tool there are some important steps / naming conventions / selection order of controls

This tool adds procedural lip behavior by creating utility nodes between selected controls and existing lip joints.

Features include:
- Arc rotation response
- Lip compression
- Neighbor influence
- Clamp protection
- Animator-friendly custom attributes

## Naming Convention Requirements

Each selected control must end with:

_ctrl

Example:

L_mouth_upper_corner_ctrl

The script automatically searches for:

Tip joint:
L_mouth_upper_corner

Root joint:
L_mouth_upper_corner_root

Naming must follow this relationship:

control = joint name + _ctrl  
root joint = joint name + _root

More INSIGHT (How it works):
basename = ctrl.replace("_ctrl", "")
root = basename + "_root"
tip = basename

## Selection Rules

Run one lip row at a time.

### Top Lip
Select controls from left to right, then run the tool.

### Bottom Lip
Select controls from left to right, then run the tool.

Selection order is important because neighbor influence is determined from adjacent selected controls.

## Launching the Tool

Run the script which builds lipToolUI()
Run lipToolUI()

-This opens the UI used by the shelf tool.
