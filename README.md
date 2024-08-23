골프 라즈베리파이 제로 2 W 초기 설정 방법

1. SD카드에 라즈베리 파이 OS (64-bit) 다운로드 받고 부팅 (최초 부팅시에는 마우스, 모니터 같은 USB를 연결 해 줘야 함 -> 그 이후 최초 세팅이 끝나면 안해줘도 되는 듯?)
2. 세팅이 끝났다면 파이썬은 이미 기본 설치가 되어있으므로 SSH를 사용해서 원격으로 조정이 가능. 

	Window에서 PowerShell 열어서 <ssh pi@192.168.0.xx>와 같이
	ssh “설정한 이름”@“IP주소“로 연결 가능
3. ssh 접속한 상태에서 파이썬 파일 같은 경우는 nano test.py 와 같은 명령어를 사용하여 작성 가능 ctrl+o 눌러러서 저장 -> ctrl+x 눌러서 나가기
4. 그리고 python test.py로 실행 가능
5. WIFI 통신을 하기 위해서 sudo apt-get install create_ap 명령어로 ap에 관한 라이브러리(?) 설치함.
6. sudo pip install pandas를 통해서 라즈베리파이 전역에 설치 (주의 : 라즈베리파이 AP설정을 마치면 인터넷 접속이 어려우므로 미리 필요한 모듈들을 다운 받을 것)
7. https://d-tail.tistory.com/5 를 보고 무선 AP 설정
8. 파이썬 코드까지 작업을 맞췄다면 라즈베리파이 부팅시 바로 스크립트 실행 되도록 설정

- systemd를 사용하여 파이썬 스크립트를 부팅과 동시에 실행.

서비스 파일 작성:
서비스 파일 (your_script.service)을 /etc/systemd/system/ 디렉토리에 생성합니다.
sudo nano /etc/systemd/system/test.service

그런 다음, 다음 내용을 파일에 추가

[Unit]
Description=My Python Script Service
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /path/to/your_script.py

[Install]
WantedBy=multi-user.target


/path/to/your_script.py는 실제 파이썬 스크립트의 경로로 변경

서비스 권한 설정:
sudo chmod 644 /etc/systemd/system/your_script.service

systemd에 서비스 변경 사항 알림:
sudo systemctl daemon-reload

서비스 활성화:
sudo systemctl enable your_script.service

부팅 시 서비스 시작:
sudo systemctl start your_script.service

라즈베리파이가 부팅될 때마다 your_script.py가 자동으로 실행.



인터넷 연결 없이 pip 모듈 다운 받는 방법 -> 일단 실패.....


1. 다른 컴퓨터에서 Python 모듈 다운로드하기
먼저, 인터넷에 연결된 컴퓨터에서 필요한 Python 모듈을 다운로드합니다. 이를 위해 `pip`의 `download` 옵션을 사용할 수 있습니다. 예를 들어, `numpy` 모듈을 다운로드하려면 다음 명령을 사용합니다:

pip download numpy

이 명령은 현재 작업 디렉토리에 `numpy` 모듈과 필요한 모든 종속성을 `.whl` 또는 `.tar.gz` 형식으로 다운로드합니다.
＊주의＊ 라즈베리 파이에 맞는 버전을 다운로드

2. 파일을 라즈베리파이로 전송하기

3. 라즈베리파이에서 모듈 설치하기

라즈베리파이에서 다운로드한 파일이 저장된 디렉토리로 이동합니다. 그런 다음, `pip`를 사용하여 모듈을 설치합니다. 예를 들어, `numpy` 모듈이 `numpy-1.21.2-cp39-cp39-manylinux_2_24_armv7l.whl` 파일로 다운로드된 경우, 다음 명령을 사용하여 설치할 수 있습니다:

