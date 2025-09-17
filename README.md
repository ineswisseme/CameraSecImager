**CameraSecImager Plug-In:**


Maya plug-in to help manage relationships between cameras and image planes.
Create image planes and easily link or delink them from specific cameras. The plug-in also put the image plane in the right corner of the camera and allow you to move it on the viewport axis. Image plane name will also show the name of the file it is projecting,
and which camera it is linked to.

![alt text](https://github.com/ineswisseme/CameraSecImager/blob/main/ImageSec.JPG)




UI description:

Left pane shows current image plane in the scene.
Middle pane shows current cameras available.
Right pane shows the Link manager.

Link manager:
Create image plane = Create a standalone image plane node.

Link button = select an image plane, select a camera and click the Link button to link them. Image plane name reflects the name of the camera it is linked to, image is placed right down corner of the camera.

Break Link = select an image plane and a camera then click Break Link button to sever the link between those specific elements.

Clear All = Sever all the links between all the cameras and all the image planes. This only unparent the image planes from the camera, it does not remove the files from the image planes.

Nudge image plane = Allows you to move the offset of the image plane on the Y and X axis. Set your own number to move it in bigger or smaller steps. 

