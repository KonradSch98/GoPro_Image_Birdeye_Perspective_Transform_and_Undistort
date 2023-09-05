import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import ImageDraw, Image
import os
import copy
import subprocess
import glob
import shutil

#local import
from undistort_class import UndistortGopro



#################################################################################




class BirdeyeProjection():

    
    
    def __init__(self, Dir = None, Height = None):
        """
        This class gives an (interactive) package to project GoPro (11 black)
        Images into BirdEye view. 

        Can deal with either single file and foldere of files 

        Handles dir request, error handling
        type and metadata search/reading
        geometric calculations of the photographed landscape
        the projection
        and a FishEye undistort algorithm if necessary


        
        If the user pases a folder, it has to contain a 
        'metadata.txt' with minimal structure/information:
        "
        Heights
        23
        4
        3.6
        .85
        "
        containing the camera lense Height in meter of every photo in the 
        given directory


        ######

        initiates variables
        calls 'GetDir' and 'CheckDir'
        Whether the images are 'Linear' or 'wide' defines
        diffrent FOV angles and calls undistort fct if necessary
        
        #####

        Args:
            Dir (str, optional): directroy of images or path of image to be transformed. 
                                only for embedded use
                                Defaults to None. >> asks user
            Height (float, optional): height of camera in meters, for single image use
                                    only for embedded use
                                    Defaults to None. >> asks user
        """


        self.alpha = [0,0]                                          #fov camera angle
        self.InputVariable = [None, None]                           #user input for image cropping
        self.WorkingDir = os.getcwd()
        
        self.FileType = self.GetDir(Dir = Dir, Height=Height)
        self.CheckDir()

        
        
        
        
        
        if self.LenseType == 'Linear':
            
            print("The files in the directory are complete and consistent of type:\n"\
                  '\nField of View - Linear\n'\
                  "You can proceed.")
            self.alpha = [np.radians(94.1) , np.radians(87.06)]


        elif self.LenseType == 'Wide' and self.MetaStatus == "complete":
            print("The (undistorted) files in the directory are complete and consistent of type:\n"\
                  '\nField of View - Wide\n'\
                  "You can proceed.")
            self.alpha = [np.radians(97) , np.radians(81)]  
            self.Betas = [i + .09 for i in self.Betas]                            #image offset due to undistort
            #those values better for lower heights
            # self.alpha = [np.radians(98) , np.radians(81)]  
            # self.Betas = [i + .115 for i in self.Betas] 

        elif self.LenseType == 'Wide' and self.MetaStatus == "incomplete":    
            #call undistort class
            #copy metafile to undistorted folder

            print('The files in the directory are of type:\n'\
                  'Field of View - Wide\n'\
                    'Before making a projection the fisheye has to be removed.\n'\
                    "To proceed enter y/n.")
            ui_answ = input().casefold()
            while ui_answ != 'y' and ui_answ != 'n' and ui_answ != 'yes' and ui_answ != 'no':
                print('What did you say?')
                ui_answ = input().casefold()
 
            if ui_answ == 'y' or ui_answ == "yes":
                os.chdir(self.WorkingDir)
                if self.FileType == "file":
                    UndistortGopro(self.ImgPath).Undistort()
                else:
                    UndistortGopro(self.ImgDir).Undistort()
                
                shutil.copy(self.ImgDir + "//metadata.txt" , self.ImgDir + "//undistorted//metadata.txt")
                shutil.copy(self.ImgDir + "//timedata.txt" , self.ImgDir + "//undistorted//timedata.txt")
                self.ImgDir = self.ImgDir + "//undistorted"

                os.chdir(self.ImgDir)
                

            elif ui_answ == 'n' or ui_answ == 'no':
                exit('Program terminated by user.')
        
            self.alpha = [np.radians(97) , np.radians(81)]  
            self.Betas = [i + .09 for i in self.Betas]                            #image offset due to undistort
            #those values better for lower heights
            # self.alpha = [np.radians(98) , np.radians(81)]  
            # self.Betas = [i + .115 for i in self.Betas]        
        



