import csv
import os
import tkinter as tk
from tkinter import filedialog
import chardet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
#速度が一定期間連続している際にそれを削除
def reset_similar_consecutive_values(data, threshold, n):
    count = 0  # 連続カウント用の変数
    reset_index = -1  # 0にリセットを開始するインデックス
    data_copy = data.copy()  # 元のデータのコピーを作成
    prev_value = data_copy[0]  # 最初の値を前回の値として保存

    for i in range(1, len(data_copy)):
        # 現在のデータと前のデータの差がしきい値より小さいかどうかをチェック
        if abs(data_copy[i] - prev_value) <= threshold:
            count += 1
            # 連続して近似の値がn-1回続いた場合（最初の値を含めるとn回）
            if count == n - 1:
                reset_index = i - (n - 1)  # 0にリセットを開始するインデックスを設定
                break  # 以降のデータを処理する必要がないため、ループを終了
        else:
            count = 0  # 連続カウントをリセット
        prev_value = data_copy[i]  # 現在の値を前回の値として更新

    # reset_index以降のデータを0に変更
    if reset_index != -1:
        for i in range(reset_index, len(data_copy)):
            data_copy[i] = 0

    return data_copy

#台形法で計算
def integrate_using_trapezoidal(data, dt):
    integral = [0]  # start with initial value of 0
    for i in range(1, len(data)):
        trapezoid_area = (data[i-1] + data[i]) / 2 * dt
        integral.append(integral[i-1] + trapezoid_area)
    return integral
#距離の合計
def all_distance(data):
    datasum = 0
    for i in range(len(data)):
        if data[i] < 0:
            datasum -= data[i]
        else:
            datasum += data[i]
            
    return datasum
        
def acceldatatozero(data, n):
    data_copy = data.copy()  # 元のデータのコピーを作成
    count = 0  # 連続する小さい値のカウント
    to_reset = []  # ゼロにリセットするインデックスを保持するリスト
    for i in range(len(data_copy)):
        if abs(data_copy[i]) < 0.98:
            count += 1
            to_reset.append(i)  # 現在のインデックスをリセットリストに追加
            # 連続カウントがnに達した場合
            if count == n:
                # 連続する値をゼロにリセット
                for idx in to_reset:
                    data_copy[idx] = 0
                # リセットリストとカウントをクリア
                to_reset = []
                count = 0
        else:
            # 連続カウントとリセットリストをクリア
            to_reset = []
            count = 0
    return data_copy

