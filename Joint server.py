import os
import socket
import subprocess
import time
import numpy as np
import pandas as pd
import json

# 서버 설정
HOST = '0.0.0.0'
PORT = 80
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(15)
server_socket.setblocking(False)

clients = []  # 연결된 클라이언트 목록
app_client = None  # 앱 클라이언트를 저장할 변수


def load_and_process_data(filepath):
    data = pd.read_csv(filepath, delimiter=',', header=None)
    sensors = ["Chest", "Hand", "Wrist", "Stomach", "Head"]  # 라즈베리파이 제로용
    # sensors = ["Chest", "Hand", "Wrist", "Stomach", "Head", "L_Arm", "R_wrist", "R_Arm", "L_thigh", "L_claf",
    #            "R_thigh", "R_calf"]
    quaternions = {sensor: data.iloc[:, 4*i:4*i+4] for i, sensor in enumerate(sensors)}
    return quaternions

def normalize_angle(current_angle, previous_angles):
    # Yaw 와 Roll은 값의 범위가 -180 ~ 180 이다.
    # 이에 따라서 실제로는 190일지라도 -170으로 표시되기에 이를 다시 190으로 정규화 하는 함수.

    above_50_values = [angle for angle in previous_angles if angle >= 50]
    under_m50_values = [angle for angle in previous_angles if angle <= -50]

    if len(above_50_values) > 2: # 이전의 값들이 50보다 큰 값들이 2개 이상 있으면.
        if current_angle < 0: # 그리고 현재 값이 음수라면
            current_angle = current_angle + 360

    if len(under_m50_values) > 2: # 이전의 값들이 -50보다 작은 값들이 2개 이상 있으면.
        if current_angle > 0: # 그리고 현재 값이 음수라면
            current_angle = current_angle - 360

    return current_angle
def quaternion_to_euler(q, previous_angles):
    x, y, z, w = q
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = np.arctan2(t0, t1)
    roll_x = round(np.degrees(roll_x), 1)    # 라디안을 도 단위로 변환
    roll_x = normalize_angle(roll_x,previous_angles[0])

    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch_y = np.arcsin(t2)
    pitch_y = round(np.degrees(pitch_y), 1)    # 라디안을 도 단위로 변환

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = np.arctan2(t3, t4)
    yaw_z = round(np.degrees(yaw_z), 1)    # 라디안을 도 단위로 변환
    yaw_z = normalize_angle(yaw_z, previous_angles[2])

    euler_angles = [roll_x, pitch_y, yaw_z]

    return euler_angles


def quaternions_to_euler_angles(quaternions):
    euler_angles = []
    previous_angles = [[0, 0, 0],[0, 0, 0],[0, 0, 0]]  # 초기 이전 각도값
    for quaternion in quaternions:
        euler_angles.append(quaternion_to_euler(quaternion, previous_angles))

        if len(euler_angles) >= 3:
            previous_angles = [[euler_angles[-3][0],euler_angles[-2][0],euler_angles[-1][0]],
                               [euler_angles[-3][1],euler_angles[-2][1],euler_angles[-1][1]],
                               [euler_angles[-3][2],euler_angles[-2][2],euler_angles[-1][2]]]


    print(euler_angles)
    return np.array(euler_angles)
def calculate_relative_changes(euler_angles):
    # 상대적 변화 계산
    relative_changes = {}
    for sensor, angles in euler_angles.items():
        changes = angles - angles[0]
        # 'Wrap-around' 처리
        # changes = np.where(changes < -180, changes + 360, changes)
        # changes = np.where(changes > 180, changes - 360, changes)
        relative_changes[sensor] = changes
    return relative_changes

def calculate_differences(relative_changes1, relative_changes2):
    # 두 데이터 세트 간의 상대적 변화 차이 계산
    differences = {}
    for sensor in relative_changes1.keys():
        diff = relative_changes1[sensor] - relative_changes2[sensor]
        differences[sensor] = diff
    return differences

