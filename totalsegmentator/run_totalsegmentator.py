import os
import glob
import json
import subprocess
import numpy as np
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator
import matplotlib.pyplot as plt
import multiprocessing

def main():
    # 対象となるディレクトリのリストを作成
    study_dirs = [d for d in glob.glob("image/nifti/*") if not os.path.basename(d).startswith(".")]
    study_dirs = [d for d in study_dirs if not d.endswith("_unet")]
    study_dirs = [d for d in study_dirs if not d.endswith("_swinunetr")]
    study_dirs = [d for d in study_dirs if not d.endswith("_ts")]
    study_dirs.sort()

    for study_dir in study_dirs:
        # ct.nii.gzファイルを再帰的に検索
        series = glob.glob(os.path.join(study_dir, "**", "ct.nii.gz"), recursive=True)
        for one_series in series:
            # 同名のJSONファイルを参照
            json_file = one_series.replace(".nii.gz", ".json")
            if not os.path.exists(json_file):
                print(f"JSONファイル {json_file} が見つからないため、{one_series} はスキップします。")
                continue

            with open(json_file, "r") as f:
                meta = json.load(f)
            image_type = meta.get("ImageType", [])
            # ImageTypeが ["Original", "PRIMARY", "AXIAL"] なら処理を実行する
            if image_type != ["ORIGINAL", "PRIMARY", "AXIAL"]:
                print(f"{one_series} はImageTypeが {image_type} のため、処理をスキップします。")
                continue

            # 保存先ディレクトリの作成
            save_dir = os.path.join(study_dir, os.path.basename(os.path.dirname(one_series)) + "_ts")
            os.makedirs(save_dir, exist_ok=True)

            # save_dir配下にすでにall_labels.nii.gzが存在する場合はスキップ
            combined_labels_files = glob.glob(os.path.join(save_dir, '**', 'all_labels.nii.gz'), recursive=True)
            if combined_labels_files:
                print(f"{save_dir} には既にall_labels.nii.gzが存在するため、スキップします。")
                continue

            savepath = os.path.join(save_dir, "all_labels.nii.gz")
            input_img = nib.load(one_series)
            output_img = totalsegmentator(input_img)
            nib.save(output_img, savepath)
            print(f"Saved {savepath}")
        
            

    
def modify_label():
    all_label_paths = glob.glob('image/nifti/*/*_ts/all_labels.nii.gz', recursive=True)

    # suprem map
    class_map_abdomenatlas_1_0 = {
        1: "aorta",
        2: "gall_bladder",
        3: "kidney_left",
        4: "kidney_right",
        5: "liver",
        6: "pancreas",
        7: "postcava",
        8: "spleen",
        9: "stomach",
        }

    class_map_abdomenatlas_1_0_for_ts = {
        8: "aorta",
        4: "gall_bladder",
        3: "kidney_left",
        2: "kidney_right",
        6: "liver",
        11: "pancreas",
        9: "postcava",
        1: "spleen",
        7: "stomach",
        30: "kidney_cyst_left",
        20: "kidney_cyst_right",
        }

    # totalsegmentator map
    class_map_totalsegmentator = {
        52: "aorta",
        4: "gall_bladder",
        3: "kidney_left",
        2: "kidney_right",
        5: "liver",
        7: "pancreas",
        63: "postcava", # inferior vena cava
        1: "spleen",
        6: "stomach",
        23:	"kidney_cyst_left",
        24:	"kidney_cyst_right"
    }

    # Reverse map for class_map_totalsegmentator to abdomenatlas_1_0
    totalsegmentator_to_abdomenatlas = {v: k for k, v in class_map_totalsegmentator.items()}
    abdomenatlas_to_new_labels = {v: k for k, v in class_map_abdomenatlas_1_0_for_ts.items()}
    for filepath in all_label_paths:
            
        # Load the prediction NIfTI file    
        pred_img = nib.load(filepath)
        pred_data = pred_img.get_fdata()

        # Create an empty array for the new labels
        new_pred_data = np.zeros_like(pred_data)

        # Apply the mapping
        for total_label, anatomy in class_map_totalsegmentator.items():
            if anatomy in abdomenatlas_to_new_labels:        
                new_label = abdomenatlas_to_new_labels[anatomy]
                new_pred_data[pred_data == total_label] = new_label
                
        # Merge kidney cysts into kidneys
        # kidney_cyst_left (23) -> kidney_left (3)
        new_pred_data[new_pred_data == abdomenatlas_to_new_labels["kidney_cyst_left"]] = abdomenatlas_to_new_labels["kidney_left"]

        # kidney_cyst_right (24) -> kidney_right (4)
        new_pred_data[new_pred_data == abdomenatlas_to_new_labels["kidney_cyst_right"]] = abdomenatlas_to_new_labels["kidney_right"]

        # Save the transformed prediction as a new NIfTI file
        new_pred_data = new_pred_data.astype(int) # Convert to integer
        new_pred_img = nib.Nifti1Image(new_pred_data, pred_img.affine, pred_img.header)
        
        new_pred_file = os.path.join(os.path.dirname(filepath), "combined_labels.nii.gz")
        nib.save(new_pred_img, new_pred_file)

        print(f"Transformed prediction saved to {new_pred_file}")
    
if __name__ == '__main__':
    multiprocessing.freeze_support()  # Windowsで必要な場合
    main()
    modify_label()