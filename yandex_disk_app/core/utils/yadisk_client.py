import requests
from typing import Dict

YANDEX_DISK_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"


class YandexDiskClient:
    """
    Класс клиента для взаимодействия с API Яндекс.Диска.
    """

    def __init__(self, public_key: str):
        """
        Инициализация клиента с публичной ссылкой.
        :param public_key: Публичная ссылка на ресурсы Яндекс.Диска.
        """
        self.public_key = public_key

    def get_resources(self) -> Dict:
        """
        Получение списка ресурсов по публичной ссылке.
        :return: Словарь с данными о ресурсах.
        """
        params = {
            'public_key': self.public_key
        }
        response = requests.get(YANDEX_DISK_API_URL, params=params)
        response.raise_for_status()
        return response.json()

    def download_file(self, file_url: str) -> bytes:
        """
        Скачивание файла по URL.
        :param file_url: Прямая ссылка на файл.
        :return: Содержимое файла в байтах.
        """
        response = requests.get(file_url)
        response.raise_for_status()
        return response.content

    def stream_file(self, file_url: str):
        """
        Возвращает поток ответа при скачивании файла по URL.
        :param file_url: Прямая ссылка на файл.
        :return: Поток ответа requests.
        """
        response = requests.get(file_url, stream=True)
        response.raise_for_status()
        return response
