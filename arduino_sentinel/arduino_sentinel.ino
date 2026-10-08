#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <time.h>

// ================= A MODIFIER =================
const char* WIFI_SSID = "MATHIS"; // ← ton nom de Wi-Fi
const char* WIFI_PASS = "U6xrQ3R5vcyBzu"; // ← ton mot de passe
const char*    MQTT_HOST  = "192.168.137.1";   // IP du PC sur CE reseau (ipconfig)
const uint16_t MQTT_PORT  = 8883;
const char*    MQTT_USER  = "esp8266";
const char*    MQTT_PASS  = "Workshop";
const char*    DEVICE_ID  = "SX-001";
const char*    NTP_SERVER = "pool.ntp.org";
const char* mqtt_topic = "api/commands";

#define USE_CA_CERT 0     // 0 = TLS sans verifier le certificat (tests) ; 1 = verifie (demo)

#if USE_CA_CERT
static const char CA_CERT[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDF00NHpJND6zjn
1MSd2MzzvNB+QqDXVbqBRW11+ROaOoOMrW7UfCuVj2G5d8SKBEBJOvGUxcztgeNQ
/ZFj9dIm+e2wuXe4BgwfPhNdmneXZtFVPHtswoMoTRGk/Kb7npIQmVPwoeE1lfWQ
BAQxxrHGDij8lKELT/lQklYCKaxKuVxJ9F9pyRjt7Ey8rlUlCp7rupOajpwHftUW
yf1h3dYLI+Ax+merOlKjoseOGyHz7VbuHD/XAJ6GjWM1ZauHJuT74wwGplTc2+rv
/IyChBA6zp3H4rjKTKV6Zdt8jv0jB1WS7E1RJzhbsLLO6DVNVQI0RSSIqXZno9kZ
2kso/6IBAgMBAAECggEABNOdvZ6/VRXlIornbS5/+aZus9XuVLKrxUGrZQh5uPaa
hREqNhb9fT2tVbgdXHy0ENVWVZnp4RWdNTmqlXTG9tp8OSadTCkhnJWIJW2CY3hH
vTuni0THrHEM8CiV7me1CqCjEqjwdL0+64+dhpVhewKXb2o077C41YVsgcsAgCYw
lyL16fAPmGT9DEIhUxLMZ5fUeX4q2FEEU8AxRI8VYFtinDhg9B+/HLLoAv5M/2jx
CvUSQyHupIYTIRlXVz/zbzRccSpawUiKGkTJz/DCVv1iEMtGzb8P7/g4DavxNxS9
/MmrbfPCMrrTrct9Q+nsdeLaeXHtTzwEKYSK13qSvQKBgQD5aEw6nziBiuC7BHqn
trgLwB1tTqXiYnvenZ8w11XfCFxe/XHC/NEhGfv+bCIssNxbTyWzdLOwd5H5aImE
UPVAGeftQOegF82EPbt1Q4pdgbuoWTtROVdAkekcXCW9SkQ98f9hbm1XQ4cM5sFE
nJUIX1Nh5nLaO2X9MrDBWQ2MtwKBgQDLDeqTwcNq911PPQ5w4Woxclcszxaeq5kI
mhCKI7DM/n6qGAmn9oECt5jnP2GBPFoTffbVW2KUVFnEjJWjg8u1/RISM0k0lmuE
gXDyoGKE0H43hnQ8p9/U0CCGd/yPQKyB2afiLhplQkPWzESMkDgmsLYlNR70XLMm
GpoH975/BwKBgH+vdddNTJCFmSgl0uWqFe9uG6KqcSLFaMU/zRAkLkJQ9XlsJ6G7
7RUVSH2ovpZCtY3Jp3OIe7YMgR8+9ahYCjcXDDXa1LqRdRYOxLn0KhJVKM23YTbk
NFdKXB24z1lpfCZ6jlRDRJc4axufx7Jot6Phqb6lTIeNgVlvai6SeO1hAoGBALls
yOULUW/x2kTM5c4RGs9yscbaibZ1zzb6sdXkB8T7NiIP92lpgqA/lqK9z0WcHkmk
gu6NGDWJ3bvOAawjY7iaFJGIQfaC0kZbihAWhEDyv//miWkGiDEnqjwBgCI1FhMx
9sxl+3ayj46sVIDkBlLWlk7d9pmBuZs3OafDBjOrAoGAXtepX/jI4D0jWj+k27nF
gyGesNWtWxprkLqVMlVyUmBLBpVE1d2TxM/jZyzpENb6l1ggLI3oNbPa+H50Zl6C
5KQHL8e04gOZqA4R2YHRQLbFX/4BN7paWQFB+STSVux7oSut3+cJJxOYGhbDgMFn
86tie7e+S+OZSHxzxeUVrUg=
-----END CERTIFICATE-----
)EOF";
BearSSL::X509List caList(CA_CERT);
#endif
// ==============================================

