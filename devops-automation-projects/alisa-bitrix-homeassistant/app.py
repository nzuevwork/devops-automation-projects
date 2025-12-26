from flask import Flask, request, jsonify
import logging
import os
import json
import requests
import sys
from urllib.parse import parse_qs

app = Flask(__name__)

# Логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Путь к сертификатам
cert_file = 'certificate.crt'
key_file = 'private.key'

# Проверка наличия файлов сертификатов
if not os.path.isfile(cert_file):
    raise FileNotFoundError(f"Файл сертификата не найден: {cert_file}")
if not os.path.isfile(key_file):
    raise FileNotFoundError(f"Файл ключа не найден: {key_file}")

# Переменные для подключения к Home Assistant
ha_url = 'http://**:8123'  # URL Home Assistant
ha_token = 'token'  # Ваш токен
yandex_stations = [
    'media_player.yandex_station_l00925000rjsrb',  # Цоколь
    'media_player.yandex_station_l00n4ba0092s2g',  # Ресепшен
    'media_player.yandex_station_l00dbea00be2mg',  # Второй этаж
    'media_player.yandex_station_l008cea00h1rwg',  # Астана
    'media_player.yandex_station_l001ja300jkkab',  # Алмата
]  # Добавьте все устройства сюда
siri_id = 'media_player.siri'  # ID устройства Siri

# Функция для отправки сообщения на колонку через Home Assistant
def send_tts_message(message, target_devices, service="cloud_say"):
    """Отправка TTS-сообщения на устройства через Home Assistant."""
    for device in target_devices:
        try:
            url = f"{ha_url}/api/services/tts/{service}"
            headers = {
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "entity_id": device,
                "message": message
            }
            logging.debug(f"Отправка TTS сообщения на {device} с сервисом {service}")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logging.info(f"Сообщение '{message}' успешно отправлено на {device}.")
            else:
                logging.error(f"Ошибка при отправке сообщения на {device}: {response.status_code} - {response.text}")
                restart_application()  # Перезапуск приложения в случае ошибки
        except Exception as e:
            logging.error(f"Ошибка при выполнении запроса: {e}")
            restart_application()  # Перезапуск приложения в случае ошибки

def restart_application():
    """Перезапуск приложения при возникновении ошибки."""
    logging.info("Ошибка при отправке сообщения. Перезапуск приложения...")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Логирование всех входящих запросов
@app.before_request
def log_request_info():
    logging.debug(f"Method: {request.method}")
    logging.debug(f"Headers: {request.headers}")
    logging.debug(f"Body: {request.get_data(as_text=True)}")

# Вебхук для обработки запросов от Bitrix24
@app.route('/bitrix', methods=['POST'])
def bitrix_webhook():
    try:
        # Получаем все данные (независимо от типа содержимого)
        data = request.get_data(as_text=True)
        logging.debug(f"Получены данные от Bitrix24: {data}")

        # Преобразуем данные в словарь
        if data:
            # Проверяем, если данные имеют формат URL-кодированных данных
            if data.startswith("document_id"):
                # Преобразуем данные из URL-кодированного формата в словарь
                data_dict = parse_qs(data)
                logging.debug(f"Преобразованные URL-кодированные данные: {data_dict}")
            else:
                # Пример, если пришли JSON данные
                try:
                    data_dict = json.loads(data)
                    logging.debug(f"Преобразованные JSON данные: {data_dict}")
                except json.JSONDecodeError:
                    data_dict = {'error': 'Invalid JSON'}
                    logging.warning(f"Ошибка в формате JSON: {data}")
        else:
            data_dict = {'error': 'No data received'}
            logging.warning(f"Нет данных в запросе: {data}")

        # Независимо от содержимого запроса всегда отправляем сообщение "Оплата получена"
        tts_message = "Совершена новая сделка."
        logging.info(f"Совершена новая сделка.")
        
        # Отправляем сообщение на все Яндекс.Станции и на Siri
        send_tts_message(tts_message, yandex_stations, service="cloud_say")  # Яндекс.Станции
        send_tts_message(tts_message, [siri_id], service="cloud_say")  # Siri

        # Формируем ответ для Яндекс.Алисы
        return jsonify({
            'response': {
                'text': "Совершена новая сделка",
                'tts': tts_message
            },
            'session': {
                'session_id': 'default_session',
                'user_id': 'default_user'
            },
            'version': '1.0'
        }), 200

    except Exception as e:
        logging.error(f"Произошла ошибка при обработке запроса от Bitrix24: {e}")
        return jsonify({
            'response': {
                'text': "Произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
            }
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=(cert_file, key_file))
