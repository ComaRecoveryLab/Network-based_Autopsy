#!/usr/bin/env python3

import os, subprocess, argparse

"""
Register Parcellations to Individual Subject (Python Version)
Original code blocks credited to:
https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/project_to_individual


The following version accomplishes the same steps embedded within a Python enviornment. This code is configured for this particular project which calls for the 1000 Parcellation/7 Network version of the atlas. 

Author: Holly J. Freeman -- February 7, 2023
"""

#------------------- Functions -------------------
def parse_args (): 

    parser = argparse.ArgumentParser(description="Registers Schaefer 2018 surface based parcellations to individual subject.")
    #------------------- Required Arguments -------------------
    parser.add_argument('-s', '--subject_directory', help="Directory containing FreeSurfer reconed subjects.", type=str, required=True)
    parser.add_argument('-f', '--fs_average', help="Full path to fsaverage subject.", type=str, required=True)
    parser.add_argument('-a', '--atlas_directory', help="Full path to CBIG directory.", type=str, required=True)
    parser.add_argument('-l', '--lut', help="Look Up Table associated with atlas.", type=str, required=True)


def callSub (run_command):
    """
    Main function used to export commands to interactive shell.
    """

    with subprocess.Popen([run_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
        for line in process.stdout:
            print(line.decode('utf8'))

    subprocess.call([run_command], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def surfReg (subject, subject_dir): 
    """
    Formats FreeSurfer mri_surf2surf command. 
    """

    for hemi in ('lh', 'rh'): 
        print("Processing HEMI %s for %s" % (hemi, subject))
        os.chdir(SUBJECTS_DIR)

        annotFile=os.path.join(CBIG_CODE_DIR, ("stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/FreeSurfer5.3/%s/label/%s.Schaefer2018_1000Parcels_7Networks_order.annot" % (FSA, hemi)))  
        print(annotFile)

        targVal = os.path.join(subject_dir, ("label/%s.Schaefer2018_1000Parcels_7Networks_order.annot" % hemi))
        print(targVal)

        surfCmd = "mri_surf2surf --hemi %s --srcsubject %s --trgsubject %s --sval-annot %s --tval %s" % (hemi, FSA, subject, annotFile, targVal)
        print(">>>", surfCmd)
        callSub(surfCmd)

def parc2seg (subject, subject_directory):
    """
    Formats FreeSurfer mri_aparc2aseg command.
    """

    parc2segCmd = "mri_aparc2aseg --s %s --o %s/mri/%s_Schaefer2018_1000Parcels_7Networks.mgz --annot Schaefer2018_1000Parcels_7Networks_order" % (subject, subject_directory, subject)
    print(">>>", parc2segCmd)
    callSub(parc2segCmd)


def annot2label (subject, output_directory):
    """
    Formats FreeSurfer mri_annotation2label command.
    """

    for hemi in ('lh', 'rh'): 
        print("Processing HEMI %s for %s" % (hemi, subject))

        annot2labelCmd = "mri_annotation2label --subject %s --hemi %s --annotation Schaefer2018_1000Parcels_7Networks_order --outdir %s --ctab %s/Schaefer2018_%s_LUT.txt" % (subject, hemi, output_directory, output_directory, hemi)

        print(">>>", annot2labelCmd)
        callSub(annot2labelCmd)

def main(): 
    #------------------- Argument Handling -------------------
    args = parse_args()
    SUBJECTS_DIR = args.subject_directory
    CBIG_CODE_DIR =  args.atlas_directory
    FSA = args.fs_average
    f_LUT = args.lut

    #------------------- Main Functions -------------------
    for subj in os.listdir(SUBJECTS_DIR):

        print("subj")
        if subj != "fsaverage6":

            print("PROCESSING SUBJECT: %s" % subj)

            subject = subj
            subDir = os.path.join(SUBJECTS_DIR, subj)
            outDir = os.path.join(subDir, "Schaefer2018_labels")

            if not os.path.exists(outDir):
                print("OUT DIR %s -- Does not exist" % outDir)
                os.makedirs(outDir)


            print("Placing copy of Yeo Atlas LUT in %s" % subDir)


            symlinkCmd = "os.symlink(%s, os.path.join(%s,Schaefer2018_1000Parcels_7Networks_order_LUT.txt" %    (f_LUT, subDir)
            print(symlinkCmd)
            callSub(symlinkCmd)

            surfReg(subject, subDir)

            parc2seg(subject, subDir)

            annot2label(subject, outDir)

            print(" ")

if __name__ == '__main__':
    main()
