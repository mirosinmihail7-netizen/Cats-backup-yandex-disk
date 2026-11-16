import json
import logging
from urllib.parse import quote

import requests

GROUP_NAME = "QAPY-144"

CAT_API_URL = "https://cataas.com/cat/cute/says/{text}"
YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/resources"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_cat_image(text: str) -> bytes:
    url = CAT_API_URL.format(text=quote(text))
    logger.info("Запрос изображения: %s", url)

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"Ожидалось изображение, получено: {content_type}")

    logger.info("Изображение получено, размер: %d байт", len(response.content))
    return response.content


def create_yandex_folder(token: str, folder_name: str) -> None:
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": folder_name}

    logger.info("Создание папки: %s", folder_name)
    response = requests.put(
        YANDEX_API_URL,
        headers=headers,
        params=params,
        timeout=30,
    )

    if response.status_code not in (201, 409):
        response.raise_for_status()

    logger.info("Папка готова: %s", folder_name)


def get_upload_url(token: str, remote_path: str) -> str:
    headers = {"Authorization": f"OAuth {token}"}
    params = {
        "path": remote_path,
        "overwrite": "true",
    }

    logger.info("Получение ссылки для загрузки: %s", remote_path)
    response = requests.get(
        f"{YANDEX_API_URL}/upload",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    upload_url = response.json()["href"]
    logger.info("Ссылка для загрузки получена")
    return upload_url


def upload_image(upload_url: str, image: bytes) -> None:
    logger.info("Загрузка изображения на Яндекс.Диск")
    response = requests.put(upload_url, data=image, timeout=60)
    response.raise_for_status()
    logger.info("Изображение загружено")


def make_filename(text: str) -> str:
    forbidden = '<>:"/\\|?*'
    safe_text = "".join(
        "_" if symbol in forbidden else symbol
        for symbol in text
    ).strip()
    return f"{safe_text or 'cat'}.jpg"


def save_result(data: dict, filename: str = "upload_info.json") -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    logger.info("Информация сохранена в %s", filename)


def main() -> None:
    text = input("Введите текст для картинки: ").strip()
    token = input("Введите OAuth-токен Яндекс.Диска: ").strip()

    if not text or not token:
        raise ValueError("Текст и токен должны быть непустыми.")

    image = get_cat_image(text)
    filename = make_filename(text)
    remote_path = f"disk:/{GROUP_NAME}/{filename}"

    create_yandex_folder(token, GROUP_NAME)
    upload_url = get_upload_url(token, remote_path)
    upload_image(upload_url, image)

    result = {
        "file_name": filename,
        "size": len(image),
        "yandex_disk_path": remote_path,
        "source_url": CAT_API_URL.format(text=quote(text)),
    }
    save_result(result)


if __name__ == "__main__":
    main()
