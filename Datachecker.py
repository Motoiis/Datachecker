import csv
import os
import tkinter as tk
from tkinter import filedialog
import chardet

current_directory = os.getcwd()
def list_files_in_directory(directory_path):
    # os.listdir()でディレクトリ内のファイル/フォルダ名のリストを取得
    all_files_and_dirs = os.listdir(directory_path)
    
    # os.path.isfile()でファイルのみをフィルタリング
    only_files = [f for f in all_files_and_dirs if os.path.isfile(os.path.join(directory_path, f))]
    
    return only_files

def running_average_filter(data, window_size=3):
    filtered_data = []
    for i in range(len(data)):
        # ウィンドウの範囲を設定
        start_idx = max(0, i - window_size + 1)
        end_idx = i + 1
        # ウィンドウ内のデータの平均を取得
        avg = sum(data[start_idx:end_idx]) / len(data[start_idx:end_idx])
        filtered_data.append(avg)
    return filtered_data

def select_folder():
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しないための設定
    folder_path = filedialog.askdirectory()  # フォルダ選択ダイアログの表示
    return folder_path

def detect_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
        result = chardet.detect(rawdata)
        return result['encoding']

def reset_consecutive_values(data, range_min, range_max, n):
    count = 0  # 連続カウント用の変数
    to_reset = []  # 0にリセットするインデックスを保持するリスト

    for i in range(len(data)):
        # 現在のデータが指定範囲内かどうかをチェック
        if range_min <= data[i] <= range_max:
            count += 1
            # 連続して範囲内の数字がn個続いた場合
            if count == n:
                # 連続したn個のインデックスをto_resetに追加
                for j in range(n):
                    to_reset.append(i - j)
        else:
            count = 0  # 連続カウントをリセット

    # to_resetのインデックスに対応するデータを0に変更
    for idx in to_reset:
        data[idx] = 0

    return data


def main():
    folderpath = select_folder()
    fileList = list_files_in_directory(folderpath)
    print(fileList)
    for i in fileList:
        filepath = folderpath + f"\\{i}"
        encoding = detect_file_encoding(filepath)
        with open(filepath, encoding=encoding) as f:
            reader = csv.reader(f, delimiter= ',')
            csvdata = [row for row in reader]
        print("元データ=",csvdata[0])
        data = [float(s) for s in csvdata[0]]
        filtered_data = running_average_filter(data, window_size=3)
        print("rowpass=",filtered_data)#ローパスフィルタのデータ
        continue_zero_data = reset_consecutive_values(data,2.5,4.5,3)
        print("連続を排除=",continue_zero_data)#連続を排除
        fillandzero = reset_consecutive_values(filtered_data,2.5,4.5,3)
        print("ローパスした後に連続を排除",fillandzero)
        
if __name__ == "__main__":
    main() 