def calculate_max_with_window(data, window_size):
    # 윈도우 크기만큼 각 값의 절대값을 취함
    abs_data = np.abs(data)
    # 이동 윈도우를 사용하여 최대값 계산
    window = np.ones(window_size)
    max_values = np.convolve(abs_data, window, mode='valid') / window_size
    return np.max(max_values)


def calculate_mean_differences(differences):
    mean_differences = {}
    for sensor, data in differences.items():
        # 각 축별 차이의 절대값을 계산하고 평균을 취함
        mean_roll_diff = np.mean(np.abs(data[40:, 0]))
        mean_pitch_diff = np.mean(np.abs(data[40:, 1]))
        mean_yaw_diff = np.mean(np.abs(data[40:, 2]))

        # 각 축별로 최대값 계산
        window_size = 10
        max_roll_diff = calculate_max_with_window(data[:, 0], window_size)
        max_pitch_diff = calculate_max_with_window(data[:, 1], window_size)
        max_yaw_diff = calculate_max_with_window(data[:, 2], window_size)

        # 평균 및 최대 차이 계산
        mean_diff = round((mean_roll_diff + mean_pitch_diff + mean_yaw_diff) / 3, 2)
        max_diff = round((max_roll_diff**2 + max_pitch_diff**2 + max_yaw_diff**2) ** (1/2) ,2)

        mean_diff = round(mean_diff / 360 * 100, 2)
        max_diff = round(max_diff / 360 * 100, 2)

        mean_differences[sensor] = {'mean': mean_diff, 'max': max_diff}

    return mean_differences

def calculate_average_euler_angles(name1, name2 ,name3 ,name4 ,name5):
    avg_quaternions1 = load_and_process_data(name1)
    avg_quaternions2 = load_and_process_data(name2)
    avg_quaternions3 = load_and_process_data(name3)
    avg_quaternions4 = load_and_process_data(name4)
    avg_quaternions5 = load_and_process_data(name5)

    avg_euler_angles1 = {sensor: quaternions_to_euler_angles(avg_quaternions1[sensor].values) for sensor in avg_quaternions1.keys()}
    avg_euler_angles2 = {sensor: quaternions_to_euler_angles(avg_quaternions2[sensor].values) for sensor in avg_quaternions2.keys()}
    avg_euler_angles3 = {sensor: quaternions_to_euler_angles(avg_quaternions3[sensor].values) for sensor in avg_quaternions3.keys()}
    avg_euler_angles4 = {sensor: quaternions_to_euler_angles(avg_quaternions4[sensor].values) for sensor in avg_quaternions4.keys()}
    avg_euler_angles5 = {sensor: quaternions_to_euler_angles(avg_quaternions5[sensor].values) for sensor in avg_quaternions5.keys()}

    avg_relative_changes1 = calculate_relative_changes(avg_euler_angles1)
    avg_relative_changes2 = calculate_relative_changes(avg_euler_angles2)
    avg_relative_changes3 = calculate_relative_changes(avg_euler_angles3)
    avg_relative_changes4 = calculate_relative_changes(avg_euler_angles4)
    avg_relative_changes5 = calculate_relative_changes(avg_euler_angles5)

    average_euler_angles = {}
    for sensor in avg_relative_changes1.keys():
        # 각 센서의 오일러 각도를 추출하고 평균을 계산
        avg_angles = (avg_relative_changes1[sensor] + avg_relative_changes2[sensor]+ avg_relative_changes3[sensor]+ avg_relative_changes4[sensor]+ avg_relative_changes5[sensor] ) / 5
        average_euler_angles[sensor] = avg_angles
    return average_euler_angles

