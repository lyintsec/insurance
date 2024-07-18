# Insurance

![ins2](https://github.com/user-attachments/assets/3bb3514f-f18b-47e7-9b45-50413c204eae)

## Обзор
Insurance - кроссплатформенное python приложение (Windows и Linux), отложенная отправка email по таймеру.

## Особенности
- Возможность запускать в режиме --daemon для привязки к screen или systemd
- Возможность шифрования пароля для хранения в файле конфигурации
- Возможность прикреплять файлы для отправки нескольким адресатам
- Цветовая индикация запущенного таймера

## Зависимости
Протестировано на версиях Python 3.9.2
- `prompt_toolkit==3.0.47`
- `console-menu==0.8.0`
- `colorama==0.4.6`
- `cryptography==42.0.8`

## Установка и запуск
Скачайте репозиторий вручную или через командную строку
```bash
git clone https://github.com/lyintsec/insurance.git
```
На linux запустите `run.sh` для автоустановки и запуска приложения
Либо установите вручную
```bash
# Создание виртуального окружения
python3 -m venv env

# Активация виртуального окружения
. env/bin/activate

# Установка зависимостей
python -m pip install -r requirements.txt

# Запуск приложения
python insurance.py
```