def main():
    # folderpath = select_folder()
    folderpath = r"/Users/member/Desktop/実験/Rikogaku/Datachecker/2023-11-09"
    fileList1 = list_files_in_directory(folderpath)
    dt = 0.05
    suffixes = ['x', 'y', 'z', 'pitch', 'roll', 'yaw']
    column1 = ["normalalldistance","lowpassalldistance","zeroalldistance","lowpassandzeroalldistance","accelzeroalldistance",
               "AandVzeroalldistance","normalvelocitydata","lowpassvelocitydata","zerovelocitydata","lowpassandzerovelocitydata",
               "normaldistancedata","lowpassdistancedata","zerodistancedata","lowpassandzerodistancedata"]
    column2 = ["normal","lowpass","zero","lowpassandzero","normalalldistance","lowpassalldistance","zeroalldistance","lowpassandzeroalldistance"]

    # print(fileList)
    #ここファイルリストで作っているから変
    keisan_df = pd.DataFrame(index = suffixes,columns=column1)
    hantei_df = pd.DataFrame(index = suffixes,columns=column2)
    # print(fileList)
    for i in fileList1:
        filepath = os.path.join(folderpath, i)
        # print(filepath)
        encoding = detect_file_encoding(filepath)
        
        with open(filepath, encoding=encoding) as f:
            reader = csv.reader(f, delimiter= ',')
            next(reader)
            csvdata = [row for row in reader]
        
        # print("元データ=",csvdata[0])
        data1 = [[float(item) for item in row] for row in csvdata]
        # print("data=",data)
        # print("data=",data)
        # 例として、0から4までの整数の配列を作成
        data = [[item * 9.8 for item in sublist] for sublist in data1]
        
        if data != []:
            for j in range(3):
                filtered_data = running_average_filter(data[j], window_size=3)
                # print("rowpass=",filtered_data)#ローパスフィルタのデータ
                # continue_zero_data = reset_consecutive_values(data,2.5,4.5,3)
                # print("連続を排除=",continue_zero_data)#連続を排除
                # fillandzero = reset_consecutive_values(filtered_data,2.5,4.5,3)
                # print("ローパスした後に連続を排除=",fillandzero)
                
                #計算フェーズ
                #生データをそのまま
                #速度求める
                normal_velocity = integrate_using_trapezoidal(data[j], dt)
                keisan_df.at[suffixes[j],"normalvelocitydata"] = normal_velocity
                
                # print("normal_velocity=",normal_velocity)
                #距離求める
                normal_distance = integrate_using_trapezoidal(normal_velocity, dt)
                keisan_df.at[suffixes[j],"normaldistancedata"] = normal_distance
                #距離の合計
                normal_all_distance = all_distance(normal_distance)
                keisan_df.at[suffixes[j],"normalalldistance"] = normal_all_distance

                #加速度に0補正を入れたデータ
                #加速度データにゼロを代入
                accelzero_data = acceldatatozero(data[j], 20)
                # print("zero_data=",zero_data)
                #速度求める
                accelzero_velocity = integrate_using_trapezoidal(accelzero_data, dt)
                #加速度と速度に補正を入れた速度データ
                AandVzero_velocity = reset_similar_consecutive_values(accelzero_velocity,0.1,20)

                #距離求める
                AandVzero_distance = integrate_using_trapezoidal(AandVzero_velocity, dt)
                #距離の合計
                AandVzero_all_distance = all_distance(AandVzero_distance)
                keisan_df.at[suffixes[j],"AandVzeroalldistance"] = AandVzero_all_distance

                hantei_df.at[suffixes[j],"normalalldistance"] = normal_all_distance
                #ローパスフィルタをかけたデータ
                #速度求める
                filterd_velocity = integrate_using_trapezoidal(filtered_data, dt)
                keisan_df.at[suffixes[j],"lowpassvelocitydata"] = filterd_velocity
                #距離求める
                filterd_distance = integrate_using_trapezoidal(filterd_velocity, dt)
                keisan_df.at[suffixes[j],"lowpassdistancedata"] = filterd_distance
                #距離の合計
                filterd_all_distance = all_distance(filterd_distance)
                keisan_df.at[suffixes[j],"lowpassalldistance"] = filterd_all_distance
                hantei_df.at[suffixes[j],"lowpassalldistance"] = filterd_all_distance
                #なんか意味ないかも
                #速度が一定期間で連続している際にそれを削除
                # print("normal_velocity=",normal_velocity)
                zero_velocity = reset_similar_consecutive_values(normal_velocity,0.1,10)
                keisan_df.at[suffixes[j],"zerovelocitydata"] = zero_velocity
                # print("normal_velocity=",normal_velocity)
                #距離求める
                zero_distance = integrate_using_trapezoidal(zero_velocity, dt)
                keisan_df.at[suffixes[j],"zerodistancedata"] = zero_distance
                #距離の合計
                zero_all_distance = all_distance(zero_distance)
                keisan_df.at[suffixes[j],"zeroalldistance"] = zero_all_distance
                hantei_df.at[suffixes[j],"zeroalldistance"] = zero_all_distance
                #ローパスフィルタをかけたデータに速度が一定期間で連続している際にそれを削除
                filterd_zero_velocity = reset_similar_consecutive_values(filterd_velocity,0.1,10)
                keisan_df.at[suffixes[j],"lowpassandzerovelocitydata"] = filterd_zero_velocity
                #距離求める
                filterd_zero_distance = integrate_using_trapezoidal(filterd_zero_velocity, dt)
                keisan_df.at[suffixes[j],"lowpassandzerodistancedata"] = filterd_zero_distance
                filterd_zero_all_distance = all_distance(filterd_zero_distance)
                keisan_df.at[suffixes[j],"lowpassandzeroalldistance"] = filterd_zero_all_distance
                hantei_df.at[suffixes[j],"lowpassandzeroalldistance"] = filterd_zero_all_distance
                #リスト化
                normal_all_distancedata = hantei_df["normalalldistance"].tolist()
                filterd_all_distancedata = hantei_df["lowpassalldistance"].tolist()
                zero_all_distancedata = hantei_df["zeroalldistance"].tolist()
                filterd_zero_all_distancedata = hantei_df["lowpassandzeroalldistance"].tolist()
                x = np.arange(0, 40, 0.05)
                # print(len(data[j]))

                #加速度のグラフ
                plt.plot(data[j])
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('accelglaph')
                plt.xlabel('Time')
                plt.ylabel('accel')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Accel",f"make_graphAccel{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

                # 速度のグラフ
                plt.plot(normal_velocity)
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('normalvelocity')
                plt.xlabel('Time')
                plt.ylabel('velocity')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

                #距離のグラフ
                plt.plot(normal_distance)
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('normalvelocity')
                plt.xlabel('Time')
                plt.ylabel('Dicetance')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Distance",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

                # # ゼロ修正後の速度のグラフ
                # plt.plot(zero_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('zerovelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Zero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #ローパスフィルタをかけた後の速度のグラフ
                # plt.plot(filterd_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('filterdvelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Filter","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                #加速度に補正を入れた加速度グラフ
                plt.plot(accelzero_data)
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('filterdvelocity')
                plt.xlabel('Time')
                plt.ylabel('velocity')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","Accelzero","Accel",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

                # #加速度に補正を入れた速度グラフ
                # plt.plot(accelzero_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('filterdvelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Accelzero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                #加速度と速度に補正を入れた位置グラフ
                plt.plot(AandVzero_velocity)
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('filterdvelocity')
                plt.xlabel('Time')
                plt.ylabel('velocity')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","AandVzero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

                #加速度と速度に補正を入れた距離グラフ
                plt.plot(AandVzero_distance)
                # グラフのタイトルと軸ラベルの追加（オプション）
                plt.title('filterdvelocity')
                plt.xlabel('Time')
                plt.ylabel('distance')
                # グラフを画像として保存
                make_graph_filepath = os.path.join(current_directory, "Glaph","AandVzero","Distance",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                plt.savefig(make_graph_filepath)
                plt.close()

        hantei_filepath = os.path.join(current_directory, "Calculate",f"hantei{i}.csv")
        keisan_filepath = os.path.join(current_directory, "Calculate",f"keisan{i}.csv")
        hantei_df.to_csv(hantei_filepath, index=False)
        keisan_df.to_csv(keisan_filepath, index=False)
        hantei_filepath = os.path.join(current_directory, "Calculate",f"hantei{i}.csv")
        keisan_filepath = os.path.join(current_directory, "Calculate",f"keisan{i}.csv")
        hantei_df.to_csv(hantei_filepath, index=False)
        keisan_df.to_csv(keisan_filepath, index=False)

    # print(normal_all_distancedata)
    #平均、標準偏差、中央値、最大値、最小値の導出
    
if __name__ == "__main__":
    main() 