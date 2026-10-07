import asyncio
import json
import os

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")     # nom du service Docker
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "backend")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_CA = os.getenv("MQTT_CA", "/certs/ca.crt")

_client = None


def start(loop: asyncio.AbstractEventLoop, on_reading):
    global _client

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sentinel-api")
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set(ca_certs=MQTT_CA)          # vérifie le certificat du broker

    def on_connect(c, userdata, flags, reason_code, properties):
        print(f"[MQTT] connecte : {reason_code}")
        c.subscribe("sentinel/sensors/#", qos=1)

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except ValueError:
            print(f"[MQTT] JSON invalide sur {msg.topic}")
            return
        asyncio.run_coroutine_threadsafe(on_reading(data), loop)

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect_async(MQTT_HOST, MQTT_PORT)   # ne bloque pas le démarrage de l'API
    client.loop_start()
    _client = client


def stop():
    if _client:
        _client.loop_stop()
        _client.disconnect()


def publish_command(device_id: str, command: dict) -> bool:
    if _client is None or not _client.is_connected():
        return False
    info = _client.publish(f"sentinel/commands/{device_id}", json.dumps(command), qos=1)
    return info.rc == mqtt.MQTT_ERR_SUCCESS