####################        
####################    




    def Project(self):
        """
        Handles procedure of class
        whether FileType = 'file' or 'folder'
        calls GeometricCalc, Transform and FinishFile
        functions 
        """


        if self.FileType == "file":
                
            if self.LenseType == "Wide":
                self.Filename = self.name + "_undist.jpg"
                self.name =  self.name + "_undist"
                self.ImgPath = self.ImgDir + "//" + self.Filename
                
   
            self.Img = cv2.imread(self.ImgPath)         
            self.ImgDimension = [self.Img.shape[1], self.Img.shape[0]]
            self.MarkedImg = None
            self.Height = self.heights[0]
            self.Beta = self.Betas[0]
            self.GeometricCalc(self.Height, self.Beta)
            self.Transform()
            self.FinishFile()
            shutil.copy(self.ImgDir + "//metadata.txt" , self.ImgDir + "//topview//metadata.txt")
            shutil.copy(self.ImgDir + "//timedata.txt" , self.ImgDir + "//topview//timedata.txt")  





        elif self.FileType == "folder":
            i=0
            dir_content = glob.glob(f"*.jpg")
            for imges in dir_content:

                self.Filename = imges                                           #file name with ending
                self.name = imges[:len(imges)-4]                                #photo ID
                self.ImgPath = self.ImgDir + '\\' + imges                       #full path
                self.Img = cv2.imread(self.ImgPath)                         
                self.ImgDimension = [self.Img.shape[1], self.Img.shape[0]]
                self.MarkedImg = None


                self.Img = cv2.imread(self.ImgDir + '\\' + imges)
                self.Height = self.heights[i]
                self.Beta = self.Betas[i]
                self.GeometricCalc(self.Height, self.Beta)
                self.Transform()
                self.FinishFile()
                i=i+1
            shutil.copy(self.ImgDir + "//metadata.txt" , self.ImgDir + "//topview//metadata.txt")
            shutil.copy(self.ImgDir + "//timedata.txt" , self.ImgDir + "//topview//timedata.txt")         



    
####################        
####################    




    def GetDir(self, Dir=None, Height = None):

        """
        Asks for a directory and checks its existence.
        Args only relevant for embedded use of the class

        Args:
            Dir (str, optional):  directory of the 'file' or 'folder of the files to convert
                    input only relevant for embedded use
                    Defaults to None. >> asks the user
            Height (float, optional):  (list) of the camera height of the pased photo
                    only relevant for type 'file' in embedded use
                    Defaults to None. >> asks user
                    
        Returns:
            Type (str): whether the given path is 'folder' or 'file
        """
        
        
        if Dir == None:
            print('Please enter the directory or a path of an image:\n')
            input_path = input()
        else: input_path = Dir

        while True:
            if not os.path.isfile(input_path) and not os.path.isdir(input_path):
                print('ERROR: Something went wrong. Please enter the directory/path again:\n')
                input_path = input()
            elif os.path.isfile(input_path):
                print('File found.')        
                self.ImgPath = input_path 
                self.Filename = self.ImgPath.split("\\")[-1]
                self.name = self.Filename[:len(self.Filename)-4]            #photo ID
                self.ImgDir = os.path.dirname(self.ImgPath)                 #dir of file
                Type = "file"
                
                if Height is not None:
                    self.heights = [Height]
                    
                break
            elif os.path.isdir(input_path):    
                print('Directory found.')        
                self.ImgDir = input_path   
                Type = "folder"
                break
        
        
        return Type 

        
        
        