#define BUZZER_PIN D7
#define PIR_PIN    D4
#define LED_PIN    D0
#define GAS_PIN    A0

const uint32_t SENSOR_PERIOD_MS  = 2000;    // le DHT22 ne se lit pas plus vite
const uint32_t PUBLISH_PERIOD_MS = 5000;
const uint32_t DISPLAY_PERIOD_MS = 500;
const uint32_t MQTT_RETRY_MS     = 5000;
const uint32_t MQ2_PREHEAT_MS    = 120000;  // 2 min

DHT dht(D5, DHT22);
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
BearSSL::WiFiClientSecure net;
PubSubClient mqtt(net);

char topicSensors[48];
char topicCmd[48];

// ---------- Etat ----------
float t = NAN, h = NAN;
int   gas = 0;
bool  dhtOk = false, gasReady = false, oledOk = false;
int   motion = 0, lastMotion = 0;
uint32_t seq = 0;
uint32_t lastSensorMs = 0, lastPublishMs = 0, lastDisplayMs = 0, lastMqttTryMs = 0;

struct Actuator {
  uint8_t pin;
  bool on;
  uint32_t offAt;
};

Actuator buzzer = { BUZZER_PIN, false, 0 };
Actuator led    = { LED_PIN, false, 0 };

// ---------- Actionneurs (sans delay) ----------
void setActuator(Actuator& a, bool state, uint32_t durationMs) {

  a.on = state;

  if (&a == &buzzer) {
    // Buzzer : génération d'une fréquence
    if (state) {
      tone(a.pin, 1000);  // 1000 Hz
    } else {
      noTone(a.pin);
    }
  } 
  else {
    // LED : simple ON/OFF
    digitalWrite(a.pin, state ? HIGH : LOW);
  }

  a.offAt = (state && durationMs > 0)
              ? millis() + durationMs
              : 0;
}

void updateActuator(Actuator& a) {

  if (a.on && a.offAt != 0 &&
      (int32_t)(millis() - a.offAt) >= 0) {

    setActuator(a, false, 0);
  }
}

// ---------- Commandes recues de l'API ----------
void onMessage(char* topic, byte* payload, unsigned int length) {
  JsonDocument doc;
  if (deserializeJson(doc, payload, length)) {
    Serial.println("Commande ignoree : JSON invalide");
    return;
  }
  const char* target = doc["target"] | "";
  bool state         = doc["state"] | false;
  uint32_t duration  = doc["duration_ms"] | 0;

  if (strcmp(target, "buzzer") == 0)   setActuator(buzzer, state, duration);
  else if (strcmp(target, "led") == 0) setActuator(led, state, duration);
  else { Serial.printf("Commande ignoree : cible \"%s\"\n", target); return; }
  Serial.printf("Commande : %s -> %s (%u ms)\n", target, state ? "ON" : "OFF", duration);
}

// ---------- Capteurs ----------
void readSensors() {
  h = dht.readHumidity();
  t = dht.readTemperature();
  dhtOk = !(isnan(h) || isnan(t));

  long sum = 0;                                   // moyenne : l'ADC de l'ESP8266 est bruite
  for (int i = 0; i < 10; i++) { sum += analogRead(GAS_PIN); delay(2); }
  gas = sum / 10;
  gasReady = millis() >= MQ2_PREHEAT_MS;
}

// ---------- Publication MQTT ----------
void publishReading() {
  JsonDocument doc;
  doc["v"]        = 1;
  doc["id"]       = DEVICE_ID;
  doc["uptime_s"] = millis() / 1000;
  doc["seq"]      = seq++;
  doc["valid"]    = dhtOk;
  if (dhtOk) {
    doc["temp_c"]       = roundf(t * 10) / 10;
    doc["humidity_pct"] = roundf(h * 10) / 10;
  }
  if (gasReady) doc["gas_raw"] = gas;
  doc["motion"] = (bool)motion;

  char buf[256];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  bool ok = mqtt.publish(topicSensors, (const uint8_t*)buf, n, false);
  Serial.printf("PUB %s heap=%u : %s\n", ok ? "ok" : "ECHEC", ESP.getFreeHeap(), buf);
  lastPublishMs = millis();
}

