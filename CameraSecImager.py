import maya.cmds as cmd
import maya.mel as mel
import os
    
    
# declaring variables: 

IMG_PLANE_LIST = "imgPlaneList" # kinda self explanatory
selected_plane = None # same
IMG_PLANE_MAP = {} # used to dict image plane node name to its visual UI name
PER_JOB_ID = [] # empty list to kill runaway script jobs 



def get_imgPlane_list(*args):   
    """Populate the textScrollList with all imagePlane nodes. In UI imgPlanes will be shown as their file names if there is one, and the camera name it is linked to if there is one."""
    
    
    # we need to make sure we kill the run-away script jobs hence the try loop:
    
    for jbid in list(PER_JOB_ID):
        try:
            if cmd.scriptJob(exists=jbid):
                cmd.scriptJob(kill=jbid, force=True)
        except Exception:
            pass
                
    PER_JOB_ID[:] = []    
    
    if cmd.textScrollList(IMG_PLANE_LIST, exists=True):
        cmd.textScrollList(IMG_PLANE_LIST, e=True, ra=True)
        
         
             
        planes = [p.split("->")[-1] for p in (cmd.ls(type="imagePlane") or [])] # removing parent path for better visual.
        
        for pl in planes: 
            file_path = cmd.getAttr(f"{pl}.imageName")  or "<noFile>"
            file_name = os.path.basename(file_path) if file_path else "<no file>" 
            
            cam = get_camera_for_image_plane(pl)
            cam_label = f"({cam})" if cam else ""
            display_str = f"{file_name}   [{pl}]         {cam_label}"
            cmd.textScrollList(IMG_PLANE_LIST, e=True, a=display_str)
            IMG_PLANE_MAP[display_str] = pl 
            
            
            try:
                jbid1 = cmd.scriptJob(attributeChange=[f"{pl}.imageName", get_imgPlane_list],protected=True,parent="CameraSecImager")
                jbid2 = cmd.scriptJob(nodeDeleted=[pl, get_imgPlane_list], protected=True, parent="CameraSecImager")
                
                PER_JOB_ID.extend([jbid1,jbid2])
                
            except:
                pass
        
        
def select_imgPlane(*args):
    """Select the scene imagePlane after selecting its equivalent in th UI."""
    sel = cmd.textScrollList(IMG_PLANE_LIST, q=True, si=True) or []          
    if sel:
        plane_node = IMG_PLANE_MAP.get(sel[0])
        if plane_node:
            cmd.select(plane_node, r=True)
            return
   
    
    
def create_imgPlane():
    """ Create an image plane node. """
    imgPlane = cmd.imagePlane(name="ImgPlane")
    


def cleanup_empty_groups():
    """ Delete empty groups left behind by image plane linking. """
    groups = cmd.ls(type="transform") or []
    to_delete = []

    for g in groups:
        # Skip if it has children or shapes
        if cmd.listRelatives(g, shapes=True) or cmd.listRelatives(g, children=True):
            continue
        to_delete.append(g)

    if to_delete:
        try:
            cmd.delete(to_delete)
            cmd.inViewMessage(amg=f"Deleted {len(to_delete)} empty groups", pos="topCenter", fade=True)
        except Exception as e:
            cmd.warning(f"Could not delete groups: {e}")
            
            
    
def link_imgPlane():
    """ Link selected image plane to selected camera and move it to the bottom right corner. This function references two helpers. """
    
    # get camera:
        
    cam_sel = cmd.ls(sl=True,dag=True,type="camera") or []
    
    if not cam_sel:
        cmd.warning("Please select a camera to link to the image plane!")
        return
    
    cam_shape = cam_sel[0]
    
    
    
    # Get image plane:
        
    sel_ui = cmd.textScrollList(IMG_PLANE_LIST, q=True, si=True) or []
    if not sel_ui:
        cmd.warning("Please select an image plane to link to the camera!")
        return
        
    old_plane = IMG_PLANE_MAP.get(sel_ui[0])
    if not old_plane or not cmd.objExists(old_plane):
        cmd.warning("Selected image plane does not exist anymore.")
        return
        
    file_path = cmd.getAttr(f"{old_plane}.imageName")
    
    try:
        cmd.delete(old_plane)
    except Exception as e:
        cmd.warning(f"Failed to switch old image plane: {e}")

    try:
        _, new_plane = cmd.imagePlane(camera=cam_shape)
        if file_path:
            cmd.setAttr(f"{new_plane}.imageName", file_path, type="string")
    except Exception as e:
        cmd.warning(f"Could not create camera image plane: {e}")
        return
    
    cleanup_empty_groups()
    get_imgPlane_list() 
    
    # Move imgPlane to the bottom right:
        
    try:
        cmd.setAttr(f"{new_plane}.displayOnlyIfCurrent", 1)
        if cmd.control("AttrEdImagePlaneFormLayout", exists=True):
            cmd.refreshEditorTemplates()

        mel_cmd = f'AEchangeLookThroughCamera "{cam_shape}->{new_plane}";'
        mel.eval(mel_cmd)
        cmd.setAttr(f"{new_plane}.fit", 1)          
        cmd.setAttr(f"{new_plane}.depth", 100)
        cmd.setAttr(f"{new_plane}.sizeX", 0.4)      
        cmd.setAttr(f"{new_plane}.sizeY", 0.4)
        cmd.setAttr(f"{new_plane}.offsetX", 0.5)    
        cmd.setAttr(f"{new_plane}.offsetY", -0.260)
        
    except Exception as e:
        cmd.warning(f"Could not position image plane: {e}")
       
    
    get_imgPlane_list() # we don't forget to update the imgPlane list
    
    cmd.inViewMessage(amg="Linked image plane to camera", pos="topCenter", fade=True)