####################        
#################### 




    def CheckDir(self):
        """
        checks whether an already transformed "undistorted"
        subfolder exists and asks user
        calls 'checkmetafile' function for either chosen/existent dir
                
        Returns:
            dir_content: list of all .jpg files in the given dir
        """
        
        
        os.chdir(self.ImgDir)

        if self.FileType == "file":
            dir_content = [self.Filename]
        elif  self.FileType == "folder":
            dir_content = glob.glob(f'*.jpg')
            print('Found ' + str(len(dir_content)) + ' images')
        

        #check if 'undistorted' sub_dir already exists
        dir_folder = glob.glob('undistorted/')
        #if yes...
        if len(dir_folder) == 1 and dir_folder[0] == 'undistorted/' : 
            os.chdir(self.ImgDir + "/undistorted")
            subdir_content = glob.glob(f'*.jpg')
            print('Found ' + str(len(subdir_content)) + " images in an 'undistorted' subfolder.\n"\
                  "Do you want to proceed in the subfolder? y/n")
            
            #ask user if wants to use those already
            ui_answ = input().casefold()
            while ui_answ != 'y' and ui_answ != 'n' and ui_answ != 'yes' and ui_answ != 'no':
                print('What did you say?')
                ui_answ = input().casefold()

            if ui_answ == 'y' or ui_answ == "yes":
                self.CheckMetaFile(subdir_content)
                self.ImgDir = os.getcwd()

            elif ui_answ == 'n' or ui_answ == 'no':
                os.chdir(self.ImgDir)
                self.CheckMetaFile(dir_content)

        #if unknown folder...check for known information
        else:
            self.CheckMetaFile(dir_content)


        return dir_content




