import os
import subprocess
import glob

def main():        
    dcm_root = "image/dcm"
    dcm_dirs = glob.glob(f"{dcm_root}/*/*")
    save_dir = "image/nifti"

    len(dcm_dirs)
    # preprocess for "pre" data
    for dcm_dir in dcm_dirs:
        input_dir = dcm_dir
        output_dir = save_dir + dcm_dir.replace(dcm_root, "")
        os.makedirs(output_dir, exist_ok=True)
        file_name = "ct"
        subprocess.run(["dcm2niix", "-z", "y", "-f", file_name, "-o", output_dir, input_dir])
        print("Done!", output_dir)

if __name__ == '__main__':
    main()
