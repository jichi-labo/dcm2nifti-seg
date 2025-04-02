# dcm2nifti-seg
## 概要
このプロジェクトではCTのDICOMファイル（**特に、クラウドベースのJ-MIDからダウンロードしたデータ**）をNIfTI形式に変換し、TotalSegmentatorとSuPreMを実行を迅速に行うためのコードを提供します。
## データ格納
DICOMファイルは以下のように`image/dcm/`内格納してください。
```
dcm2nifti-seg/
├── image/
│   ├── dcm/ 
│       ├── STD_****/            # 検査単位のフォルダ
│           ├── SER_1/           # シリーズ単位のフォルダ
│               ├── IMG_1.dcm   # dcmフォーマットの画像
│               └── …  
```
## 使い方
カレントディレクトリとして本プロジェクトのフォルダに移動し、コマンドラインで
1. make run_preprocess
  - `image/nifti/`内に、`image/dcm/`のフォルダ構成を模倣してniftiに変換した画像が作成されます。
3. make run_totalsegmentator
  - `image/nifti/`に格納されている画像について、totalsegmentatorのinference処理を実行します。結果は、`SER_1_ts/`のように、suffixがついて該当検査フォルダ内に格納されます。
  - なお、ImageTypeが`["ORIGINAL", "PRIMARY", "AXIAL"]`のものに絞って処理されます。変更する場合は`totalsegmentator/run_totalsegmentator.py`の内容を変更してください。また、本プロジェクトでは公式の出力のほか、**肝臓、膵臓、脾臓、右腎、左腎**に絞った結果を統合した`combined_label.nii.gz`も後処理で生成されます。
4. make run_suprem
  - 仕様は2とほぼ同様です。suffixはbackboneである`_unet`と`_swinunetr`の2つとしており、`suprem/run_suprem.py`を変更しない限り両方のモデルの出力が作られます。
