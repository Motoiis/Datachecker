import csv
import os
import tkinter as tk
from tkinter import filedialog
import chardet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#項目を追加するときはhantei_columnと処理を追加すればできる
#!**消去している＊＊＊＊カレントディレクトリの指定
# current_directory = os.getcwd()
current_directory = r"/Users/member/Desktop/実験/Rikogaku/判定条件から結果を導出"
def list_files_in_directory(directory_path):
    # os.listdir()でディレクトリ内のファイル/フォルダ名のリストを取得
    all_files_and_dirs = os.listdir(directory_path)
    # os.path.isfile()でファイルのみをフィルタリング
    only_files = [f for f in all_files_and_dirs if os.path.isfile(os.path.join(directory_path, f))]
    
    return only_files

def running_average_filter(data, window_size=3):
    filtered = []
    for i in range(len(data)):
        # ウィンドウの範囲を設定
        start_idx = max(0, i - window_size + 1)
        end_idx = i + 1
        # ウィンドウ内のデータの平均を取得
        avg = sum(data[start_idx:end_idx]) / len(data[start_idx:end_idx])
        filtered.append(avg)
    return filtered

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
    folderpath = select_folder()
    # folderpath = r"/Users/member/Desktop/実験/Rikogaku/2023-12-05"
    fileList1 = list_files_in_directory(folderpath)
    dt = 0.05
    suffixes = ['x', 'y', 'z', 'pitch', 'roll', 'yaw']
    hantei_columns = ['raw','a_zero','a_and_v_zero','lowpass','v_zero','lowpass_and_v_zero']
    zokusei = ['_accel_data', '_velocity_data', '_distance_data']
    keisan_columns = [h + z for h in hantei_columns for z in zokusei]
    print(keisan_columns)

    # print(fileList)
    #ここファイルリストで作っているから変
    #計算用のデータフレーム
    keisan_df = pd.DataFrame(index = suffixes,columns=keisan_columns)
    #判定用のデータフレーム
    hantei_df = pd.DataFrame(index = suffixes,columns=hantei_columns)
    #そう距離をまとめる
    normal_all_distancedata = [[],[],[]]
    a_zero_all_distancedata = [[],[],[]]
    a_and_v_zero_all_distancedata = [[],[],[]]
    lowpass_all_distancedata = [[],[],[]]
    v_zero_all_distancedata = [[],[],[]]
    lowpass_and_v_zero_all_distancedata = [[],[],[]]
    # print(fileList)
    #ファイルぶん回す
    for i in fileList1:
        if i != ".DS_Store":
            filepath = os.path.join(folderpath, i)
        else:
            pass
        # print(filepath)
        encoding = detect_file_encoding(filepath)
        
        with open(filepath, encoding=encoding) as f:
            reader = csv.reader(f, delimiter= ',')
            next(reader)
            csvdata = [row for row in reader]
        
        # print("元データ=",csvdata[0])
        data1 = []
        for row in csvdata:
            converted_row = []
            for item in row:
                try:
                    # 変換を試みる
                    converted_row.append(float(item))
                except ValueError:
                    # 変換できない場合は元の値を保持
                    converted_row.append(item)
            data1.append(converted_row)


        data = [[item * 9.8 for item in sublist] for sublist in data1]
        
        if data != []:
            for j in range(3):
                #生データ
                raw_accel = data[j]
                keisan_df.at[suffixes[j],"raw_accel_data"] = raw_accel
                raw_velocity = integrate_using_trapezoidal(data[j], dt)
                keisan_df.at[suffixes[j],"raw_velocity_data"] = raw_velocity
                #距離求める
                raw_distance = integrate_using_trapezoidal(raw_velocity, dt)
                keisan_df.at[suffixes[j],"raw_distance_data"] = raw_distance
                normal_all_distancedata[j].append(all_distance(raw_distance))
                hantei_df.at[suffixes[j],"raw"] = all_distance(raw_distance)
                #加速度を0にする
                a_zero_accel_data = acceldatatozero(raw_accel, 10)
                keisan_df.at[suffixes[j],"a_zero_accel_data"] = a_zero_accel_data
                #速度を求める
                a_zero_velocity = integrate_using_trapezoidal(a_zero_accel_data, dt)
                keisan_df.at[suffixes[j],"a_zero_velocity_data"] = a_zero_velocity
                #距離求める
                a_zero_distance = integrate_using_trapezoidal(a_zero_velocity, dt)
                keisan_df.at[suffixes[j],"a_zero_distance_data"] = a_zero_distance
                a_zero_all_distancedata[j].append(all_distance(a_zero_distance))
                hantei_df.at[suffixes[j],"a_zero"] = all_distance(a_zero_distance)
                #加速度と速度を0にする
                a_and_v_zero_accel_data = a_zero_accel_data
                keisan_df.at[suffixes[j],"a_and_v_zero_accel_data"] = a_and_v_zero_accel_data
                #速度を求める
                a_and_v_zero_velocity = reset_similar_consecutive_values(a_zero_velocity,0.1,10)
                keisan_df.at[suffixes[j],"a_and_v_zero_velocity_data"] = a_and_v_zero_velocity
                #距離求める
                a_and_v_zero_distance = integrate_using_trapezoidal(a_and_v_zero_velocity, dt)
                keisan_df.at[suffixes[j],"a_and_v_zero_distance_data"] = a_and_v_zero_distance
                a_and_v_zero_all_distancedata[j].append(all_distance(a_and_v_zero_distance))
                hantei_df.at[suffixes[j],"a_and_v_zero"] = all_distance(a_and_v_zero_distance)

                #ローパスフィルター
                lowpass_accel_data = running_average_filter(raw_accel, 5)
                keisan_df.at[suffixes[j],"lowpass_accel_data"] = lowpass_accel_data
                #速度を求める
                lowpass_velocity = integrate_using_trapezoidal(lowpass_accel_data, dt)
                keisan_df.at[suffixes[j],"lowpass_velocity_data"] = lowpass_velocity
                #距離求める
                lowpass_distance = integrate_using_trapezoidal(lowpass_velocity, dt)
                keisan_df.at[suffixes[j],"lowpass_distance_data"] = lowpass_distance
                lowpass_all_distancedata[j].append(all_distance(lowpass_distance))
                hantei_df.at[suffixes[j],"lowpass"] = all_distance(lowpass_distance)

                #速度を0にする
                v_zero_accel_data = raw_accel
                keisan_df.at[suffixes[j],"v_zero_accel_data"] = v_zero_accel_data
                v_zero_velocity = reset_similar_consecutive_values(raw_velocity,0.1,10)
                keisan_df.at[suffixes[j],"v_zero_velocity_data"] = v_zero_velocity
                #距離求める
                v_zero_distance = integrate_using_trapezoidal(v_zero_velocity, dt)
                keisan_df.at[suffixes[j],"v_zero_distance_data"] = v_zero_distance
                v_zero_all_distancedata[j].append(all_distance(v_zero_distance))
                hantei_df.at[suffixes[j],"v_zero"] = all_distance(v_zero_distance)

                #ローパスフィルターと速度を0にする
                lowpass_and_v_zero_accel_data = running_average_filter(raw_accel, 5)
                keisan_df.at[suffixes[j],"lowpass_and_v_zero_accel_data"] = lowpass_and_v_zero_accel_data
                #速度を求める
                lowpass_and_v_zero_velocity = reset_similar_consecutive_values(lowpass_and_v_zero_accel_data,0.1,10)
                keisan_df.at[suffixes[j],"lowpass_and_v_zero_velocity_data"] = lowpass_and_v_zero_velocity
                #距離求める
                lowpass_and_v_zero_distance = integrate_using_trapezoidal(lowpass_and_v_zero_velocity, dt)
                keisan_df.at[suffixes[j],"lowpass_and_v_zero_distance_data"] = lowpass_and_v_zero_distance
                lowpass_and_v_zero_all_distancedata[j].append(all_distance(lowpass_and_v_zero_distance))
                hantei_df.at[suffixes[j],"lowpass_and_v_zero"] = all_distance(lowpass_and_v_zero_distance)


                # #加速度のグラフ
                # plt.plot(raw_accel)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('accelglaph')
                # plt.xlabel('Time')
                # plt.ylabel('accel')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Accel",f"make_graphAccel{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # # 速度のグラフ
                # plt.plot(raw_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('normalvelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #距離のグラフ
                # plt.plot(raw_distance)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('normalvelocity')
                # plt.xlabel('Time')
                # plt.ylabel('Dicetance')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Normal","Distance",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # # ゼロ修正後の速度のグラフ
                # plt.plot(a_zero_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('zerovelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Zero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #ローパスフィルタをかけた後の速度のグラフ
                # plt.plot(lowpass_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('filterdvelocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Filter","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #加速度に補正を入れた加速度グラフ
                # plt.plot(a_zero_accel_data)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('a_zero_accelglaph')
                # plt.xlabel('Time')
                # plt.ylabel('accel')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Accelzero","Accel",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #加速度に補正を入れた速度グラフ
                # plt.plot(a_zero_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('a_zero_velocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","Accelzero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

                # #加速度と速度に補正を入れた位置グラフ
                # plt.plot(a_and_v_zero_velocity)
                # # グラフのタイトルと軸ラベルの追加（オプション）
                # plt.title('a_and_v_zero_velocity')
                # plt.xlabel('Time')
                # plt.ylabel('velocity')
                # # グラフを画像として保存
                # make_graph_filepath = os.path.join(current_directory, "Glaph","AandVzero","Velocity",f"make_graphnormalVelocity{i}{suffixes[j]}.png")
                # plt.savefig(make_graph_filepath)
                # plt.close()

        hantei_filepath = os.path.join(current_directory, "Calculate",f"hantei{i}.csv")
        keisan_filepath = os.path.join(current_directory, "Calculate",f"keisan{i}.csv")
        hantei_df.to_csv(hantei_filepath, index=False)
        keisan_df.to_csv(keisan_filepath, index=False)
    
    normal_all_distancedata = np.array(normal_all_distancedata)
    a_zero_all_distancedata = np.array(a_zero_all_distancedata)
    a_and_v_zero_all_distancedata = np.array(a_and_v_zero_all_distancedata)
    lowpass_all_distancedata = np.array(lowpass_all_distancedata)
    v_zero_all_distancedata = np.array(v_zero_all_distancedata)
    lowpass_and_v_zero_all_distancedata = np.array(lowpass_and_v_zero_all_distancedata)
    hantei_zyoken_columns=["_max","_min","_average","_std","_median"]
    all_hantei_zyoken_columns = [h + z for h in hantei_columns for z in hantei_zyoken_columns]
    hantei_zyoken_df = pd.DataFrame(index = suffixes,columns=all_hantei_zyoken_columns)

    for j in range(3):
        hantei_zyoken_df.at[suffixes[j],"raw_average"] = np.average(normal_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"raw_std"] = np.std(normal_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"raw_max"] = np.max(normal_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"raw_min"] = np.min(normal_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"raw_median"] = np.median(normal_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_zero_average"] = np.average(a_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_zero_std"] = np.std(a_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_zero_max"] = np.max(a_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_zero_min"] = np.min(a_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_zero_median"] = np.median(a_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_and_v_zero_average"] = np.average(a_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_and_v_zero_std"] = np.std(a_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_and_v_zero_max"] = np.max(a_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_and_v_zero_min"] = np.min(a_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"a_and_v_zero_median"] = np.median(a_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_average"] = np.average(lowpass_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_std"] = np.std(lowpass_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_max"] = np.max(lowpass_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_min"] = np.min(lowpass_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_median"] = np.median(lowpass_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"v_zero_average"] = np.average(v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"v_zero_std"] = np.std(v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"v_zero_max"] = np.max(v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"v_zero_min"] = np.min(v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"v_zero_median"] = np.median(v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_and_v_zero_average"] = np.average(lowpass_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_and_v_zero_std"] = np.std(lowpass_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_and_v_zero_max"] = np.max(lowpass_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_and_v_zero_min"] = np.min(lowpass_and_v_zero_all_distancedata[j])
        hantei_zyoken_df.at[suffixes[j],"lowpass_and_v_zero_median"] = np.median(lowpass_and_v_zero_all_distancedata[j])

    hantei_zyoken_filepath = os.path.join(current_directory, "Calculate",f"hantei_zyoken.csv")
    hantei_zyoken_df.to_csv(hantei_zyoken_filepath, index=False)
    for i in range(3):

        hantei_df.at[suffixes[i],"raw"] = np.average(normal_all_distancedata[i])
        hantei_df.at[suffixes[i],"a_zero"] = np.average(a_zero_all_distancedata[i])
        hantei_df.at[suffixes[i],"a_and_v_zero"] = np.average(a_and_v_zero_all_distancedata[i])
        hantei_df.at[suffixes[i],"lowpass"] = np.average(lowpass_all_distancedata[i])
        hantei_df.at[suffixes[i],"v_zero"] = np.average(v_zero_all_distancedata[i])
        hantei_df.at[suffixes[i],"lowpass_and_v_zero"] = np.average(lowpass_and_v_zero_all_distancedata[i])
# print(normal_all_distancedata)
    #平均、std、median、max、minの導出
    #まとまったデータ

if __name__ == "__main__":
    main() 