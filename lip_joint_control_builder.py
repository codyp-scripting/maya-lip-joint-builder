# Lip joint builder tool script
# Maya Python utility for building lip joint behavior from selected controls
# Includes arc rotation, compression, neighbor influence, and clamp protection 

import maya.cmds as cmds

# Neighbor Detection Using Selection Order

def getNeighborsFromSelection(ctrls, index):

    neighbors = []

    if index > 0:
        neighbors.append(ctrls[index-1])

    if index < len(ctrls)-1:
        neighbors.append(ctrls[index+1])

    return neighbors

# Build System

def buildLipJointSystem():

    ctrls = cmds.ls(sl=True)

    if not ctrls:
        cmds.warning("Select lip controls")
        return

    builtCount = 0

    for i, ctrl in enumerate(ctrls):

        if not ctrl.endswith("_ctrl"):
            cmds.warning(ctrl + " is not a control")
            continue

        base = ctrl.replace("_ctrl", "")

        root = base + "_root"
        tip = base

        # Prevent duplicate build
        if cmds.objExists(ctrl + "_rotMult"):
            cmds.warning(ctrl + " already has a lip system. Skipping.")
            continue

        # Verify joints exist
        if not cmds.objExists(root) or not cmds.objExists(tip):
            cmds.warning("Missing joints for " + ctrl)
            continue

        # Add animator attributes

        if not cmds.attributeQuery("ArcStrengthX", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="ArcStrengthX", at="double", dv=10, k=True)

        if not cmds.attributeQuery("ArcStrengthY", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="ArcStrengthY", at="double", dv=-10, k=True)

        if not cmds.attributeQuery("LipCompression", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="LipCompression", at="double", dv=-0.5, k=True)

        if not cmds.attributeQuery("MinLipLength", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="MinLipLength", at="double", dv=0.25, k=True)

        if not cmds.attributeQuery("NeighborFollow", node=ctrl, exists=True):
            cmds.addAttr(ctrl, ln="NeighborFollow", at="double", min=0, max=1, dv=0.3, k=True)

        # Rotation Arc

        rotMult = cmds.createNode("multiplyDivide", n=ctrl + "_rotMult")

        cmds.connectAttr(ctrl + ".translateX", rotMult + ".input1X")
        cmds.connectAttr(ctrl + ".translateY", rotMult + ".input1Y")

        cmds.connectAttr(ctrl + ".ArcStrengthX", rotMult + ".input2X")
        cmds.connectAttr(ctrl + ".ArcStrengthY", rotMult + ".input2Y")

        # Compression System

        squareNode = cmds.createNode("multiplyDivide", n=ctrl + "_squareX")
        cmds.setAttr(squareNode + ".operation", 3)
        cmds.setAttr(squareNode + ".input2X", 2)

        cmds.connectAttr(ctrl + ".translateX", squareNode + ".input1X")

        sqrtNode = cmds.createNode("multiplyDivide", n=ctrl + "_sqrtX")
        cmds.setAttr(sqrtNode + ".operation", 3)
        cmds.setAttr(sqrtNode + ".input2X", 0.5)

        cmds.connectAttr(squareNode + ".outputX", sqrtNode + ".input1X")

        compMult = cmds.createNode("multiplyDivide", n=ctrl + "_compressMult")

        cmds.connectAttr(sqrtNode + ".outputX", compMult + ".input1X")
        cmds.connectAttr(ctrl + ".LipCompression", compMult + ".input2X")

        # Length Offset

        baseLength = cmds.getAttr(tip + ".translateZ")

        offsetNode = cmds.createNode("plusMinusAverage", n=ctrl + "_lengthOffset")
        cmds.setAttr(offsetNode + ".operation", 1)

        cmds.setAttr(offsetNode + ".input1D[0]", baseLength)

        cmds.connectAttr(compMult + ".outputX", offsetNode + ".input1D[1]")

        # Neighbor Influence System

        neighbors = getNeighborsFromSelection(ctrls, i)

        neighborAdd = cmds.createNode("plusMinusAverage", n=ctrl + "_neighborAdd")

        # Main control goes first
        cmds.connectAttr(rotMult + ".outputX", neighborAdd + ".input2D[0].input2Dx")
        cmds.connectAttr(rotMult + ".outputY", neighborAdd + ".input2D[0].input2Dy")

        for n, nCtrl in enumerate(neighbors):

            # Use neighbor control translate directly scaled by NeighborFollow
            neighborMult = cmds.createNode(
                "multiplyDivide",
                n=ctrl + "_" + nCtrl + "_neighborFollow_mult"
            )

            # X direct
            cmds.connectAttr(nCtrl + ".translateX", neighborMult + ".input1X")
 
            # Y inverted
            invertMult = cmds.createNode(
                "multiplyDivide",
                n=ctrl + "_" + nCtrl + "_neighborInvert_mult"
            )
 
            cmds.connectAttr(nCtrl + ".translateY", invertMult + ".input1Y")
            cmds.setAttr(invertMult + ".input2Y", -1)
 
            cmds.connectAttr(invertMult + ".outputY", neighborMult + ".input1Y")
 
            # Neighbor strength
            cmds.connectAttr(ctrl + ".NeighborFollow", neighborMult + ".input2X")
            cmds.connectAttr(ctrl + ".NeighborFollow", neighborMult + ".input2Y")
 
            cmds.connectAttr(
                neighborMult + ".outputX",
                neighborAdd + ".input2D[%d].input2Dx" % (n+1)
            )
 
            cmds.connectAttr(
                neighborMult + ".outputY",
                neighborAdd + ".input2D[%d].input2Dy" % (n+1)
            )

        # Final combined output
        cmds.connectAttr(neighborAdd + ".output2Dx", root + ".rotateY", force=True)
        cmds.connectAttr(neighborAdd + ".output2Dy", root + ".rotateX", force=True)

        # Clamp Protection

        clampNode = cmds.createNode("clamp", n=ctrl + "_lengthClamp")

        minMult = cmds.createNode("multiplyDivide", n=ctrl + "_minLengthMult")

        cmds.connectAttr(ctrl + ".MinLipLength", minMult + ".input1X")
        cmds.setAttr(minMult + ".input2X", baseLength)

        cmds.connectAttr(minMult + ".outputX", clampNode + ".minR")

        cmds.setAttr(clampNode + ".maxR", baseLength)

        cmds.connectAttr(offsetNode + ".output1D", clampNode + ".inputR")

        cmds.connectAttr(clampNode + ".outputR", tip + ".translateZ")

        builtCount += 1

    print("Lip systems successfully built for", builtCount, "controls")

# Error Safe Runner

def runLipBuilder():

    ctrls = cmds.ls(sl=True)

    if not ctrls:
        cmds.warning("Please select at least one lip control.")
        cmds.confirmDialog(
            title="Lip Builder",
            message="Please select at least one lip control before running the tool.",
            button=["OK"]
        )
        return

    buildLipJointSystem()

# UI Window

def lipToolUI():

    if cmds.window("lipToolWin", exists=True):
        cmds.deleteUI("lipToolWin")

    win = cmds.window(
        "lipToolWin",
        title="Lip Joint Builder",
        widthHeight=(260, 140)
    )

    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    cmds.text(label="Lip Joint Builder", height=30, align="center")

    cmds.separator()

    cmds.text(label="1. Select mouth controls L to R (one row at a time)")
    cmds.text(label="   (example: *_ctrl)")
    cmds.text(label="2. Press Build")

    cmds.separator()

    cmds.button(
        label="Build Lip System",
        height=40,
        command=lambda x: runLipBuilder()
    )

    cmds.showWindow(win)