####################        
#################### 




    def CheckMetaFile(self, dir_content):
        """
        Checks necessary meta information of the pased files
        distiguishes whether
        1. height info unknown
           then looks for metafile and reads info
           or checks the metainfo in the specif. files
           if necessary
        2. height known
           read tilt and time metainfo from file
           write to .txt

        Args:
            dir_content (list): List of all .jpg files in pased dir
        """
        
        
        
        #if Height information is not already pased (directly or with dir)
        if  not hasattr(self, 'heights'):
            
            if self.FileType == 'folder':
                try:
                    meta_file = open("metadata.txt", 'r')
                except FileNotFoundError:
                    print("ERROR: The given directory does not contain a 'metadata.txt' file.\n"
                          "This is necessary for FileType = 'folder'.")
                    exit()
                
            if self.FileType == 'file':
                try:
                    meta_file = open("metadata.txt", 'r')
                except FileNotFoundError:
            
                    print("Please enter the height in meter of the camera in the given Image:")
                    h = input()
                    while True:
                        try: 
                            h = float(h)
                            break
                        except:
                            print('Please enter the float again.')
                            h = input()
                    self.heights = [h]

            
            FileLines = meta_file.readlines()
            meta_file.close()
            while True:
                try:
                    ind = FileLines.index('\n')
                    FileLines.pop(ind)
                except:
                    break
            self.heights = np.zeros(shape=(len(dir_content),))
            self.Betas = np.zeros(shape=(len(dir_content),))


            #new folder without information
            if FileLines[0].strip('\n') == 'Heights':
                
                self.MetaStatus = "incomplete"
                
                #read heights from file
                for i in range(len(dir_content)):
                    #read height data
                    try:   
                        self.heights[i] = float(FileLines[i+1])
                    except ValueError:
                        print('\nERROR: Number of images unequals number of information in metadata file.\n'\
                            'Maybe check for not deleted TEMP file. \n')
                        exit()

                #check for type and tilt angles
                TimeStamps = []
                Types = []
                for i in range(len(dir_content)):
                    Types,TimeStamps = self.ReadGoproMeta(Img=dir_content[i], Types=Types, Index = i, TimeStamps=TimeStamps)

                #check for type consistency
                if(len(set(Types)) != 1):
                    print("The files in the given directory are not consistent.\n"\
                        "There are different FOV types. Please check directory.")

                else:

                    #write to metafile lines
                    FileLines.insert(0,'Type\n')
                    FileLines.insert(1,Types[0]+"\n")

                    #write tilt angles to metafile
                    FileLines.append("Tilts\n")
                    for i in range(len(self.Betas)):
                        FileLines.append(str(self.Betas[i])+"\n")                
                
                    meta_file = open("metadata.txt", 'w') 
                    meta_file.writelines(FileLines)
                    meta_file.close()
                    #update lense type
                    self.LenseType = FileLines[1].strip('\n')
                    
                    FileLines =[]
                    FileLines.append("TimeStamps\n")
                    for i, time in enumerate(TimeStamps):
                        fname = dir_content[i]
                        FileLines.append(fname[:len(fname)-4] + "\t" + time + "\n")
                        
                    time_file = open("timedata.txt", "w")
                    time_file.writelines(FileLines)
                    time_file.close



            #known folder with information in the metafile
            elif FileLines[0].strip('\n') == 'Type':
                
                self.MetaStatus = "complete"
                #read lensetype
                try:
                    self.LenseType = FileLines[1].strip('\n')
                except ValueError:
                    print('\nERROR: Could not read Lensetype from metadata file \n')
                    exit()
                #read height
                
                for i in range(len(dir_content)):
                    #read height
                    try:
                        self.heights[i] = float(FileLines[i+3])
                    except ValueError:
                        print('\nERROR: Number of images unequals number of information in metadata file.\n'\
                                'Maybe check for not deleted TEMP file. \n')
                        exit()
                    #read height
                    try:
                        self.heights[i] = float(FileLines[i+3])
                    except ValueError:
                        print('\nERROR: Number of images unequals number of information in metadata file.\n'\
                                'Maybe check for not deleted TEMP file. \n')
                        exit()
                    #read tilts
                    try:
                        self.Betas[i] = float(FileLines[ len(dir_content)+4+i ])
                    except ValueError:
                        print('\nERROR: Number of images unequals number of information in metadata file.\n'\
                                'Maybe check for not deleted TEMP file. \n')
                        exit()
        
        
        
        
        #for known Height data initiate new metadata file
        else:
            
            
            self.Betas = [0]
            #check for type and tilt angles
            TimeStamps = []
            Types = []
            for i, file in enumerate(dir_content):
                Types,TimeStamps = self.ReadGoproMeta(Img=file, Types=Types, Index = i, TimeStamps=TimeStamps)

            FileLines = []
            #write to metafile lines
            FileLines.append('Type\n')
            FileLines.append(Types[0]+"\n")
            #update lense type
            self.LenseType = Types[0]

            FileLines.append("Heights\n")
            FileLines.append(str(self.heights) + "\n")
            #write tilt angles to metafile
            FileLines.append("Tilts\n")
            FileLines.append(str(self.Betas[0])+"\n")                
        
            meta_file = open("metadata.txt", 'w') 
            meta_file.writelines(FileLines)
            meta_file.close()  
            
            FileLines =[]
            FileLines.append("TimeStamps\n")
            for i, time in enumerate(TimeStamps):
                fname = dir_content[i]
                FileLines.append(fname[:len(fname)-4] + "\t" + time + "\n")
                
            time_file = open("timedata.txt", "w")
            time_file.writelines(FileLines)
            time_file.close
     





