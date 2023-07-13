#!/usr/bin/env python3

import os, sys, argparse, datetime, torch, subprocess #$# sys and os are unused, maybe want to use subprocess to run commands?
from py_console import console, textColor

"""
Probabalistic Tractography Wrapper

Preprocesses data and formats command call to FSL probtrackx2_gpu (https://users.fmrib.ox.ac.uk/~moisesf/Probtrackx_GPU/Installation.html), with option to run on CPU. 

Provided an input directory containing all ROIs, this script will: 
- Create network matrix with full path to ROIs
- Copy geometry header from diffusion mask generated by bedpostx (optional)


Usage: 
conda create --name <env> --file probtrackx_requirements.txt
./run,DAN_probtrackx2_gpu.py -i /path/to/ROI/directory -s subject -o /path/to/output/directory -b /path/to/bedpostx/directory 

optional: -n /path/to/ROI/text/document --no_geometry_fix <skips geometry steps> --cpu <runs program on CPU> 

Author: Holly J. Freeman -- 07.27.2022
"""

#------------------- Functions -------------------
def parse_args ():
    """
    Required Arguements: 
    -i --input directory        : Directory containing all ROI's to process. 
    -s --subject                : Subject ID
    -o --output_directory       : Directory to place outputs. 
    -b --bedpost_directory      : Directory containing outputs from bedpostx analyses.

    Optional: 
    -n --newtork                : Skips generating ROI list for network analyses if you would rather provide your own. 
    -g --no_geometry_fix        : Skips copying diffusion mask geometry to ROI header. 
    -c --cpu                    : Runs program on CPU. Default is GPU.
    """

    parser = argparse.ArgumentParser(description="Prepares data to run probibalistic tractography. Checks ROI inputs for matching geometry.")
    #------------------- Required Arguments -------------------
    parser.add_argument('-i','--input_directory', help="Directory containing all ROIs, please make sure all ROIs are located in this location otherwise they will not be processed.", type=str, required=True)
    parser.add_argument('-s', '--subject', help="Subject ID", type=str, required=True)
    parser.add_argument('-o','--output_directory', help="Full directory path to place outputs.", type=str, required=True)
    parser.add_argument('-b','--bedpost_directory', help="Full directory path to bedpost directory", type=str, required=True)
    #------------------- Optional Arguments -------------------
    parser.add_argument('-n', '--network', help="Process subset of ROIs", type=str, required=False)
    parser.add_argument('-g', '--no_geometry_fix', help="Skips copying diffusion mask geometry to ROI header", action='store_true', required=False)
    parser.add_argument('-c', '--cpu', help="Forces CPU usage. Default is GPU.", action='store_true', required=False)
    return parser.parse_args()

def set_device (): 
    """
    By default, will check to see if GPU device is available on machine and set CUDA packages and LD Library Paths. If no device is found, CPU will be used and returned to main script instead. 
    """
    if torch.cuda.is_available():
        os.environ["CUDA_HOME"]="/usr/pubsw/packages/CUDA/11.6/"
        os.environ["CUDA_VISIBLE_DEVICES"]="0"
        os.environ["LD_LIBRARY_PATH"]="/usr/pubsw/packages/CUDA/11.6/lib64:/usr/pubsw/packages/CUDA/11.6/extras/CUPTI/lib64:/usr/pubsw/packages/CUDA/9.0/lib64:/usr/pubsw/packages/CUDA/9.1/lib64"
        device = torch.device("cuda")
        cuda = True

    else:
        device = torch.device("cpu")
    
    return(device, cuda)

def get_roi_list (roi_path, subject, date):
    """
    Using the input directory, will check for nifti file extensions (ending in .nii) and place them all into a list and text file to pass to probtrackx network call. 
    """

    rois = []
    for item in [os.path.join(roi_path, file) for file in os.listdir(roi_path)]:
        if item.endswith(".nii"):
            rois.append(item)

    network_file_name = subject + "_network_" + date + ".txt"
    network_file = os.path.join(roi_path, network_file_name)

    with open(network_file, 'w') as f:
        for item in rois:
            f.write("%s\n" % item)

    return(rois, network_file)