def get_camera_for_image_plane(planes):
    """Return the camera connected to this image plane, or None."""
    cams = cmd.listConnections(planes, type="camera") or []
    return cams[0] if cams else None
    
    

def break_link():
    """ Break the parent link between an image plane and a camera. """
    
     # Get selected camera:
    cam = cmd.ls(sl=True, dag=True, type="camera") or []
    if not cam:
        cmd.warning("Please select a camera first!")
        return
    cam_shape = cam[0]
    
    
    # Get selected image plane from UI:
        
    sel_ui = cmd.textScrollList(IMG_PLANE_LIST, q=True, si=True) or []
    if not sel_ui:
        cmd.warning("Please select an image plane from the list!")
        return
        
    plane_node = IMG_PLANE_MAP.get(sel_ui[0])
    if not plane_node or not cmd.objExists(plane_node):
        cmd.warning("Selected image plane does not exist anymore.")
        return
    
    # Unparent Attr "message" from the camera:
        
    conns = cmd.listConnections(f"{plane_node}.message", plugs=True, connections=True) or []
    for i in range(0, len(conns), 2):
        src, dst = conns[i], conns[i+1]
        if dst.startswith(f"{cam_shape}.imagePlane"):
            try:
                cmd.disconnectAttr(src, dst)
                cmd.inViewMessage(amg="Unlinked image plane from camera", pos="topCenter", fade=True)
                break
            except Exception as e:
                cmd.warning(f"Could not disconnect: {e}")
                return
        
        
    # refresh the UI now
    
    get_imgPlane_list()


def clear_all_links(*args):
    """ Disconnect all the imgPlanes from their cameras. """
    
    cameras = cmd.ls(type="camera") or []
    if not cameras:
        cmd.warning("No cameras found!")
        return
        
    for cam_shape in cameras:
        indices = cmd.getAttr(f"{cam_shape}.imagePlane", multiIndices=True) or []
        for i in indices:
            dest_attr = f"{cam_shape}.imagePlane[{i}]"
            
            conns = cmd.listConnections(dest_attr, plugs=True, source=True) or []
            for src in conns:
                try:
                    cmd.disconnectAttr(src, dest_attr)
                except Exception as e:
                    cmd.warning(f"Could not disconnect {src} from {dest_attr}: {e}")

    cmd.inViewMessage(amg="All image planes disconnected from all cameras", pos="topCenter", fade=True)
    
    # reset the UI:
    
    get_imgPlane_list()


# quad buttons:

def move_offset(dx=0, dy=0):
    """Nudge the image plane offset by dx, dy. Used with the arrow buttons."""
    
    sel = cmd.textScrollList(IMG_PLANE_LIST, q=True, si=True) or []
    if not sel:
        cmd.warning("Please select an image plane from the list!")
        return
    
    label = sel[0]
    plane_node = IMG_PLANE_MAP.get(label)
      
    if not cmd.objExists(plane_node):
        cmd.warning(f"Image plane '{plane_node}' does not exist anymore.")
        return
    
    step = cmd.floatField("stepSizeField", q=True, v=True)        
        
    offsetX = cmd.getAttr(f"{plane_node}.offsetX") + dx * step
    offsetY = cmd.getAttr(f"{plane_node}.offsetY") + dy * step
   
    cmd.setAttr(f"{plane_node}.offsetX", offsetX)
    cmd.setAttr(f"{plane_node}.offsetY", offsetY)
    
    
