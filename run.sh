#!/bin/bash

# Скрипт запуска приложения insurance.py 
# вместе с созданием виртуального окружения
# и автоустановкой зависимостей

cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# Проверка установки Python
if ! command -v python3 &> /dev/null
then
    echo "Python не установлен. Пожалуйста, установите Python и попробуйте снова."
    echo "sudo apt install python3"
    exit 1
fi

# Проверка установки pip
if ! python3 -m pip --version &> /dev/null
then
    echo "pip не установлен. Пожалуйста, установите pip и попробуйте снова."
    echo "sudo apt install python3-pip"
    exit 1
fi

# Проверка установки модуля venv
if ! python3 -m venv --help &> /dev/null
then
    echo "Модуль venv не установлен. Пожалуйста, установите Python с поддержкой venv и попробуйте снова."
    echo "sudo apt install python3-venv"
    exit 1
fi

# Создание виртуального окружения
if ! command -v env/bin/python &> /dev/null
then
    echo "Создание виртуального окружения..."
    if ! python3 -m venv env
    then
        echo "Произошла ошибка при создании виртуального окружения."
        exit 1
    fi
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
. env/bin/activate

# Установка зависимостей
echo "Проверка зависимостей..."
while read p; do
  package_name=$(echo $p | tr '==' ' ' | awk '{print $1}' | tr -d '-')
  test_package=$(python -c "import $package_name" &>/dev/null && echo 0)
  if [ "$test_package" != 0 ]
  then
    echo "Установка $p ..." 
    python -m pip install $p &>/dev/null
  fi
done <requirements.txt


# Права на запуск
chmod +x ./insurance.py

# Запуск
python3 ./insurance.py