'''
SLVAE : 1 qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
SLVAE : 2 qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
SLVAE : 3 qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
SLVAE : 4 qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
의 형식으로 받은 Raw 데이터를 
qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,qx,qy,qz,qw,
이런식으로 분석하기 쉽게 정렬해주는 작업
'''
def transform_data_to_parallel(data: str) -> list:
    # Split the data into lines
    lines = data.strip().split('\n')

    # Extract values for each slave
    slave_data = {}
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue  # Skip this line and proceed to the next
        slave_id = int(parts[3])
        values = [float(val) for val in parts[4].split(',')[:-1]]  # Remove 'END!!!'
        slave_data[slave_id] = values

    # Transform into desired format
    output = []
    grouped_data = [slave_data[key] for key in sorted(slave_data.keys())]
    for i in range(0, len(grouped_data[0]), 5):  # Change 4 to 5 here
        flattened = [item for sublist in grouped_data for item in sublist[i:i + 5]]  # Change 4 to 5 here
        output.append(','.join(f'{val:.2f}' for val in flattened))

    return output



# print("Waiting for a phone...")
# while (True):
#     try:
#         output = subprocess.check_output(['arp', '-a'])
#         print (output)
#         if output != b'':
#             break
#     except Exception as e:
#         pass
# start_time = time.time()  # 시작 시간 기록
#
# while time.time() - start_time < 10:  # 시작 시간으로부터의 차이가 5초 미만인 동안 루프 실행
#     # 원하는 코드를 여기에 작성
#     print("Looping...")
#     time.sleep(0.5)  # 예시로 0.5초 대기

 # # 디렉토리 생성
directory_path = '/home/pi/golf'
#
if not os.path.exists(directory_path):
    os.makedirs(directory_path)