####################        
#################### 




    def ReadGoproMeta(self, Img, Types=None, Index=None,TimeStamps=None):
        """
        accesses exiftool meta info from given Img
        reads time stamp, tilt angle and FOV type
        stores tilt directly in self.Beta using Index
        stores FOV in lists
        stores FOV in 

        Args:
            Img (numpy.ndarray): Image to be read
            Types (list, optional): list of str defining imges by 'Linear'/'Wide'
                                   Defaults to None. >> initiates new list
            Index (int, optional): current global Index of the img. Used for insertion
                                    Defaults to None. >> 0

        Returns:
            Types: list of 'Linear'/'Wide' info of image(s) 
            TimeStamp: list of time stamps in format '%Y:%m:%d %H:%M:%S' 
        """
        
        
        if Types == None:
            Types = []
        if Index == None:
            Index = 0
        if TimeStamps == None:
            TimeStamps = []
            
        temp_file = "temp.txt"
        myCommand = 'exiftool' + " -u -j " + self.ImgDir + '\\' + Img + " > " + temp_file
        subprocess.call(myCommand, shell=True)

        temp_meta_file = open(temp_file, 'r')
  

        ## find correct line in meta file
        substring = ["GoPro", "CreateDate" , "GRAV", "FieldOfView"]
        
        
        for sub in substring:
            i = 0
            if sub == "GoPro":
                while True:
                    next_line = temp_meta_file.readline()
                    i=i+1
                    if "GoPro" in next_line:
                        break
                    elif i>20:
                        print("ERROR: There is one or more non-Gopro files in your directory.\n"\
                            "Or the metafile is damaged")
                        exit() 
            elif sub == "CreateDate":
                while True:
                    next_line = temp_meta_file.readline()
                    i=i+1
                    if sub in next_line:
                        #add tilt angle info to beta list
                        time = next_line.split('"')[3]
                        TimeStamps.append(time)
                        break  
                    elif i>40:
                        print("ERROR: There is one or more non-Gopro files in your directory.\n"\
                            "Or the metafile is damaged")
                        exit()         
            elif sub == "GRAV":
                while True:
                    next_line = temp_meta_file.readline()
                    i=i+1
                    if sub in next_line or "GoPro_GRAV" in next_line:
                        #add tilt angle info to beta list
                        coord = next_line.split('"')[3]
                        coord = np.float_(coord.split(' '))
                        self.Betas[Index] = np.arctan(coord[1]/coord[2])
                        break
            if sub == "FieldOfView":
                while True:
                    next_line = temp_meta_file.readline()
                    i=i+1
                    if sub in next_line:
                        #add type info to type list
                        Info = next_line.split('"')[3]
                        Info = Info.strip(' ')
                        Types.append(Info)
                        break
            

        temp_meta_file.close()
        os.remove(temp_file)    

        return Types, TimeStamps




####################        
#################### 


        
        
    def AskforVariable(self,variable):
        """
        asks the user where to mark/cut the image.
        saves the input parameters for the image
        saves a 'marked image' 

        Args:
            variable (str): 'x' or 'y' coordinate axe of interest
        """
        
        
        ui_answ = 'n'
        while ui_answ == "n":
            
            
            if variable == 'x':
                print("\nWhere do you want to cut the horizon?\n"\
                    "Enter float a, with dim_x / a.")
                x_factor = input()
                while True:
                    try: 
                        x_factor = float(x_factor)
                        break
                    except:
                        print('Please enter the float again.')
                        x_factor = input()
            

                #start for y in middle if not yet defined
                if self.InputVariable[1] == None:
                    y_in = .5 *self.ImgDimension[0]
                else:
                    y_in = self.InputVariable[1]
                
                x_in = self.ImgDimension[0]/x_factor
                self.user_input_points = [[int(x_in),int(y_in)], [self.ImgDimension[0]-int(x_in),int(y_in)]]
                
                #show user current input on image
                m_img = copy.deepcopy(self.Img)
                for i in [0,1]:
                    m_img = cv2.drawMarker(m_img, tuple(self.user_input_points[i]), color = (255,0,0),markerType=cv2.MARKER_SQUARE, thickness=4, markerSize = 50)
                m_img = cv2.line(m_img, self.user_input_points[0], self.user_input_points[1], color = (255,0,0), thickness=3)    
                
                self.ShowImg(m_img, "Marked Points")
                


            elif variable == 'y':
                print("\nWhere do you want to cut vertically?\n"\
                    "Enter float a, with dim_y / a.")
                y_factor = input()
                while True:
                    try: 
                        y_factor = float(y_factor)
                        break
                    except:
                        print('Please enter the float again.')
                        y_factor = input()
                

                x_in = self.InputVariable[0]
                y_in = self.ImgDimension[1] - self.ImgDimension[1]/y_factor
                self.user_input_points = [[int(x_in),int(y_in)], [self.ImgDimension[0]-int(x_in),int(y_in)]]
            
                #show user current input on image
                m_img = copy.deepcopy(self.Img)
                for i in [0,1]:
                    m_img = cv2.drawMarker(m_img, tuple(self.user_input_points[i]), color = (0,255,0),markerType=cv2.MARKER_SQUARE, thickness=4, markerSize = 50)
                m_img = cv2.line(m_img, self.user_input_points[0], self.user_input_points[1], color = (0,255,0), thickness=3)    
                self.ShowImg(m_img, "Marked Points")
            
            
            
            
            print("\nGood so? Enter: y\n"
                    "Or do you want to adjust? Enter: n")
            ui_answ = input().casefold()
            while ui_answ != 'y' and ui_answ != 'n' and ui_answ != 'yes' and ui_answ != 'no':
                print('What did you say?')
                ui_answ = input().casefold()
            
            
        
        if variable == 'x':
            self.InputVariable[0] = x_in
        elif variable == 'y':
            self.InputVariable[1] = y_in
        self.MarkedIm = m_img    
        self.Save(m_img, package='cv2', folder='marked')
        cv2.destroyAllWindows()
                  
    
    
    