def set_geometry (bedpost_directory, network_file):
    """
    Copies diffusion mask geometry header and applies it to all ROIs in list. This is to prevent possible mismatched matrices that is often caused by the geometry headers not matching. This does not change or alter the data besides updating the header.
    """

    mask = os.path.join(bedpost_directory, "nodif_brain_mask.nii.gz")

    if os.path.exists(mask) == True and os.path.exists(network_file) == True: 
        print("Diffusion Mask Volume == ", mask)
        print("ROI Network List == ", network_file)

        roi = open(network_file, 'r')
        rois = roi.readlines()

        for line in rois: 
            print("Working on", line)
            geometryCommand = "fslcpgeom " + mask + " " + line
            os.system(geometryCommand)

def build_probtrackx_command(output_directory, bedpost_directory, network_matrix, cuda, device):
    """
    Using default flags and settings, generates probtrackx2 command and runs either the cpu or gpu version depending on your device configuration. 
    """

    if cuda == True: 
        probtrackx_version="/usr/pubsw/packages/fsl/6.0.5.1/bin/probtrackx2_gpu"
    else:
        probtrackx_version="/usr/pubsw/packages/fsl/6.0.5.1/bin/probtrackx2"

    probtrackxCommand= probtrackx_version + " -x " + network_matrix + " -s " + os.path.join(bedpost_directory, "merged") + " -m " + os.path.join(bedpost_directory, "nodif_brain_mask") + " --dir=" + output_directory + " -l -c 0.2 -S 2000 -P 5000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --steplength=0.25 --forcedir --opd --network -V 1"
    print(probtrackxCommand)
    os.system(probtrackxCommand) #$# worth having a flag to optionally run this, or using subprocess.POPEN to capture output?

def main(): 
    #------------------- Set Date and Time-------------------
    currentDate = datetime.date.today()
    currentDate = currentDate.strftime("%Y%m%d")
    currentDate = str(currentDate)
    now = datetime.datetime.now()
    

    #------------------- Argument Handling -------------------
    args = parse_args()
    input_directory = args.input_directory
    subject = args.subject
    bedpost_directory = args.bedpost_directory
    output_directory = args.output_directory
    directory_name = subject + ".probtrackx.network." + currentDate
    output_directory = os.path.join(output_directory, directory_name)

    if args.network is not None: 
        network_file = args.network
    else: 
        network_file = None

    if args.no_geometry_fix is not False: 
        skip_geometry = args.no_geometry_fix
    else: 
        skip_geometry = False

    if args.cpu is True: 
        use_gpu = False 
    else: 
        use_gpu = True


    #------------------- Device Configuration -------------------
    #$# this is all handled in set_device(), I'd just roll the check for 
    # use_gpu into the set_device() call and make this one line calling set_device(use_gpu)
    print("#------------------- Device Configuration -------------------")
    if use_gpu == True: 
        device, cuda = set_device()
        console.success("Using", device, "device.", showTime=False)
    else: 
        device = torch.device("cpu")
        console.success("Using", device, "device.", showTime=False)
        cuda = False
    print(" ")


    #------------------- Set Up Enviornment -------------------
    print("------------------- Setting Up Enviornment -------------------")
    os.environ["FSLDIR"] = "/usr/pubsw/packages/fsl/6.0.5.1"

    print("FSL DIRECTORY --> ", os.environ.get("FSLDIR"))
    print("CUDA HOME --> ", os.environ.get("CUDA_HOME"))
    print("LD LIBRARY PATH --> ", os.environ.get("LD_LIBRARY_PATH"))
    print("CUDA VISIBLE DEVICES --> ", os.environ.get("CUDA_VISIBLE_DEVICES"))
    print(" ")


    #------------------- Set Up Output Directory -------------------
    isExist = os.path.exists(output_directory)

    if not isExist: 
        print("Creating output directory ->", output_directory)
        os.mkdir(output_directory)
    else:
        print("Output Directory =", output_directory)


    #------------------- Main Function Calls -------------------
    print()
    print("------------------- Begin Processing ", now,  "-------------------")

    if network_file is not None: 
        print("Skip ROI List Generation,", network_file, "provided as ROI list.")
    else: 
        print("Generating ROI Network File")
        rois, network_file = get_roi_list(input_directory, subject, currentDate)

    if skip_geometry == True: 
        print("Skip Geometry has been set - will NOT copy geometry from diffusion mask to ROIs.")
    else: 
        print("Copying Diffusion Mask Geometry to ROI")
        set_geometry(bedpost_directory, network_file)
    
    print("Running Probtrackx2")
    build_probtrackx_command(output_directory, bedpost_directory, network_file, cuda, device)

    print("Done!")

if __name__ == '__main__':
    main()