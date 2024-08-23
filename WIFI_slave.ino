#include <WiFi.h>
#include "MPU9250.h"

///////////////////////////////// SLAVEID만 바꾸어서 업로드//////////////////////////////////////////////////////////////////
int  SLAVEID = 10;

const char *ssid = "ESPMASTER";
const char *password = "123456789";

WiFiClient client;

std::vector<float> qq;


#define SerialDebug   false  // Set to true to get Serial output for debugging
#define I2Cclock      400000
#define MPU_INT_PIN   5 // Interrupt Pin definitions
MPU9250       mpu;

float test_var=0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");

  while (!client.connect("192.168.4.1", 80)) {
    delay(100);
    Serial.println("Connecting to Server...");
  }

  Serial.println("Connected to Server");

  ////////////MPU초기화//////////////////////
  mpu.selectFilter( QuatFilterSel::MAHONY);
  mpu.setup(0x68,0);  // change to your own address 
}


bool golf_operate = false;
int past;
int now;
void loop() {
  past = millis();

  if (client.connected()) {

    while (client.available()) {      // WIFI로 Client에 데이터가 들어오는 경우에만 작동
      String command = client.readStringUntil('\n');
      if (command.startsWith("ON")) {
        Serial.println("Operation started");
        golf_operate = true;

        // 쿼터니안 벡터 초기화
        qq.clear();
      } 
      if (command.startsWith("OFF")) { // OFF 신호 처리
        golf_operate = false;
        Serial.println("Operation stopped");
      // }

      // if (command.startsWith("DATA_REQUEST")) { // 데이터 요청 처리
      //   golf_operate = false;
      //   Serial.println("Data request received");

        int delaytime = 1000 + 3000*(SLAVEID-1);
        delay(delaytime);
        // client.println("Data request received");
        // delay(600);
        
        Serial.println("Send Signal");
        client.write("Slave ID : ");
        client.print(SLAVEID); client.write("  ");

        String dataToSend;
        for(int i = 0; i < qq.size(); i++) {
          dataToSend += String(qq[i], 2) + ",";
        }

        // // Remove the 가장 마지막의 "," 
        // dataToSend = dataToSend.substring(0, dataToSend.length()-1);

        client.print(dataToSend);        
        client.println("END!!!");
        qq.clear();
      } 
    }


    if (golf_operate){
      MPU_operate();

      now=millis();
      while (now - past <= 20) {
        now = millis();
      }
      Serial.print("\t"); Serial.println(now-past); 
    }



  } else {
    Serial.println("Disconnected from server");
    while (!client.connect("192,168.4.1", 80)) {
      delay(1000);
      Serial.println("Reconnecting to Server...");
    }
    Serial.println("Reconnected to Server");
  }
}

void MPU_operate(){
  mpu.update(0);

  qq.push_back(mpu.getQuaternionX());
  qq.push_back(mpu.getQuaternionY());
  qq.push_back(mpu.getQuaternionZ());
  qq.push_back(mpu.getQuaternionW());
}