####################        
####################  
    
    
    
    
    def ShowImg(self, img, window_name, final=None):
        """
        shows an image in a pop-up window

        Args:
            img (numpy.ndarray): the image to show
            window_name (str): name of the pop-up window
            final (str, optional): 'projected' says that its the projected.
                                    closed with <enter> 
                                    Defaults to None. >> simple show
        """
        
        
        cv2.namedWindow(window_name,  cv2.WINDOW_KEEPRATIO)
        cv2.imshow(window_name, img)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        #cv2.setWindowProperty(window_name, cv2.WINDOW_KEEPRATIO)
        if final == 'projected':
            cv2.waitKey(2) 
            Input = input()
            if Input == '':
                cv2.destroyAllWindows() 
        else:
            cv2.waitKey(100)
    
    


####################        
#################### 




    def AskVariables(self):
        """
        calls "askvariable" function
        gives option to repeat/adjust choices
        """
        
        
        Input = None
        while True:
            
            if Input == None:
                self.AskforVariable('x')
                self.AskforVariable('y')
            elif Input == 'y':
                self.AskforVariable('y')
            elif Input == 'x':
                self.AskforVariable('x')
            elif Input == '':
                break
            
            print("\nAll good? Enter: Hit Enter\n"
                    "Or do you want to adjust a variable? Enter: x or y")
            Input = input().casefold()
            while Input != 'y' and Input != 'x' and Input != '':
                print('What did you say?')
                Input = input().casefold()
            
            
      
            
####################        
####################                 




    def GeometricCalc(self, height, beta):
        """
        does all the geometric calculations necessary for the transformation

        Args:
            height (float): height in meters of the camera lense
            beta (float): tilt angle of the camera in radians
        """
        
        
        
        self.AskVariables()
        

        ## geometric calculations
        alph_hh = 0.5*self.alpha[0]                          
        alph_hv = 0.5*self.alpha[1]                          
        d_i = height / np.cos(beta-alph_hv)
        d_id = np.cos(alph_hv) * d_i
        d_hi = np.tan(beta-alph_hv) * height
        y_wh = d_id*np.tan(alph_hv) 
                                                          
        #reverse engineered distance          
        y_ci_r = self.InputVariable[1] * 2*y_wh / self.ImgDimension[1]
        zeta = np.arctan( (y_wh - y_ci_r) / d_id )
        gam = 0.5*np.pi - zeta - beta
        
        d_c = height / np.tan(gam)                  
        d_ct =height / np.sin(gam)
        d_cd = np.cos(zeta) * d_ct 
        w_ii = 2* np.tan(alph_hh) * d_id
        w_ic = 2* np.tan(alph_hh) * d_cd
            
        #reverse engineered width
        x_ci_r = self.InputVariable[0] * w_ic/self.ImgDimension[0]  
        w_ii_r = w_ic - 2* x_ci_r
        #alph_hh_r = np.arctan( w_ii_r / 2*h)
        
        new_x_dim = self.ImgDimension[0] * w_ii_r / w_ii
        self.X_PixelExtent = .5*(new_x_dim-self.ImgDimension[0])

        self.Py = (self.ImgDimension[0] * (d_c - d_hi))  /  w_ii
        

        self.GeomVariables = {"d_c": d_c , "d_hi":d_hi, "w_ii":w_ii, "w_ii_r" : w_ii_r}
        
    
    
    