print("Waiting for a connection...")
while True:
    data = b"no_data"
    try:
        client_socket, addr = server_socket.accept()
        client_socket.setblocking(False)  # 논블로킹 모드로 클라이언트 소켓 설정
        print(f"Connection from {addr}")
        clients.append(client_socket)

        if app_client is not None:
            app_client.send(f"Connection from {addr} \n".encode())

    except BlockingIOError:
        # 아직 연결 요청이 없음
        pass

    # sleeptime을 계속 바꿔주면서 혹시라도 ESP32와 엇물린 타이밍으로 인해서 연결이 안되는 경우를 방지
    sleeptime = 0.01
    time.sleep(sleeptime)
    sleeptime = sleeptime + 0.01
    if sleeptime >= 0.05:
        sleeptime = 0.01

    for client in clients:
        try:
            data = client.recv(1024)
            print(f"Received data from {client}: {data.decode('utf-8')}")    #

            if data.startswith(b"application"):
                print("This client is an app!")
                app_client = client
                app_client.send("FIND APP!!!!".encode())

        except BlockingIOError:
            # data = b"no_data"
            pass


    if data.startswith(b"start"):
        for client in clients:
            client.send("ON".encode())

        # data를 문자열로 변환
        decoded_data = data.decode("utf-8")
        # _를 기준으로 문자열 분할
        parts = decoded_data.split("_")

        if len(parts) >= 2:
            name = parts[1]                     # 저장한 파일 이름 구해오기
        else:
            name = "NO"


    elif data.startswith(b"stop"):
        for client in clients:
            client.send("OFF".encode())

        time.sleep(1)
        total_string_data = ""
        for client in clients:

            print(client)
            if client == app_client:
                continue

            # b""에서 b는 BYTE문자열을 의미한다. WIFI나 다른 통신으로 데이터를 주고받을 때는 Byte로 읽기 때문
            total_data = b""
            # blocking을 활성화해서 데이터가 들어올 떄까지 정지.
            client.setblocking(True)
            while True:
                data = client.recv(524288)
                total_data += data
                # total_data += b"\n"
                if b"END!!!" in data:
                    total_data += b"\n"
                    break
            client.setblocking(False)
            print(f"Received QUATERNION: {total_data.decode('utf-8')}")
            total_string_data += total_data.decode('utf-8')
            print("FINSH one slave \n")
            # app_client.send(f"FINSH one slave {client} \n".encode())

        print("Finish all slave data request")
        # app_client.send("Finish all slave data request".encode())


        # 텍스트 데이터 저장
        file_path = os.path.join(directory_path, name + '_raw.txt')
        with open(file_path, 'w') as file:
            file.write(total_string_data)
        print(f"File saved at: {file_path}")

        transformed_data = transform_data_to_parallel(total_string_data)

        # 리스트를 string으로 변환함.
        transformed_data = '\n'.join(transformed_data)

        # 텍스트 데이터 저장
        file_path = os.path.join(directory_path, name + '_trans.txt')
        with open(file_path, 'w') as file:
            file.write(transformed_data)
        print(f"File saved at: {file_path}")

        ############ txt파일을 읽어옴 ############
        file_path = directory_path + '/' + name + '_trans.txt'
        data = pd.read_csv(file_path, delimiter=',', header=None)  # use comma as delimiter
        # # Split the data into the individual sensors

        sensors = ["Chest", "Hand", "Wrist", "Stomach", "Head"]  # 라즈베리파이 제로용
        # sensors = ["Chest", "Hand", "Wrist", "Stomach", "Head", "L_Arm", "R_wrist", "R_Arm", "L_thigh", "L_claf",
        #            "R_thigh", "R_calf"]

        # #######################가속도를 기준으로 데이터를 자름#####################
        # Extract quaternions for each sensor from the new dataset
        quaternions = {sensor: data.loc[:, 5 * i: 5 * i + 4] for i, sensor in enumerate(sensors)}

        acc = {sensor: data.iloc[:, 5 * i + 4] for i, sensor in enumerate(sensors)}
        total_acc = sum(acc[sensor] for sensor in sensors[1:3])
        peak_index = total_acc.idxmax()

        quaternions = {sensor: data.loc[:, 5 * i:5 * i + 3] for i, sensor in enumerate(sensors)}

        trimmed_quaternions = {sensor: quats[peak_index - 100:peak_index + 10] for sensor, quats in quaternions.items()}

        # # 상대적인 y축 이동을 적용
        # for sensor in sensors:
        #     for i in range(4):
        #         first_value = trimmed_quaternions[sensor].iloc[0, i]  # 첫 번째 행, i번째 열의 값 가져오기
        #         trimmed_quaternions[sensor] = trimmed_quaternions[sensor].copy()  # 복사본을 만듭니다
        #         trimmed_quaternions[sensor].iloc[:, i] = round(trimmed_quaternions[sensor].iloc[:, i] ,2)

        ############ 자른 데이터 저장 ############
        # Combine all the quaternions into a single DataFrame
        all_quats_list = [trimmed_quaternions[sensor] for sensor in trimmed_quaternions]
        all_quats = pd.concat(all_quats_list, axis=1)
        all_quats = all_quats.iloc[:, :]
        # Save the DataFrame to a .txt file
        all_quats.to_csv(directory_path + '/'+name+'_trim.txt', index=False, header=False)

        ############ 프로 데이터와 분석 ############
    #     user = load_and_process_data(directory_path + '/' + name + '_trim.txt')
    #     # user = load_and_process_data('/home/pi/golf/punch1120_trim.txt')
    #
    #     # 각 센서별 오일러 각도 추출
    #     user_euler_angles = {sensor: quaternions_to_euler_angles(user[sensor].values) for sensor in
    #                      user.keys()}
    #     user_relative_changes = calculate_relative_changes(user_euler_angles)
    #
    #     mean_differences={}
    #     if name.startswith("punch"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Punch1_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Punch2_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Punch3_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Punch4_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Punch5_raw_forzerotrim.txt')
    #     elif name.startswith("draw"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Draw2_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Draw3_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Draw4_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Draw5_raw_forzerotrim.txt',
    #                                                   '/home/pi/golf/pro/Draw6_raw_forzerotrim.txt')
    #     elif name.startswith("fade"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Fade1_raw_forzerotrim.txt','/home/pi/golf/pro/Fade1_raw_forzerotrim.txt', '/home/pi/golf/pro/Fade3_raw_forzerotrim.txt',
    #                                                '/home/pi/golf/pro/Fade5_raw_forzerotrim.txt', '/home/pi/golf/pro/Fade7_raw_forzerotrim.txt' )
    #     elif name.startswith("chip"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Chip1_raw_forzerotrim.txt', '/home/pi/golf/pro/Chip2_raw_forzerotrim.txt',
    #                                                '/home/pi/golf/pro/Chip3_raw_forzerotrim.txt', '/home/pi/golf/pro/Chip4_raw_forzerotrim.txt', '/home/pi/golf/pro/Chip5_raw_forzerotrim.txt' )
    #     elif name.startswith("flop"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Flop1_raw_forzerotrim.txt', '/home/pi/golf/pro/Flop1_raw_forzerotrim.txt',
    #                                                '/home/pi/golf/pro/Flop2_raw_forzerotrim.txt', '/home/pi/golf/pro/Flop4_raw_forzerotrim.txt', '/home/pi/golf/pro/Flop4_raw_forzerotrim.txt' )
    #     elif name.startswith("pitch"):
    #         # 상대적 변화 계산
    #         pro_data = calculate_average_euler_angles('/home/pi/golf/pro/Pitch1_raw_forzerotrim.txt', '/home/pi/golf/pro/Pitch1_raw_forzerotrim.txt',
    #                                                '/home/pi/golf/pro/Pitch2_raw_forzerotrim.txt', '/home/pi/golf/pro/Pitch3_raw_forzerotrim.txt', '/home/pi/golf/pro/Pitch4_raw_forzerotrim.txt' )
    #
    #
    #     # 상대적 변화의 차이 계산
    #     differences = calculate_differences(pro_data, user_relative_changes)
    #     mean_differences = calculate_mean_differences(differences)
    #     mean_differences = json.dumps(mean_differences) ## dict 타입을 string으로 변환해야 encode()가 가능
    #     print(mean_differences)
    #     app_client.send(mean_differences.encode())
    #
    # elif data.startswith(b"layup"):
    #     pro_man_thickshot_avg = load_and_process_data('/home/pi/golf/Punch_forzeroavg.txt')
    #     # user = load_and_process_data(directory_path + '/' + name + '_trim.txt')
    #     user = load_and_process_data('/home/pi/golf/Punch1_raw_forzerotrim.txt')
    #
    #     # 각 센서별 오일러 각도 추출
    #     euler_angles1 = {sensor: quaternions_to_euler_angles(pro_man_thickshot_avg[sensor].values) for sensor in
    #                      pro_man_thickshot_avg.keys()}
    #     euler_angles2 = {sensor: quaternions_to_euler_angles(user[sensor].values) for sensor in
    #                      user.keys()}
    #
    #     # 상대적 변화 계산
    #     relative_changes1 = calculate_relative_changes(euler_angles1)
    #     relative_changes2 = calculate_relative_changes(euler_angles2)
    #
    #     # 상대적 변화의 차이 계산
    #     differences = calculate_differences(relative_changes1, relative_changes2)
    #
    #     mean_differences = calculate_mean_differences(differences)
    #     mean_differences = json.dumps(mean_differences)  ## dict 타입을 string으로 변환해야 encode()가 가능
    #     print(mean_differences)
    #     app_client.send(mean_differences.encode())


    elif data == b"POWEROFF":
        print("Powering off due to received signal!")
        os.system("sudo poweroff")

    elif data == b"SYSTEMOFF":
        break

    elif data.startswith(b"send"):

        # data를 문자열로 변환
        decoded_data = data.decode("utf-8")
        # _를 기준으로 문자열 분할
        parts = decoded_data.split("_")

        if len(parts) >= 2:
            name = parts[1]
        else:
            name = "NO"

        file_path = directory_path + '/' + name + '_trans.txt'
        file = open(file_path, "r")
        data_txt = file.read()
        print(data)
        app_client.send(data_txt.encode())
        file.close()

    # ... 기타 필요한 로직 추가 ...

    # # 연결 종료
    # client_socket.close()
    # clients.remove(client_socket)


