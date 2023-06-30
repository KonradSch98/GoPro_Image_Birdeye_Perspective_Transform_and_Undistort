# GoPro_Image_Birdeye_Perspective_Transform_and_Undistort
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


_Class to calculate landscape geometrics, transform image to birdeye perspective and undistort fisheye distortion if necessary._

*Vorläufe Variante.....*
This class gives an (interactive) package to project GoPro images into BirdEye view. 
The 'calibrationdata.npz' file is currently calibrated for GoPro Hero 11 black.



Can deal with either single file and folder of files 

###Handles 
- directory use-request
- error handling
- type and metadata search/reading
- geometric calculations of the photographed landscape
- the projection
- FishEye undistort algorithm of the WIDE Lense if necessary


###Requirement
If the user passes a folder, it has to contain a 
'metadata.txt' with _minimal_ structure/information:
"
Heights
23
4
3.6
.85
"
containing the camera lens Height in meters of every photo in the 
given directory. An entirely written example file can also be found here.


##ToDo
- finishfile()_fct on request >> restructure for embedded use (pass info in init)
- interactive mode 'on/'off' user_choice >> for embedded or direct use
- refine wide-lens calibration offsez