// ---------- Connexion MQTT ----------
void tryMqttConnect() {
#if USE_CA_CERT
  if (time(nullptr) < 1700000000) {
    Serial.println("Heure NTP pas encore recue (necessaire pour verifier le certificat)");
    return;
  }
#endif
  char clientId[32];
  snprintf(clientId, sizeof(clientId), "sentinel-%s", DEVICE_ID);
  Serial.printf("Connexion MQTT a %s:%u ... ", MQTT_HOST, MQTT_PORT);
  if (mqtt.connect(clientId, MQTT_USER, MQTT_PASS)) {
    Serial.println("OK");
    mqtt.subscribe(topicCmd);
  } else {
    Serial.printf("echec (code %d : -2 reseau/TLS, 4 ou 5 identifiants)\n", mqtt.state());
  }
}

// ---------- Ecran ----------
void updateDisplay() {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextColor(WHITE);
  oled.setTextSize(1); oled.setCursor(0, 0);
  oled.println("SENTINEL-X  SX-001");
  oled.drawLine(0, 10, 127, 10, WHITE);
  oled.setCursor(0, 16);
  if (dhtOk) {
    oled.printf("Temp : %.1f C\n", t);
    oled.printf("Hum  : %.0f %%\n", h);
  } else {
    oled.print("Temp : --\nHum  : --\n");
  }
  if (gasReady) oled.printf("Gaz  : %d\n", gas);
  else          oled.printf("Gaz  : chauffe %us\n", (MQ2_PREHEAT_MS - millis()) / 1000);

  oled.setCursor(0, 39);
  oled.printf("WiFi:%s MQTT:%s", WiFi.status() == WL_CONNECTED ? "OK" : "--",
              mqtt.connected() ? "OK" : "--");

  oled.setTextSize(2); oled.setCursor(0, 48);
  oled.display();
}

bool i2cPresent(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

// ---------- Setup / loop ----------
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\nSENTINEL-X demarrage");
  Serial.println("MQ-2 : chauffe 2-3 min avant d'avoir des valeurs stables");

  pinMode(BUZZER_PIN, OUTPUT); digitalWrite(BUZZER_PIN, LOW);
  pinMode(LED_PIN, OUTPUT);    digitalWrite(LED_PIN, LOW);
  pinMode(PIR_PIN, INPUT);

  snprintf(topicSensors, sizeof(topicSensors), "sentinel/sensors/%s", DEVICE_ID);
  snprintf(topicCmd,     sizeof(topicCmd),     "sentinel/commands/%s", DEVICE_ID);

  Wire.begin(D2, D1);
  dht.begin();
  oledOk = i2cPresent(0x3C) && oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  Serial.println(oledOk ? "OLED OK" : "OLED non detecte (on continue sans ecran)");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);           // connexion en arriere-plan
  configTime(0, 0, NTP_SERVER);               // heure UTC (necessaire pour valider le certificat)

#if USE_CA_CERT
  net.setTrustAnchors(&caList);
#else
  net.setInsecure();                          // TESTS UNIQUEMENT
#endif
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMessage);
  mqtt.setBufferSize(512);
}

void loop() {
  uint32_t now = millis();

  updateActuator(buzzer);
  updateActuator(led);

  if (WiFi.status() == WL_CONNECTED) {
    if (mqtt.connected()) {
      mqtt.loop();
    } else if (now - lastMqttTryMs >= MQTT_RETRY_MS) {
      lastMqttTryMs = now;
      tryMqttConnect();
    }
  }
  
  // PIR : LED allumée uniquement lorsqu'il y a du mouvement
  motion = digitalRead(PIR_PIN);
  
  if (motion != lastMotion) {

    if (motion == HIGH) {
      Serial.println(">>> MOUVEMENT DETECTE");
    } else {
      Serial.println(">>> PLUS DE MOUVEMENT");
    }

    if (mqtt.connected()) {
      publishReading();
    }

    lastMotion = motion;
  }

  if (now - lastSensorMs >= SENSOR_PERIOD_MS) {
    lastSensorMs = now;
    readSensors();

    Serial.printf(
      "Temp: %.1f C | Hum: %.1f %% | Gaz: %d | Mvt: %d\n",
      t, h, gas, motion
    );
  }

  if (mqtt.connected() && now - lastPublishMs >= PUBLISH_PERIOD_MS) {
    publishReading();
  }

  if (now - lastDisplayMs >= DISPLAY_PERIOD_MS) {
    lastDisplayMs = now;
    updateDisplay();
  }
}