####################        
####################    
    
    
    
    
    def SizeCheck(self):
        """
        checks if calculated pixel size exceeds memory 
        """


        while True:    
            if self.ImgDimension[0] + 2*self.X_PixelExtent < 178956970 and self.Py < 178956970: break
            else:
                print('The calculated pixel number exceeds max of 178956970 pixels in at least one dimension.\n' \
                    'Please define your varibles again.')

                self.GeometricCalc(self.Height, self.Beta)   
        
 
  
        
####################        
####################         
        
        
           
        
    def ExtendImg(self):
        """
        extend the image size if necessary for the projection
        used to broaden the possible viewable range in the image

        Returns:
            self.Img: the extended image. only for embedded/single use
        """
        
        
        img_ext = Image.open(self.ImgPath)
    
        img_ext = img_ext.crop( (-self.X_PixelExtent,0,self.ImgDimension[0]+self.X_PixelExtent,self.ImgDimension[1]) )  

        if self.X_PixelExtent > 0:
            draw = ImageDraw.Draw(img_ext)
            draw.rectangle( (0,0,self.X_PixelExtent,self.ImgDimension[1]), fill="green" )
            draw.rectangle( (self.ImgDimension[0]+self.X_PixelExtent  ,  0 ,  self.ImgDimension[0]+2*self.X_PixelExtent  ,  self.ImgDimension[1]), fill="green" )
            del draw
        self.temp_file = self.ImgDir + '\\'  + self.name + '_temp.jpg'
        img_ext.save(self.temp_file, "JPEG", quality=75)
  
        self.Img = cv2.imread(self.temp_file)
        self.ImgDimension = [self.Img.shape[1], self.Img.shape[0]]

        return self.Img
        
        
    
        
####################        
####################         
        
        
        
            
    def Transform(self):
        """
        transformes the given image with the given information
        checks whether img size exceeds
        extends the original image if necessary

        Returns:
            self.ProjImg: The transformed image. Return only for single or embedded use
        """
        
        

        self.SizeCheck()
        self.ExtendImg()
        
        ## new image points in photo and projections
        img_vert_in = [[int(self.InputVariable[0]+self.X_PixelExtent) , int(self.InputVariable[1])]  , [self.ImgDimension[0]-int(self.InputVariable[0]+self.X_PixelExtent),int(self.InputVariable[1])]  ,  [0, self.ImgDimension[1]]  ,   [self.ImgDimension[0], self.ImgDimension[1]]]
        img_vert_out = [[0,0], [self.ImgDimension[0],0],[0,int(self.Py)],[self.ImgDimension[0],int(self.Py)]]

        ## opencv projection
        T = cv2.getPerspectiveTransform(np.float32(img_vert_in),np.float32(img_vert_out))
        self.ProjImg = cv2.warpPerspective(self.Img , T , (self.ImgDimension[0],int(self.Py)))       
        
        
        self.ShowImg(self.ProjImg, 'Topview' + self.name, final = 'projected')
        
        return self.ProjImg
            
    
    
    
