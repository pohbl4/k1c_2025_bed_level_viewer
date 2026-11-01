# Bed Map

Read-only bed mesh viewer for Creality K1C and other printers exposing the Klipper-compatible bed mesh API at port `7125`.

## Requirements

- Windows 10 or 11, Python 3.10 or newer
- Local network access to your printer's API
- Python packages from `requirements.txt` (the launcher installs them if missing)

## Start on Windows

1. Install Python 3.10+ from https://www.python.org/downloads/windows/ . Choose **Add Python to PATH** during setup.
2. Extract the ZIP and double-click `START_WINDOWS.bat`.
3. Enter **only the IP address** of your printer, for example `192.168.0.0` (no URL and no port).
4. Select **Load map**. The application uses port `7125` automatically.
5. Click **Instructions** for the full preparation and Auto Leveling procedure.

To run it manually:

```powershell
py -3 -m pip install -r requirements.txt
py -3 bed_map.py
```

## Features

- Color map: red = higher, blue = lower. Rear at the top, front at the bottom.
- Minimum, maximum and range calculated from `probed_matrix` (measured points).
- Smooth visualization of `mesh_matrix` (interpolated values).
- Opens saved API responses from JSON and saves the current image as PNG and source data as JSON.
- English and Russian UI, including chart labels, alerts and instructions.
- API endpoint: `http://PRINTER_IP:7125/printer/objects/query?bed_mesh`.
- Read-only: no G-code, printer movement or bed leveling commands are sent.

## Important

Loading a map does **not** trigger a new calibration. Run Auto Leveling using the printer's screen first. The app may show a saved but inactive mesh profile if no active map exists.

If connection fails, confirm that the printer and computer can reach each other on the same network, that the printer IP is correct, and that the API is available on port 7125.

---
## RUS
---

# Карта стола

Приложение для просмотра карты высот стола Creality K1C и других 3D-принтеров, предоставляющих доступ к Klipper-совместимому API на порту `7125`. Работает только в режиме чтения.

## Требования

- Windows 10 или 11, Python 3.10 или новее.
- Доступ к API принтера по локальной сети.
- Python-библиотеки из `requirements.txt` (при необходимости установщик загрузит их автоматически).

## Запуск на Windows

1. Установите Python 3.10 или новее с сайта [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/). Во время установки выберите **Add Python to PATH**.
2. Распакуйте ZIP-архив и дважды щёлкните по файлу `START_WINDOWS.bat`.
3. Введите **только IP-адрес** вашего принтера, например `192.168.0.0` (без URL и порта).
4. Нажмите **Load map / Загрузить карту**. Приложение автоматически использует порт `7125`.
5. Нажмите **Instructions / Инструкция**, чтобы открыть полное руководство по подготовке и автоматическому выравниванию стола.

Для ручного запуска:

```powershell
py -3 -m pip install -r requirements.txt
py -3 bed_map.py
```

## Возможности

- Цветная карта высот: красный — выше, синий — ниже. Задняя часть стола отображается сверху, передняя — снизу.
- Минимальная, максимальная высота и общий перепад рассчитываются по `probed_matrix` (измеренные точки).
- Сглаженная визуализация `mesh_matrix` (интерполированные значения).
- Открытие сохранённых ответов API из JSON, сохранение текущей карты в PNG и исходных данных в JSON.
- Английский и русский интерфейс, включая подписи графика, уведомления и инструкции.
- Адрес API: `http://PRINTER_IP:7125/printer/objects/query?bed_mesh`.
- Режим только для чтения: приложение не отправляет G-code, команды перемещения принтера или выравнивания стола.

## Важно

Загрузка карты **не запускает новую калибровку**. Сначала выполните автоматическое выравнивание стола (Auto Leveling) через экран принтера. Если активная карта отсутствует, приложение может отобразить сохранённый, но неактивный профиль.

Если подключение не удаётся, убедитесь, что принтер и компьютер доступны друг другу в одной сети, IP-адрес принтера указан правильно, а API доступен на порту `7125`.