# Kaggle Setup (không cần Jupyter local)

Mục tiêu: chạy full pipeline Lab 3 trên Kaggle Notebook để sinh đủ `models/`, `outputs/`, `figures/` và test API logic (không cần mở port).

## 1) Upload project lên Kaggle

### Cách 1 (dễ nhất): upload zip

1. Nén cả thư mục `lab3_aiot_anomaly_event_intelligence_v3/` thành 1 file zip.
2. Kaggle → **Code** → **New Notebook**.
3. Sidebar **Add data** → **Upload** → upload file zip.

### Cách 2: dùng GitHub

Push repo lên GitHub rồi trong Kaggle chọn **Add data** → **GitHub**.

## 2) Cells để chạy

### Cell A — Giải nén zip vào `/kaggle/working/lab3`

```python
import os, glob, zipfile, pathlib

print("Inputs:", os.listdir("/kaggle/input"))
zip_paths = glob.glob("/kaggle/input/**/**/*.zip", recursive=True) + glob.glob("/kaggle/input/**/*.zip", recursive=True)
zip_paths = list(dict.fromkeys(zip_paths))
print("Found zips:", zip_paths)

zip_path = zip_paths[0]  # nếu có nhiều zip, đổi index tại đây
dest = "/kaggle/working/lab3"
pathlib.Path(dest).mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(dest)

print("Extracted to:", dest)
print("Top-level:", os.listdir(dest)[:50])
```

### Cell B — Tìm đúng thư mục project (nơi có `requirements.txt`) và `cd` vào đó

```python
import os, glob

candidates = glob.glob("/kaggle/working/lab3/**/requirements.txt", recursive=True)
print("requirements.txt candidates:", candidates)

project_dir = os.path.dirname(candidates[0])
print("Using project_dir:", project_dir)

os.chdir(project_dir)
print("CWD:", os.getcwd())
```

### Cell C — Cài dependencies

```python
!python -m pip install -U pip
!pip install -r requirements.txt
```

### Cell D — Chạy 1 lệnh (khuyến nghị): `run_all.py`

```python
!python run_all.py
```

Nếu bạn muốn chạy từng bước:

```python
!python src/download_data.py
!python src/train_anomaly.py
!python src/plot_results.py
!python src/test_api_local.py
```

## 3) Lấy file để nộp

Nếu cần gom lại thành 1 file:

```python
!zip -r lab3_submit.zip outputs figures models src requirements.txt README.md
```

Sau đó tải `lab3_submit.zip` từ phần file browser của Kaggle.