####################        
####################     
    
    
    
    
    def Save(self, Img, package: str,  folder=None, Dir=None):
        """
        saves image of given type (package) in given dir
        in the given folder

        Args:
            Img (numpy.ndarray): image to be stored
            package (str): 'cv2' or 'mpl' = matplotlib image. 
            folder (str, optional): name of the folder_name = subdir of previously given path. 
                                Defaults to None >> no subfolder
            Dir (str, optional): dir where to be stored. 
                                Defaults to None. >> self.ImgDir
        """
        
        
        if Dir == None:
            Dir = self.ImgDir
        if folder == None:
            folder = ""
        
        save_dir = os.path.join(Dir ,folder)
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        if package == 'cv2':
            cv2.imwrite(save_dir + "/" + self.name + "_" + folder + ".jpg" ,Img)
        elif package == 'mpl':
            save_path = save_dir + "/" + self.name + "_" + folder + "jpg"
            Img.savefig(save_path)
        
     
        
        
####################        
####################        
      
      
        
        
    def FinishFile (self , Img = None,  Dir = None, save = None):
        """
        calls terminating tasks to save (or not) all relevant data of the transformed file

        Args:
            Img (numpy.ndarray, optional): the image to be saved/finished/closed.... 
                                   Defaults to None. >> self.ProjImg
            Dir (str, optional): dir where to be stored. 
                                   Defaults to None >> self.ImgDir
            save (str, optional): ='save' >> saves the image, the scaled version, 
                                    pixelsize of image; destroys windows
                                  ='without >> destroys windows
                                  Defaults to None. >> asks the user
        """
        
        
        if Img == None:
            Img = self.ProjImg
        if Dir == None:
            Dir = self.ImgDir
        if save == None:
            print("Do you want to save the image? y/n")
            ui_answ = input().casefold()
            while ui_answ != 'y' and ui_answ != 'n' and ui_answ != 'yes' and ui_answ != 'no':
                print('What did you say?')
                ui_answ = input().casefold()
            if ui_answ == 'y' or ui_answ == "yes":
                save = 'save'
            elif ui_answ == 'n' or ui_answ == 'no':
                save = 'without'



        if save == 'save':
            print('\nFinishing and saving. This may take a few seconds......')
            print('... Projected Image ....')
            self.Save(Img,'cv2', folder='topview', Dir=Dir)
            print('... Image with scales ....')
            self.SaveScaleimg(Dir)
            print('... Save Meta data of Image ....')
            self.SavePixelsize()
            print('Done Saving.')
            cv2.destroyAllWindows()   
    
        elif save == 'without':
            cv2.destroyAllWindows()   
       
        
 
        
####################        
####################        
        
        
    
        
    def SaveScaleimg(self, Dir):
        """
        creates transformed image with dimension scales at 
        the image's sides
        calles 'Save' function
        """
        
        
        plt.ioff()                                                                      #interactive off
        fig, ax = plt.subplots(figsize=( self.ImgDimension[0]/100, self.Py/100))
        #fig, ax = plt.subplots()
        ax.imshow(self.ProjImg, extent=[0,self.GeomVariables['w_ii_r'],0,(self.GeomVariables['d_c'] - self.GeomVariables['d_hi'])])                                #ax range
        ax.tick_params(axis='both', which='both', labelsize=80, width=10, length=30)    #ax setup
        plt.setp(ax.spines.values(), linewidth=15)                                      #ax number spines setup
        fig.tight_layout()
        
        self.Save(fig, 'mpl', folder='_topview_scale', Dir=Dir)
   
            
        
        
####################        
####################         
        
        
      
        
    def SavePixelsize(self):
        """
        save generel pixel size in meter of image in extra txt file
        in file dir
        """
        
        
        ##  save pixelsize
        x_pix_size = self.GeomVariables['w_ii'] /  (self.ImgDimension[0]-2* self.X_PixelExtent)  #pixel size in meter
        y_pix_size = (self.GeomVariables['d_c'] - self.GeomVariables['d_hi']) / self.Py
        size_Outfile = self.ImgDir + "/" +'topview/' + self.name + "_size.txt"
        size_file = open(size_Outfile, 'w')
        
        size_file.writelines([str(x_pix_size*y_pix_size)+'\n', str(x_pix_size)+'\n', str(y_pix_size)])
        size_file.close()


        os.remove(self.temp_file)
        
        
    