import os
import subprocess
import nibabel as nib
import numpy as np
import glob
import monai
import urllib.request
import json
import tempfile
import shutil

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    urllib.request.urlretrieve(url, dest_path)
    print("Download completed.")

def download_weights():
    download_dir = "suprem/direct_inference/pretrained_checkpoints"
    os.makedirs(download_dir, exist_ok=True)

    files = [
        (
            "https://huggingface.co/MrGiovanni/SuPreM/resolve/main/supervised_suprem_swinunetr_2100.pth?download=true",
            os.path.join(download_dir, "supervised_suprem_swinunetr_2100.pth")
        ),
        (
            "https://huggingface.co/MrGiovanni/SuPreM/resolve/main/supervised_suprem_unet_2100.pth?download=true",
            os.path.join(download_dir, "supervised_suprem_unet_2100.pth")
        )
    ]
    
    for url, dest in files:
        if not os.path.exists(dest):
            download_file(url, dest)
        else:
            print(f"{dest} already exists. Skipping download.")

def create_inference_temp_dir(target_series_dirs):
    """
    指定された各シリーズディレクトリへのシンボリックリンクを含む一時ディレクトリを作成し、そのパスを返す。
    """
    temp_dir = tempfile.mkdtemp(prefix="inference_")
    for series_dir in target_series_dirs:
        link_name = os.path.join(temp_dir, os.path.basename(series_dir))
        os.symlink(os.path.abspath(series_dir), link_name)
    return temp_dir

def main(backbone):
    # 対象となるディレクトリのリストを作成（不要なサフィックスは除外）
    study_dirs = [d for d in glob.glob("image/nifti/*") if not os.path.basename(d).startswith(".")]
    study_dirs = [d for d in study_dirs if not d.endswith("_unet")]
    study_dirs = [d for d in study_dirs if not d.endswith("_swinunetr")]
    study_dirs = [d for d in study_dirs if not d.endswith("_ts")]
    study_dirs.sort()

    # 使用する重みファイルのパスを選択
    if backbone == "unet":
        pretrainpath = "suprem/direct_inference/pretrained_checkpoints/supervised_suprem_unet_2100.pth"
    elif backbone == "swinunetr":
        pretrainpath = "suprem/direct_inference/pretrained_checkpoints/supervised_suprem_swinunetr_2100.pth"
    else:
        print("Unknown backbone")
        return

    # 各 study_dir ごとに処理
    for study_dir in study_dirs:
        # 対象のシリーズ（ct.nii.gz が存在し、かつ JSON の条件を満たすディレクトリ）のリストを収集
        target_series_dirs = []
        series_paths = glob.glob(os.path.join(study_dir, "**", "ct.nii.gz"), recursive=True)
        for one_series in series_paths:
            json_file = one_series.replace(".nii.gz", ".json")
            if not os.path.exists(json_file):
                print(f"JSONファイル {json_file} が見つからないため、{one_series} はスキップします。")
                continue

            with open(json_file, "r") as f:
                meta = json.load(f)
            image_type = meta.get("ImageType", [])
            # ["ORIGINAL", "PRIMARY", "AXIAL"] を処理する条件とした。
            if image_type != ["ORIGINAL", "PRIMARY", "AXIAL"]:
                print(f"{one_series} はImageTypeが {image_type} のため、スキップします。")
                continue

            target_series_dirs.append(os.path.dirname(one_series))
        
        if not target_series_dirs:
            print(f"{study_dir} には有効なシリーズが見つかりません。")
            continue

        # 一時ディレクトリを作成（対象シリーズのみのシンボリックリンクを配置）
        temp_data_root = create_inference_temp_dir(target_series_dirs)
        # 一時的な保存先ディレクトリを作成
        temp_save_dir = tempfile.mkdtemp(prefix="inference_save_")
        
        command = [
            "python", "-W", "ignore", "suprem/direct_inference/inference.py",
            "--save_dir", temp_save_dir,
            "--checkpoint", pretrainpath,
            "--data_root_path", temp_data_root,
            "--backbone", backbone,
            "--store_result", "--suprem"
        ]
        
        print(f"Running inference for {study_dir} with backbone {backbone}...")
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)
        
        # 結果を最終保存先に移動
        # 各対象シリーズ毎に、最終保存先は
        # os.path.join(study_dir, basename(series_dir) + f"_{backbone}")
        for series_dir in target_series_dirs:
            final_dir = os.path.join(study_dir, os.path.basename(series_dir) + f"_{backbone}")
            # temp_save_dir 内に該当する結果フォルダがあれば移動
            src = os.path.join(temp_save_dir, os.path.basename(series_dir))
            if os.path.exists(src):
                print(f"Moving results from {src} to {final_dir}...")
                shutil.move(src, final_dir)
            else:
                print(f"No result found for series {series_dir} in temporary save dir.")
        
        # 一時ディレクトリのクリーンアップ
        shutil.rmtree(temp_data_root)
        shutil.rmtree(temp_save_dir)

if __name__ == '__main__':
    download_weights()
    main("unet")
    main("swinunetr")
