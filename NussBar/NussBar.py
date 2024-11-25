import os
import unittest
import vtk, qt, ctk, slicer
import logging, time
import numpy, math, slicer, math
from slicer.ScriptedLoadableModule import *
from numpy import mean
from heapq import nsmallest
import numpy as np
try:
  import trimesh
except:
  slicer.util.pip_install('trimesh')
  import trimesh
from scipy.optimize import curve_fit
import random

#
# NussBar
#

class NussBar(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "ShapeNuss"
    self.parent.categories = ["Preoperative Tools"]
    self.parent.dependencies = []
    self.parent.contributors = ["Akhil Deo (Johns Hopkins Laboratory for Computational Sensing and Robotics)"]
    self.parent.helpText = """
This module calculates and outputs the ideal Nuss Bar given the patient's CT scan, markups indicating the location of the bar post-operative, and the desired bar length.
"""
    self.parent.acknowledgementText = """
This module was developed by Akhil Deo. Thank you to Peter Kazanzides and Sam Alaish.
""" 

#
# NussBarWidget
#

class NussBarWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    #####
    ## Visualize CT Scan area
    #####
    self.meshCollapsibleButton = ctk.ctkCollapsibleButton()
    self.meshCollapsibleButton.text = "Visualize CT Scan"
    self.layout.addWidget(self.meshCollapsibleButton)

    # Layout within the sample collapsible button
    self.meshFormLayout = qt.QFormLayout(self.meshCollapsibleButton)

    # The Input Volume Selector
    self.inputFrame = qt.QFrame(self.meshCollapsibleButton)
    self.inputFrame.setLayout(qt.QHBoxLayout())
    self.meshFormLayout.addRow(self.inputFrame)
    self.inputSelector = qt.QLabel("Input Volume: ", self.inputFrame)
    self.inputFrame.layout().addWidget(self.inputSelector)
    self.inputSelector = slicer.qMRMLNodeComboBox(self.inputFrame)
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputFrame.layout().addWidget(self.inputSelector)
    
    self.control_points = None


    # Apply Button 'Create a quick mesh'
    self.applyButton2 = qt.QPushButton("Create 3D Model")
    self.applyButton2.toolTip = "Run the algorithm."
    self.applyButton2.enabled = True
    self.inputFrame.layout().addWidget(self.applyButton2)

    # connections 'Create a quick mesh'
    self.applyButton2.connect('clicked(bool)', self.onApplyButton2)

    #####
    ## Create Nuss Bar area
    #####
    self.parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    self.parametersCollapsibleButton.text = "Create Nuss Bar"
    self.layout.addWidget(self.parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(self.parametersCollapsibleButton)

    # Source points (vtkMRMLMarkupsFiducialNode)
    self.SourceSelector = slicer.qMRMLNodeComboBox()
    self.SourceSelector.nodeTypes = ( ("vtkMRMLMarkupsFiducialNode"), "" )
    self.SourceSelector.addEnabled = True
    self.SourceSelector.removeEnabled = False
    self.SourceSelector.noneEnabled = True
    self.SourceSelector.showHidden = False
    self.SourceSelector.renameEnabled = True
    self.SourceSelector.showChildNodeTypes = False
    self.SourceSelector.setMRMLScene( slicer.mrmlScene )
    self.SourceSelector.setToolTip( "Pick up a Markups node listing fiducials. The name must be different to model name" )
    parametersFormLayout.addRow("Source points: ", self.SourceSelector)
    
    # Textbox for Bar Length
    self.barLength = qt.QLineEdit()
    self.barLength.text = '12'
    self.barLength.frame = True
    self.barLength.cursor = qt.QCursor(qt.Qt.IBeamCursor)
    parametersFormLayout.addRow("Physical Bar Length (in):", self.barLength)

    # Apply Button "Draw Bar Shape"
    self.applyButtonDraw = qt.QPushButton("Draw Bar Shape")
    self.applyButtonDraw.toolTip = "Draw the Nuss Bar Shape given the fiducials"
    parametersFormLayout.addRow(self.applyButtonDraw)

    # connections "Draw Bar Shape"
    self.applyButtonDraw.connect('clicked(bool)', self.onApplyButtonDraw)
    
    # Textbox for Markup Bar Length
    self.markupBarLength = qt.QLineEdit()
    self.markupBarLength.text = '...'
    self.markupBarLength.readOnly = True
    self.markupBarLength.frame = True
    self.markupBarLength.cursor = qt.QCursor(qt.Qt.IBeamCursor)
    self.markupBarLength.styleSheet = "QLineEdit { background:transparent; }"
    parametersFormLayout.addRow("Markup Bar Length (in):", self.markupBarLength)
    
    # Textbox for Generated Bar Length
    self.generatedBarLength = qt.QLineEdit()
    self.generatedBarLength.text = '...'
    self.generatedBarLength.readOnly = True
    self.generatedBarLength.frame = True
    self.generatedBarLength.cursor = qt.QCursor(qt.Qt.IBeamCursor)
    self.generatedBarLength.styleSheet = "QLineEdit { background:transparent; }"
    parametersFormLayout.addRow("Generated Bar Length (in):", self.generatedBarLength)
    
    # Apply Button "Output Generated Nuss Bar"
    self.applyButtonOutput = qt.QPushButton("Output Nuss Bar")
    self.applyButtonOutput.toolTip = "Output the Nuss Bar Shape given the fiducials"
    parametersFormLayout.addRow(self.applyButtonOutput)
    
    # connections "Output Generated Nuss Bar"
    self.applyButtonOutput.connect('clicked(bool)', self.onApplyButtonOutput) # NEED

    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass
  
  def onApplyButtonOutput(self):
    logic = NussBarLogic()
    self.applyButtonOutput.text = "Working..."
    slicer.app.processEvents()
    
    if (self.control_points == None):
      slicer.util.errorDisplay("Please draw the bar shape first.")
      return
    
    logic.output(self.control_points)
    self.applyButtonOutput.text = "Output Nuss Bar"

  def onApplyButton2(self):
    logic = NussBarLogic()
    slicer.app.processEvents()
    logic.mesh(self.inputSelector.currentNode())
    self.applyButton2.text = "Create 3D Model"

  def onSelect(self):
    self.applyButton.enabled = self.inputTargetModelSelector.currentNode() and self.outputSelector.currentNode()

  def getButtonApplyDrawButton(self):
    return self.applyButtonDraw

  def onApplyButtonDraw(self):
    logic = NussBarLogic()
        
    barL, control_points = logic.draw(self.SourceSelector, self.getButtonApplyDrawButton())
    self.control_points = control_points
    
    modelNodes = slicer.util.getNodes('vtkMRMLModelNode*Line*')
    logging.info('Model nodes: ' + str(modelNodes))
    
    self.applyButtonDraw.text = "Draw Bar Shape"
    self.markupBarLength.text = str(barL)

class NussBarLogic(ScriptedLoadableModuleLogic):

  def __init__(self):
    self.StimulationPoint = 0
    self.M1Site = 0
    self.MTunadjusted = 100
    self.curve_actors = []  # List to keep track of curve actors

  def mesh(self, inputVolume):
    """
    From the ExtractSkin.py of lassoan: https://gist.github.com/lassoan/1673b25d8e7913cbc245b4f09ed853f9
    """
    # verifies inputVolume is not empty
    if not inputVolume:
        error_text='Add a volume.nii'
        slicer.util.errorDisplay(error_text, windowTitle='Nuss Bar error', parent=None, standardButtons=None)
        return False
      
    # delete previous model
    for i in range(1, 1000):
      try:
        slicer.mrmlScene.RemoveNode(slicer.util.getNode('vtkMRMLModelNode'+str(i)))
      except:
        pass
    
    for i in range(11, 20):
      try:
        delete_node('ModelDisplay_'  + str(i))
      except:
        pass
    
    # delete previous segmentation
    try:
      for i in range(1, 1000):
          slicer.mrmlScene.RemoveNode(slicer.util.getNode('vtkMRMLSegmentationNode'+str(i)))
    except:
      pass
    
    # update view
    slicer.app.processEvents()
    # force render view
    slicer.app.layoutManager().threeDWidget(0).threeDView().forceRender()
    
    
    # print all registered nodes
    for i in range(0, slicer.mrmlScene.GetNumberOfNodes()):
      logging.info(slicer.mrmlScene.GetNthNode(i).GetName())
    

    logging.info('Processing started')
    # wait popup
    progressBar=slicer.util.createProgressDialog()
    progressBar.labelText='This can take a few minutes'
    slicer.app.processEvents()
    # model filename
    nom = inputVolume.GetName()
    print(nom)
    masterVolumeNode = slicer.util.getNode(nom)
    
    ## Makes the Mesh
    # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
    addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("skin")
    
    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
    
    # Thresholding
    segmentEditorWidget.setActiveEffectByName("Threshold")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold","100") # adjusting according to data
    effect.setParameter("MaximumThreshold","5000") # adjusting according to data
    effect.self().onApply()
    progressBar.value = 10
    
    # Smoothing
    segmentEditorWidget.setActiveEffectByName("Smoothing")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("SmoothingMethod", "MEDIAN")
    effect.setParameter("KernelSizeMm", 10)
    effect.self().onApply()
    print(nom)
    progressBar.value = 30
    
    # Clean up
    segmentEditorWidget = None
    slicer.mrmlScene.RemoveNode(segmentEditorNode)
    
    # Make segmentation results visible in 3D
    segmentationNode.CreateClosedSurfaceRepresentation()
    
    # Fix normals
    surfaceMesh = vtk.vtkPolyData()
    segmentationNode.GetClosedSurfaceRepresentation(addedSegmentID, surfaceMesh)
    normals = vtk.vtkPolyDataNormals() # to normal data
    normals.AutoOrientNormalsOn()
    normals.ConsistencyOn() # to normal data
    normals.SetInputData(surfaceMesh) # to normal data
    normals.Update() # to normal data
    surfaceMesh = normals.GetOutput() # to normal data

    ## Display Output
    progressBar.value = 80
    
    # Write to STL file
    writer = vtk.vtkSTLWriter()
    writer.SetInputData(surfaceMesh)
    volumeNode2 = slicer.util.getNode(nom)
    filename2 = volumeNode2.GetStorageNode().GetFileName()
    nom=filename2+'.stl'
    logging.info('Model is writing')
    writer.SetFileName(nom)
    writer.SetHeader("NussBar output. SPACE=RAS")
    writer.Update()
    
    ## Load this model
    name = inputVolume.GetName()
    volumeNode2 = slicer.util.getNode(name)
    filename2 = volumeNode2.GetStorageNode().GetFileName()
    name2=filename2+'.stl'
    SegNode_View = slicer.util.getNode('vtkMRMLSegmentationNode1')
    SegNode_View.SetDisplayVisibility(0)
    progressBar.value = 80

    slicer.util.loadModel(name2)

    # Add skin color
    ModelNode_color= slicer.util.getNode('vtkMRMLModelNode4')
    displayNode = ModelNode_color.GetDisplayNode()
    RGB_COLOR = 0.6941176470588235, 0.47843137254901963, 0.396078431372549
    displayNode.SetColor(RGB_COLOR)

    base=os.path.basename(name2)
    base2=os.path.splitext(base)[0]

    progressBar.value = 100
    progressBar.close()
    logging.info('Processing completed here '+nom)
  
  def remove_actors(self):
    # Remove 3D curve actors from the 3D view
    view = slicer.app.layoutManager().threeDWidget(0).threeDView()
    renderer = view.renderWindow().GetRenderers().GetFirstRenderer()
    
    actors_to_remove = []
    for actor in renderer.GetActors():
        # Check if the actor is a line (curve) with specific properties
        if (isinstance(actor, vtk.vtkActor) and 
            actor.GetProperty().GetLineWidth() > 1):
            actors_to_remove.append(actor)
    
    for actor in actors_to_remove:
        renderer.RemoveActor(actor)
    
    # Force render to update the view
    view.forceRender()

    # Remove curve model nodes
    curve_nodes = slicer.util.getNodesByClass('vtkMRMLModelNode')
    for node in curve_nodes:
        if node.GetName().startswith('NussCurve_'):
            slicer.mrmlScene.RemoveNode(node)

    # Remove 2D actors from slice views
    for view_name in ["Red", "Yellow", "Green"]:
        slice_view = slicer.app.layoutManager().sliceWidget(view_name).sliceView()
        slice_renderer = slice_view.renderWindow().GetRenderers().GetFirstRenderer()
        actors_to_remove = [actor for actor in slice_renderer.GetActors2D() 
                            if isinstance(actor, vtk.vtkActor2D) and hasattr(actor, 'is_curve_actor')]
        for actor in actors_to_remove:
            slice_renderer.RemoveActor2D(actor)

    # Remove curve model nodes
    old_model_nodes = slicer.util.getNodes('vtkMRMLModelNode*NussCurve*').values()
    for node in old_model_nodes:
        slicer.mrmlScene.RemoveNode(node)
    view.forceRender()

  # Create 2D actor for slice views
  def create_2d_actor(self, renderer, view, curve_source):
    mapper = vtk.vtkPolyDataMapper2D()
    actor = vtk.vtkActor2D()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(random.random(), random.random(), random.random())
    actor.GetProperty().SetLineWidth(10)
    actor.is_curve_actor = True
    renderer.AddActor2D(actor)
    
    # Get the slice node
    sliceNode = view.mrmlSliceNode()
    
    # Create a transform to map from RAS to XY view coordinates
    rasToXY = vtk.vtkTransform()
    xyToRAS = sliceNode.GetXYToRAS()
    rasToXYMatrix = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Invert(xyToRAS, rasToXYMatrix)
    rasToXY.SetMatrix(rasToXYMatrix)
    
    # Transform the curve points
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputConnection(curve_source.GetOutputPort())
    transformFilter.SetTransform(rasToXY)
    transformFilter.Update()
    
    # Set the transformed data to the mapper
    mapper.SetInputConnection(transformFilter.GetOutputPort())
    
    return actor
  
  # sort points
  def sort_points_polar(self, points):
    points_array = np.array(points)
    
    # Find the centermost point
    center = np.mean(points_array[:, :2], axis=0)
    center[1] = np.min(points_array[:, 1]) - 1
    
    # Calculate angles of points relative to the center
    angles = np.arctan2(points_array[:, 1] - center[1], points_array[:, 0] - center[0])
    
    # Adjust angles to go from 0 to 2*pi
    angles = (angles + 2*np.pi) % (2*np.pi)
    
    # Create a custom sorting key
    def sorting_key(angle):
        if np.pi <= angle <= 2*np.pi:
            return angle - np.pi
        else:
            return angle + np.pi
    
    # Sort points based on these adjusted angles
    sorted_indices = sorted(range(len(angles)), key=lambda i: sorting_key(angles[i]))
    sorted_points = points_array[sorted_indices]
    
    return sorted_points
  
  def draw(self, fiducialInput, getApplyButtonDrawButton):
    """
    Draw the Curve
    """
    
    drawButton = getApplyButtonDrawButton
    
    self.remove_actors()
    
    # verifies fiducials have been created
    if not fiducialInput.currentNode():
        error_text='Add at least two fiducials'
        slicer.util.errorDisplay(error_text, windowTitle='Nuss Bar error', parent=None, standardButtons=None)
        return False

    logging.info('Processing started')
    drawButton.text = "Processing..."
    
    # wait popup
    progressBar=slicer.util.createProgressDialog()
    progressBar.labelText='This can take a few minutes'
    slicer.app.processEvents()

    # text view
    view=slicer.app.layoutManager().threeDWidget(0).threeDView()
    view.cornerAnnotation().ClearAllTexts()
    renderer=view.renderWindow().GetRenderers().GetFirstRenderer()
    actors = renderer.GetViewProps()
            
    # fiducial list 
    numFids = fiducialInput.currentNode().GetNumberOfControlPoints()
    progressBar.labelText = "Processing Fiducials..."
    logging.info('Processing fiducials...')
    progressBar.value = 20

    list=[]
    for i in range(numFids):
        ras = [0,0,0]
        fiducialInput.currentNode().GetNthControlPointPosition(i,ras)
        list.append(ras)
        
    # sort list based on x coordinate from least to greatest
    list = sorted(list, key=lambda x: x[0])
    
    progressBar.labelText = "Fiducials processed"
    logging.info('First fiducial: ' + str(list[0]) + '...')
    progressBar.labelText = "Curve fit..."
    logging.info('Curve fit...')
    progressBar.value = 40
    
    # Create control points for Bezier curve
    control_points = []
    for i in range(len(list) - 1):
        p0 = list[i]
        p1 = list[i+1]
        control_points.append(p0)
        
    control_points.append(list[-1])
    control_points = self.sort_points_polar(control_points)
    
    progressBar.value = 50
    progressBar.labelText = "Create curve"
    logging.info('Create VTK PolyData...')
    
    # Create a VTK PolyData object for the line
    line_points = vtk.vtkPoints()
    for i in range(len(control_points)):
        line_points.InsertNextPoint(control_points[i][0], control_points[i][1], control_points[i][2])
    
    spline = vtk.vtkParametricSpline()
    spline.SetPoints(line_points)
    curve_source = vtk.vtkParametricFunctionSource()
    curve_source.SetParametricFunction(spline)
    curve_source.Update()    
    progressBar.value = 60
    progressBar.labelText = "Plot curve..."
    logging.info('Create mapper...')
        
    # Create a mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(curve_source.GetOutput())

    # Create an actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(random.random(), random.random(), random.random())
    actor.GetProperty().SetLineWidth(10)  
    actor.is_curve_actor = True

    # Add the actor to the renderer
    renderer = view.renderWindow().GetRenderers().GetFirstRenderer()
    renderer.AddActor(actor)
    progressBar.value = 70
    view.forceRender()

    # Get the slice view renderers
    red_renderer = slicer.app.layoutManager().sliceWidget("Red").sliceView().renderWindow().GetRenderers().GetFirstRenderer()
    yellow_renderer = slicer.app.layoutManager().sliceWidget("Yellow").sliceView().renderWindow().GetRenderers().GetFirstRenderer()
    green_renderer = slicer.app.layoutManager().sliceWidget("Green").sliceView().renderWindow().GetRenderers().GetFirstRenderer()

    red_view = slicer.app.layoutManager().sliceWidget("Red").sliceView()
    yellow_view = slicer.app.layoutManager().sliceWidget("Yellow").sliceView()
    green_view = slicer.app.layoutManager().sliceWidget("Green").sliceView()

    # Create 2D mappers and actors for slice views
    red_mapper = vtk.vtkPolyDataMapper2D()
    red_mapper.SetInputData(curve_source.GetOutput())
    red_actor = self.create_2d_actor(red_renderer, red_view, curve_source)
    red_renderer.AddActor2D(red_actor)

    yellow_mapper = vtk.vtkPolyDataMapper2D()
    yellow_mapper.SetInputData(curve_source.GetOutput())
    yellow_actor = self.create_2d_actor(yellow_renderer, yellow_view, curve_source)
    yellow_renderer.AddActor2D(yellow_actor)

    green_mapper = vtk.vtkPolyDataMapper2D()
    green_mapper.SetInputData(curve_source.GetOutput())
    green_actor = self.create_2d_actor(green_renderer, green_view, curve_source)
    green_renderer.AddActor2D(green_actor)
    
    # Remove old model nodes
    old_model_nodes = slicer.util.getNodes('vtkMRMLModelNode*Line*').values()
    for node in old_model_nodes:
        slicer.mrmlScene.RemoveNode(node)
    
    # Create a model node
    modelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
    modelNode.SetName('NussCurve_' + str(random.randint(1, 1000)))
    modelNode.SetAndObservePolyData(curve_source.GetOutput())
    modelNode.CreateDefaultDisplayNodes()
    modelNode.GetDisplayNode().SetColor(random.random(), random.random(), random.random())  
    modelNode.GetDisplayNode().SetLineWidth(10)
    
    view.forceRender()
    progressBar.value = 90
    
    # set line color to random color
    modelNode.GetDisplayNode().SetColor(random.random(), random.random(), random.random())  
    modelNode.GetDisplayNode().SetLineWidth(10)  
        
    # display output
    logging.info('Processing completed')
    progressBar.labelText = "Processing completed"
    progressBar.value = 100
    progressBar.close()
    
    # Returns the arc length
    def arc_length(x, y):
      return np.sum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
    
    # Convert arc length from millimeters to inches
    def mm_to_in(mm):
      return mm * 0.0393701

    return round(mm_to_in(arc_length(np.array(list)[:,0], np.array(list)[:,1])), 4), control_points
  
  def output(self, control_points):
    # turn control_points into 3D by extruding the points 7.5 millimeters up and down and 1 millimeter up and down
    extrusion_width = 7.5  # this is in millimeters
    extrusion_depth = 1  # this is in millimeters
    
    vertices = []
    triangles = []
    
    for i, point in enumerate(control_points):
        # Create 4 vertices for each control point
        vertices.append([point[0], point[1] + extrusion_depth, point[2] + extrusion_width])
        vertices.append([point[0], point[1] + extrusion_depth, point[2] - extrusion_width])
        vertices.append([point[0], point[1] - extrusion_depth, point[2] + extrusion_width])
        vertices.append([point[0], point[1] - extrusion_depth, point[2] - extrusion_width])
        
        if i < len(control_points) - 1:
            base = i * 4
            next_base = (i + 1) * 4
            
            # Front face
            triangles.append([base, next_base, next_base + 1])
            triangles.append([base, next_base + 1, base + 1])
            
            # Back face
            triangles.append([base + 2, next_base + 3, next_base + 2])
            triangles.append([base + 2, base + 3, next_base + 3])
            
            # Top face
            triangles.append([base, next_base + 2, next_base])
            triangles.append([base, base + 2, next_base + 2])
            
            # Bottom face
            triangles.append([base + 1, next_base + 1, next_base + 3])
            triangles.append([base + 1, next_base + 3, base + 3])
    
    # Add end caps correctly
    triangles.append([0, 1, 2])
    triangles.append([1, 3, 2])
    
    last = len(vertices) - 4
    triangles.append([last, last + 1, last + 2])
    triangles.append([last + 1, last + 3, last + 2])
    
    mesh = trimesh.Trimesh(vertices, faces=triangles, process=False)
    
    # Allow user to specify where to save the file as an obj
    save_path = qt.QFileDialog.getSaveFileName(None, 'Save Nuss Bar', '', 'OBJ (*.obj)')
    if save_path:
        mesh.export(save_path, file_type='obj')
    else:
        slicer.util.errorDisplay('Please specify a save path.')
        return
      