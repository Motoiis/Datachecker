import csv
import os
import tkinter as tk
from tkinter import filedialog
import chardet
import pandas as pd
import numpy as np

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
def reset_similar_consecutive_values(data, threshold, n):
    count = 0  # 連続カウント用の変数
    to_reset = []  # 0にリセットするインデックスを保持するリスト
    prev_value = data[0]  # 最初の値を前回の値として保存

    for i in range(1, len(data)):
        # 現在のデータと前のデータの差がしきい値より小さいかどうかをチェック
        if abs(data[i] - prev_value) <= threshold:
            count += 1
            # 連続して近似の値がn-1回続いた場合（最初の値を含めるとn回）
            if count == n - 1:
                # 連続したn個のインデックスをto_resetに追加
                for j in range(n):
                    to_reset.append(i - j + 1)
        else:
            count = 0  # 連続カウントをリセット
            to_reset = []  # リセット用のリストをクリア
        prev_value = data[i]  # 現在の値を前回の値として更新

    # to_resetのインデックスに対応するデータを0に変更
    for idx in to_reset:
        data[idx] = 0
    return data

def integrate_using_trapezoidal(data, dt):
    integral = [0]  # start with initial value of 0
    for i in range(1, len(data)):
        trapezoid_area = (data[i-1] + data[i]) / 2 * dt
        integral.append(integral[i-1] + trapezoid_area)
    return integral

def all_distance(data):
    datasum = 0
    for i in range(len(data)):
        if data[i] < 0:
            datasum -= data[i]
        else:
            datasum += data[i]
            
    return datasum
        
def main():
    folderpath = select_folder()
    fileList = list_files_in_directory(folderpath)
    dt = 0.1
    keisan_df = pd.DataFrame(index = fileList,columns=["normalalldistance","lowpassalldistance","zeroalldistance","lowpassandzeroalldistance","normalvelocitydata","lowpassvelocitydata","zerovelocitydata","lowpassandzerovelocitydata","normaldistancedata","lowpassdistancedata","zerodistancedata","lowpassandzerodistancedata"])
    hantei_df = pd.DataFrame(index = fileList,columns=["normal","lowpass","zero","lowpassandzero","normalalldistance","lowpassalldistance","zeroalldistance","lowpassandzeroalldistance"])
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
        # continue_zero_data = reset_consecutive_values(data,2.5,4.5,3)
        # print("連続を排除=",continue_zero_data)#連続を排除
        # fillandzero = reset_consecutive_values(filtered_data,2.5,4.5,3)
        # print("ローパスした後に連続を排除=",fillandzero)
        
        #計算フェーズ
        #生データをそのまま
        normal_velocity = integrate_using_trapezoidal(data, dt)
        keisan_df.at[i,"normalvelocitydata"] = normal_velocity
        normal_distance = integrate_using_trapezoidal(normal_velocity, dt)
        keisan_df.at[i,"normaldistancedata"] = normal_distance
        normal_all_distance = all_distance(normal_distance)
        keisan_df.at[i,"normalalldistance"] = normal_all_distance
        hantei_df.at[i,"normalalldistance"] = normal_all_distance
        #ローパスフィルタをかけたデータ
        filterd_velocity = integrate_using_trapezoidal(filtered_data, dt)
        keisan_df.at[i,"lowpassvelocitydata"] = filterd_velocity
        filterd_distance = integrate_using_trapezoidal(filterd_velocity, dt)
        keisan_df.at[i,"lowpassdistancedata"] = filterd_distance
        filterd_all_distance = all_distance(filterd_distance)
        keisan_df.at[i,"lowpassalldistance"] = filterd_all_distance
        hantei_df.at[i,"lowpassalldistance"] = filterd_all_distance
        #なんか意味ないかも
        #速度が一定期間で連続している際にそれを削除
        zero_velocity = reset_similar_consecutive_values(normal_velocity,0.2,3)
        keisan_df.at[i,"zerovelocitydata"] = zero_velocity
        zero_distance = integrate_using_trapezoidal(zero_velocity, dt)
        keisan_df.at[i,"zerodistancedata"] = zero_distance
        zero_all_distance = all_distance(zero_distance)
        keisan_df.at[i,"zeroalldistance"] = zero_all_distance
        hantei_df.at[i,"zeroalldistance"] = zero_all_distance
        #ローパスフィルタをかけたデータに速度が一定期間で連続している際にそれを削除
        filterd_zero_velocity = reset_similar_consecutive_values(filterd_velocity,0.2,3)
        keisan_df.at[i,"lowpassandzerovelocitydata"] = filterd_zero_velocity
        filterd_zero_distance = integrate_using_trapezoidal(filterd_zero_velocity, dt)
        keisan_df.at[i,"lowpassandzerodistancedata"] = filterd_zero_distance
        filterd_zero_all_distance = all_distance(filterd_zero_distance)
        keisan_df.at[i,"lowpassandzeroalldistance"] = filterd_zero_all_distance
        hantei_df.at[i,"lowpassandzeroalldistance"] = filterd_zero_all_distance
    #リスト化
    normal_all_distancedata = hantei_df["normalalldistance"].tolist()
    filterd_all_distancedata = hantei_df["lowpassalldistance"].tolist()
    zero_all_distancedata = hantei_df["zeroalldistance"].tolist()
    filterd_zero_all_distancedata = hantei_df["lowpassandzeroalldistance"].tolist()
    print(normal_all_distancedata)
    #平均、標準偏差、中央値、最大値、最小値の導出
    
if __name__ == "__main__":
    main() 