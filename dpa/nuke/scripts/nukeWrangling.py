#!/usr/bin/python

import nuke
import os, sys
import pwd

if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print "\nInvalid file Path."
        sys.exit(0)
    nodes = []
    for item in sys.argv[1:]:
        filepath,startFrame,endFrame = item.split(',')
        start = int(startFrame)
        end   = int(endFrame)
        readNode = nuke.nodes.Read(file=filepath)
        readNode.knob("first").setValue(start)
        readNode.knob("last").setValue(end)
        readNode.knob("on_error").setValue(3)
        readNode.knob("colorspace").setValue(1)
        nodes.append(readNode)
    if len(nodes) == 0:
        print "\nNo items to read found"
        sys.exit(0)
    print "Number of nodes: " + str(len(nodes))
    viewer   = nuke.nodes.Viewer(inputs=nodes)
    root = nuke.toNode('root')
    root.knob('first_frame').setValue(start)
    root.knob('last_frame').setValue(end)
    savePath = "/tmp/nukeWrangling_" + str(pwd.getpwuid(os.getuid())[0]) 
    os.system( "mkdir -p " + savePath )
    savePath = savePath + "/tmpFile.nk"
    if os.path.exists(savePath):
        os.remove(savePath)
    script   = nuke.toNode('root').name()
    nuke.scriptSaveAs(savePath)
    os.chmod(savePath,777)
    os.system('nuke ' + savePath)
