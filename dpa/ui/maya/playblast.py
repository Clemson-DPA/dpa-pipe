
# PB - PlayBlaster
# Generates playblast from current maya scene. Includes camera focal length.

import maya.cmds as cmds
import os


#from dpaCreateFS import *
from dpa.ptask.area import PTaskArea




def playblast_dialog():
  # Creates a dialog prompt to determine if the user wishes to create a playblast
  #response = cmds.confirmDialog( title='Playblast', message='Are you SURE you want to create a new playblast?', button=['Yes','No'], defaultButton='No', cancelButton='No', dismissString='No' )
  #if response == 'Yes':
  floatUI()

def floatUI():
  # Check to see if window exists
  if cmds.window("PBQuality", exists=True):
    cmds.deleteUI("PBQuality")

  # Create window
  window = cmds.window("PBQuality", title="DPA Playblast", w=300, h=100, mnb=False, mxb=False, sizeable=False)

  # Create a main layout
  mainLayout = cmds.columnLayout(adj=True)
  blastLayout = cmds.columnLayout("blastLayout", p=mainLayout, w=260, adj=False, rs=5, cat=('left', 5))
  cmds.separator(p=blastLayout)

  cmds.text(label="Enter desired playbast quality:", p=blastLayout)
  qualityField = cmds.floatField("playblastValue", p=blastLayout, w=250, min=50, max=100, pre=0, step=1, v=90, ed=True)
  qualitySlider = cmds.floatSlider("playblastPercentage", p=blastLayout, w=250, min=50, max=100, step=1, v=90, dc=updatePercent)
  cmds.separator(p=blastLayout)

  sequenceOption = cmds.checkBox("sequenceOption", label="From Sequence", value=False)
  reviewOption = cmds.checkBox("reviewOption", label="Auto-bot review submission", value=False)
  cmds.separator(p=blastLayout)

  confirmLayout = cmds.rowColumnLayout("confirmLayout", p=mainLayout, w=250, nc=2, rs=(5, 5), co=[(1, 'left', 5), (2, 'right', 5)], cw=[(1, 125), (2, 125)])
  cancelButton = cmds.button("cancelButton", p=confirmLayout, label="Cancel", c="cmds.deleteUI('PBQuality')", w=80, h=30)
  pbButton = cmds.button("pbButton", p=confirmLayout, label="Playblast", c=handlePB, w=100, h=30)
  cmds.separator(p=confirmLayout)

  cmds.showWindow(window)

def updatePercent(*args):
  percent = cmds.floatSlider("playblastPercentage", q=True, v=True)
  cmds.floatField("playblastValue", e=True, v=percent)

def handlePB(*args):
  percent = cmds.floatField("playblastValue", q=True, v=True)
  #check to see if sequence option is selected
  seqTag = cmds.checkBox("sequenceOption", query=True, value =True)
  #check for auto review submission
  revTag = cmds.checkBox("reviewOption", query=True, value =True)
  runPB(percent, seqTag, revTag)

def runPB(quality, sequence, autoReview):
  #Get the file unix path of the maya file
  filePath = cmds.file(q=True, sceneName=True)
  #Parse the unix path and convert it into a dpa fspattern

  if quality < 50:
    print "Lower than 50 percent quality may result in very poor imaging..."
    cmds.deleteUI("PBQuality")
    return

  print "Percentage chosen: " + str(quality)
  print "From Sequence: " + str(sequence)
  print "AutoSubmit: " + str(autoReview)

  #Attempts to create a playblast of the current maya scene
  success = playblaster(quality, sequence, autoReview)

  if success:
    print "Successfully generated playblast :)"
  else:
    print "Failed to generate playblast :("