#### UI #### 
     
def CameraSecImagerUI():
    """ Creates UI for CameraSecImager(), links helper functions to UI. """ 
    
    if cmd.window("CameraSecImager", exists=True):
        cmd.deleteUI("CameraSecImager")
        
    
    win = cmd.window("CameraSecImager", title="CameraSecImager",s=False, rtf=True)

    
    frame00 = cmd.frameLayout(parent=win, label="CameraSecImager", fn="boldLabelFont", h=350, w=300, la="top", li=400, mh=5, mw=5)   
    gridall = cmd.gridLayout(parent=frame00, nc=3, nr=1, cwh=(300,350))     
    frame01 = cmd.frameLayout(parent=gridall, label=" Available Image Planes", fn="boldLabelFont")
    cmd.frameLayout(parent=frame01, label="File               |          Image Plane         |        Camera ", fn="obliqueLabelFont")
    window_img = cmd.scrollLayout(parent=frame01, cr=True)
    cmd.textScrollList(IMG_PLANE_LIST,parent=window_img,allowMultiSelection=False,selectCommand=select_imgPlane, h=298)
    frame02 = cmd.frameLayout(parent=gridall, label=" Available Cameras", fn="boldLabelFont") 
    window_cam = cmd.outlinerPanel(parent=frame02, mbv=False)
    cmd.outlinerEditor(window_cam, edit=True, mainListConnection='worldList', selectionConnection='modelList', showShapes=False, showAttributes=False, showConnected=False, showAnimCurvesOnly=False, autoExpand=False, showDagOnly=True, ignoreDagHierarchy=False, expandConnections=False, showNamespace=True, showCompounds=True, showNumericAttrsOnly=False, highlightActive=True, autoSelectNewObjects=False, doNotSelectNewObjects=False, transmitFilters=False, showSetMembers=False, filter='DefaultCameraShapesFilter')   
    buttonframe = cmd.frameLayout(parent=gridall, label=" Link Manager", fn="boldLabelFont", mh=10, mw=10)
    buttoncolumn = cmd.columnLayout(parent=buttonframe, rs=10)
    cmd.text(parent=buttoncolumn, label="Create an image plane node:", fn= "boldLabelFont")    
    cmd.button(parent=buttoncolumn, label="Create Image Plane", w=120, h=30, command="create_imgPlane()")
    cmd.text(parent=buttoncolumn, label="Link a Camera and an Image Plane:", fn= "boldLabelFont")
    cmd.button(parent=buttoncolumn, label="Link",w=120, h=30, command="link_imgPlane()")
    cmd.text(parent=buttoncolumn, label="Break the link between a Camera | Image Plane:", fn= "boldLabelFont")
    cmd.button(parent=buttoncolumn, label="Break Link",w=120, h=30, command="break_link()")
    cmd.text(parent=buttoncolumn, label="Reset all links:", fn= "boldLabelFont")
    cmd.button(parent=buttoncolumn, label="Clear All",w=120, h=30, command="clear_all_links()")  
    cmd.text(parent=buttoncolumn, label="Nudge Image Plane:                     Unit:", fn= "boldLabelFont")
    buttonrow = cmd.rowLayout(parent=buttonframe, nc=10)   
    cmd.iconTextButton(parent=buttonrow,image="arrowLeft.png", w=30, h=30, ebg=True, command=lambda *_: move_offset(-1, 0))
    cmd.separator(style='single',w=5) 
    cmd.iconTextButton(parent=buttonrow,image="arrowUp.png", w=30, h=30, ebg=True, command=lambda *_: move_offset(0, 1)) 
    cmd.separator(style='single',w=5) 
    cmd.iconTextButton(parent=buttonrow,image="arrowRight.png", w=30, h=30, ebg=True, command=lambda *_: move_offset(1, 0)) 
    cmd.separator(style='single',w=5) 
    cmd.iconTextButton(parent=buttonrow,image="arrowDown.png", w=30, h=30, ebg=True, command=lambda *_: move_offset(0, -1))
    cmd.separator(style='single',w=15) 
    cmd.floatField("stepSizeField", v=0.1, pre=2)
    cmd.showWindow()
       
                      
    get_imgPlane_list()
    
    
    
    #script jobs:
  
    cmd.scriptJob(event=["DagObjectCreated", get_imgPlane_list], protected=True, parent="CameraSecImager")
    cmd.scriptJob(event=["NameChanged", get_imgPlane_list], protected=True, parent="CameraSecImager")
    
   
    


CameraSecImagerUI()       

