import numpy as np
import os
import glob
import cv2



class UndistortGopro():
    """
    This class undistorts images given in a directory
    the class requieres a 'calibrationdata.npz' file 
    in its very same directory with the 'mtx' and 'dist' matrices
    for the lens_transformation info
    """



    def __init__(self, Dir):
        """ 
        initializes and loads 'calibrationdata.npz' frome  
        <this scripts path> 
        reads the images from the given directory

        Args:
            Dir (str): 
        """

        CalibData = np.load('calibrationdata.npz',allow_pickle=True)
        self.mtx = CalibData['mtx']
        self.dist = CalibData['dist']  
        
        os.chdir(Dir)
        
        if os.path.isfile(Dir):
            self.Images = [Dir.split("\\")[-1]]
            Dir = os.path.dirname(Dir)
        else:  
            self.Images = glob.glob(f'*.jpg')
        
        


    def Undistort(self):
        """
        Utilizes the undistortion parameters obtained via calibration to undistort other images taken from the same
        camera.

        Args:
            img (numpy.ndarray): cv.image, required - The image to be undistorted.
            mtx (numpy.ndarray): The undistortion parameters obtained via calibration.
            dist (numpy.ndarray): The undistortion parameters obtained via calibration.

        Returns:
            undistortedImg (numpy.ndarray): the undistorted image
            roi (list): list of size information of the image
        """
        
        for image in self.Images:
            img = cv2.imread(image)
            h, w = img.shape[:2]
            newCameraMtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w, h), 1, (w, h))
            undistortedImg = cv2.undistort(img, self.mtx, self.dist, None, newCameraMtx)


            # crop the image
            x, y, w, h = roi
            hnew = int(w*7/8)
            undistortedImg = undistortedImg[y:y+hnew, x:x+w]
            
            save_dir = os.path.join(os.getcwd() ,"undistorted")
            if not os.path.isdir(save_dir):
                os.makedirs(save_dir)
            cv2.imwrite(save_dir + "/"+ image[len(image)-12:len(image)-4]+"_undist.jpg", undistortedImg)


if __name__ == '__main__':
    path = r"D:\Dokumente\Uni\Master\Arktis_HIWI\schiff"
    a=UndistortGopro(path)
    a.Undistort()