def playblaster(quality, sequence, autoReview):
  #Does some error checking to ensure the fspattern is correct
    area = PTaskArea.current()
    spec = None
    if area:
        spec = area.spec
    else:
        print "You need to dpaset into a ptask to use this tool."
        return False
    currentCam = cmds.modelPanel(cmds.getPanel(wf=True), q=True, cam=True)
    currentCamMunged = currentCam.replace( '|', '_' )
    focalLength = cmds.camera(currentCam, q=True, fl=True)
    cameraName = currentCamMunged.title() + "Fov" + str(focalLength)
    print "Camera Name: " + cameraName
    specName = spec.name(spec).title()

    if not autoReview:
        playblastdir = "/scratch" + area.dir()
        #listing = os.listdir(playblastdir)
        print "Making directory " + playblastdir
        os.system( "mkdir -p " + playblastdir ) 
        #get a listing of the version numbers in the directory
        nbversions = len(os.listdir(playblastdir))
        versionFrame = "%04d" % (nbversions + 1 )
        fileName = "%s/playblast%s%s-%s" % (playblastdir,specName,cameraName,versionFrame)
        print "writing playblast to file " + fileName + ".mov"
        xVal = cmds.getAttr('defaultResolution.width')
        yVal = cmds.getAttr('defaultResolution.height')
        if sequence:
            sqMgr = cmds.listConnections('sequenceManager1', s=True, d=False)[0]
            seqEnd = cmds.getAttr(str(sqMgr)+".maxFrame")
            seqStart = cmds.getAttr(str(sqMgr) +".minFrame")
            print "SqStart: " + str(seqStart)
            print "SqEnd: " + str(seqEnd)
            cmds.playblast(startTime=seqStart, endTime=seqEnd, sequenceTime=sequence, f=fileName, percent=quality, offScreen=True, format="qt", width=xVal, height=yVal)
        else:
            cmds.playblast(f=fileName, percent=quality, offScreen=True, format="qt", width=xVal, height=yVal)
        cmds.deleteUI("PBQuality")
        os.chmod(fileName+ ".mov", 0777)
        os.system( "vlc " + fileName + ".mov &" )
        return True
    if autoReview:
        #create a product to put this in
        xVal = cmds.getAttr('defaultResolution.width')
        yVal = cmds.getAttr('defaultResolution.height')
        product_spec = "playblast=movie"
        product_type = "mov"
        product_resolution = str(xVal) + "x" + str(yVal)
        product_description = "auto generated in dpa playblast tool"
        from dpa.action.registry import ActionRegistry
        create_action_cls = ActionRegistry().get_action('create', 'product')
        create_action = create_action_cls(product=product_spec, ptask=spec, description=product_description, file_type=product_type, resolution=product_resolution )
        try:
            create_action()
        except ActionError as e:
            raise EntityError("Unable to create a product: " + str(e) )

        #use product to get the directory path
        area = create_action.product_repr.area
        playblastdir = area.dir()
        versionFrame = create_action.product_version.number_padded
        baseFileName = "playblast%s%s-%s" % (specName,cameraName,versionFrame)
        fileName = playblastdir + "/" + baseFileName
        print "writing playblast to file " + fileName + ".mov"
        if sequence:
            sqMgr = cmds.listConnections('sequenceManager1', s=True, d=False)[0]
            seqEnd = cmds.getAttr(str(sqMgr)+".maxFrame")
            seqStart = cmds.getAttr(str(sqMgr) +".minFrame")
            print "SqStart: " + str(seqStart)
            print "SqEnd: " + str(seqEnd)
            cmds.playblast(startTime=seqStart, endTime=seqEnd, sequenceTime=sequence, f=fileName, percent=quality, offScreen=True, format="qt", width=xVal, height=yVal)
        else:
            cmds.playblast(f=fileName, percent=quality, offScreen=True, format="qt", width=xVal, height=yVal)
        cmds.deleteUI("PBQuality")
        os.chmod(fileName+ ".mov", 0777)
        reviewcmd = "cd " + playblastdir + "; dpacreatereview " + baseFileName + ".mov " +  str(create_action.product_repr.spec)
        print "creating review: " + reviewcmd
        os.system( reviewcmd )
        os.system( "vlc " + fileName + ".mov &" )
        return True

    cmds.error("Invalid selections.")
    return False
    