pip install numpy-1.21.2-cp39-cp39-manylinux_2_24_armv7l.whl
```

### 주의 사항

- **아키텍처 호환성**: 라즈베리파이에서 사용하는 ARM 아키텍처에 맞는 모듈을 다운로드해야 합니다. 일부 모듈은 ARM 프로세서용으로 별도로 컴파일되어야 할 수 있습니다.
- **Python 버전 호환성**: 라즈베리파이에서 사용하는 Python 버전과 호환되는 모듈 버전을 다운로드해야 합니다.
- **종속성 관리**: 모듈이 다른 종속성을 가지고 있다면, 해당 종속성도 함께 다운로드하고 설치해야 합니다. `pip download`는 기본적으로 필요한 종속성을 함께 다운로드합니다.

이 방법을 사용하면 라즈베리파이와 같은 오프라인 환경에서도 필요한 Python 모듈을 쉽게 설치할 수 있습니다.

라즈베리파이로 무선  AP 만드는 방법 
%% 중요https://d-tail.tistory.com/5
 

먼저 Raspbian 설치를 업데이트를 한다.

$ sudo apt-get update
$ sudo apt-get upgrade
그 다음 필요한 모든 소프트웨어를 한 번에 설치한다.

$ sudo apt-get install dnsmasq hostapd
이 소프트웨어들은 설치되면 바로 실행이 저절로 되기 때문에 구성 파일이 준비되지 않았으므로, 다음과 같이 새 소프트웨어를 꺼준다.

$ sudo systemctl stop dnsmasq
$ sudo systemctl stop hostapd
설치가 다 완료되었고, 소프트웨어도 껐다면 올바르게 사용하기 위해 리부트한다.

$ sudo reboot

----------
고정 IP 만들어주기 

독립형 네트워크를 구성하기 위해 라즈베리 파이에는 무선 포트에 static IP 주소가 할당 되어야 한다.

따라서 무선 네트워크 표준인 192.168.xx IP 주소를 사용하고 있다고 가정하고, 서버에 192.168.4.1을 할당한다.

$ sudo nano /etc/dhcpcd.conf
이 파일의 끝에 다음줄을 첨가한다.

interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
올바르게 작성했으면 다시 시작하여 새로운 wlan0 구성을 설정한다.

$ sudo service dhcpcd restart
----------
DHCP 서버 구성(dnsmasq)
DHCP 서비스는 dnsmasq에서 제공한다. 이 때, 기본적인 구성 파일에는 필요하지 않은 정보가 많이 포함되어 있기 때문에 처음부터 시작하기 위해서 파일을 옮기고, 새 파일을 만들어 수정한다.

$ sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  
$ sudo nano /etc/dnsmasq.conf

다음 줄들을 dnsmasq 파일에 입력한다.

다음 코드를 통해 192.168.4.2에서 192.168.4.20 사이의 IP 주소를 24시간 동안 제공해주는 것이다.

dnsmasq에는 더 많은 옵션들이 있고, 다른 섹션을 첨가하려면 이 사이트를 통해 살펴보면 된다.

interface=wlan0      # Use the require wireless interface - usually wlan0
  dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h

---------------------
액세스 포인트 호스트 소프트웨어 구성(hostapd)

이 다음은 무선 네트워크의 다양한 매개변수를 추가하는 것에 대한 내용이다.

/etc/hostapd/hostapd.conf에 있는 hostapd 구성 파일을 편집하면 된다.

$ sudo nano /etc/hostapd/hostapd.conf
다음 파일을 열어서 아래 내용을 첨가해주면 된다.

이 때, 이름과 암호는 ''로 묶으면 안되고, 암호는 8자에서 64자 사이여야한다.

5GHz 대역을 사용하려면 작동모드를 hw_mode=g에서 hw_mode=a로 변경하면 된다.

interface=wlan0
driver=nl80211
ssid=설정할 이름
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=암호
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
이 때, 혹시 무선 네트워크를 숨기고 싶다면, ignore_broadcast_ssid=1로 바꿔주면 된다.

이렇게 작성을 완료했다면 이 위치를 알려야 하기 때문에 다음과 같은 명령을 적어준다.

$ sudo nano /etc/default/hostapd
이 파일에서 #DAEMON_CONF 로 시작하는 줄을 찾아 다음과 같이 작성하고, 주석을 해제한다.

DAEMON_CONF="/etc/hostapd/hostapd.conf“

---------------
시작하기
이제 환경을 다 갖추었고, 시작하면 된다.

$ sudo systemctl start hostapd
$ sudo systemctl start dnsmasq
$ sudo nano /etc/sysctl.conf
로 가서, 다음 행의 주석을 해제한다.

net.ipv4.ip_forward=1
또한, 다음 명령을 추가한다.

$ sudo iptables -t nat -A  POSTROUTING -o eth0 -j MASQUERADE
$ sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
그리고, 다음 파일로 가서 exit0 바로 위에 다음 행을 추가한다.

$ sudo nano /etc/rc.local
iptables-restore < /etc/iptables.ipv4.nat
이제 모든 작업이 완료되었고, 리부트를 해준다.

$ sudo reboot

---------------------
ERRORS
직접 해보면서 한 두가지 오류들이 나왔었다.

먼저, hostapd를 설치할 때 제대로 설지가 되지 않았다. 

Failed to start hostapd.service: Unit hostapd.service is masked
라는 오류가 떴었고, 구글에서 찾아보니 아마 버전이 업데이트 되면서 마스크가 된채로 배포되어 생기는 문제 같았다.

$ sudo systemctl unmask hostapd
$ sudo systemctl enabel hostapd
$ sudo systemctl start hostapd
위의 명령들을 치고 나니 다행히 작동이 되었다.

 

또한, 나중에 모든 설정을 마치고 다시 hostapd를 실행시켰을 때 오류가 났었는데,

Job for hostapd.service failed because the control process exited with error code
라는 오류가 났었고 이유를 찾을 수가 없었다.

나중에 다시 차근차근 해보니 #DAEMON_CONF 의 주석처리를 제거하지 않아 생기는 문제였고, 주석을 해제하고 나니 잘 실행이 되었다.

hostapd dnsmasq 자동실행
라즈베리파이를 reboot했을 때, 자꾸 hostapd와 dnsmasq가 꺼져 다시 켜야하는 상황이 있었다.

이 때는

$ sudo update-rc.d hostapd enable
$ sudo update-rc.d dnsmasq enable
에러 사항 

1. 포트 80 바인딩 권한 오류:

포트 80은 프라이빗 포트 범위 내에 있어서 일반 사용자는 바인딩할 수 없습니다. 그러므로 코드를 “sudo 권한”으로 실행해야 합니다:

sudo python3 /home/pi/wifi_connection_test.py

또는 다른 고유한 포트 번호를 사용하여 바인딩하실 수도 있습니다. 예를 들면, 8080 포트를 사용하면 권한 없이도 바인딩할 수 있습니다.

2. sudo: create_ap: command not found

순서대로 실행

sudo apt-get install git util-linux procps hostapd iproute2 iw haveged dnsmasq
git clone https://github.com/oblique/create_ap
cd create_ap
sudo make install

3. 인터넷을 제거하고 생긴 에러 WARN: brmfmac driver doesn't work properly with virtual interfaces and
      it can cause kernel panic. For this reason we disallow virtual
      interfaces for your adapter.
      For more info: https://github.com/oblique/create_ap/issues/203
WARN: Your adapter does not fullly support AP virtual interface, enabling --no-virt
ERROR: 'eth0' is not an interface

4. WIFI 멀티 연결 오류 (7개 이상 연결이 안됨)
-> 펌웨어에서 WIFI의 메모리를 제한 하므로 이를 바꿔줘야함
(https://github.com/raspberrypi/linux/issues/3010) 

1. https://github.com/RPi-Distro/firmware-nonfree/tree/bullseye/debian/config/brcm80211/cypress -> 여기서 cyfmac43455-sdio-minimal.bin 파일 다운 받고
2. WIN SCP를 통해서 라즈베리 파이로 옮겨준다.
3. sudo update-alternatives —config cyfmac43455-sdio.bin 이 명령어를 통해서 다운받은 Bin 파일로 교체
4. 그리고 재부팅

5. root권한으로 되어있으면 파일/ 폴더 수정이 불가능 -> root 소유자을 다른 것으로 바꿔주기 

 sudo chown pi /home/pi/golf/
