############################################################################
#
## Copyright 2024 lyint
##
## Лицензия Apache версии 2.0 («Лицензия»);
## вы не можете использовать этот файл, кроме как в соответствии с Лицензией.
## Вы можете получить копию Лицензии по адресу
##
## https://www.apache.org/licenses/LICENSE-2.0
##
## Если это не требуется действующим законодательством или не согласовано 
## в письменной форме, программное обеспечение распространяется по Лицензии,
## распространяется на условиях «КАК ЕСТЬ»,
## БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ ИЛИ УСЛОВИЙ, явных или подразумеваемых.
## См. лицензию для конкретного языка, регулирующего разрешения и
## ограничения по Лицензии.
##
############################################################################

"""
Проект: Insurance
Автор: lyintSec
Github: https://github.com/lyintsec/remotron
Версия: 1.0
Дата обновления: 18 июля 2024
Описание: Отложенная отправка email по таймеру

Зависимости:
prompt_toolkit==3.0.47
console-menu==0.8.0
colorama==0.4.6
cryptography==42.0.8
"""

import os
import sys
import time
import signal
import json
import threading
import asyncio
import argparse
from datetime import datetime as dt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from prompt_toolkit import print_formatted_text, PromptSession, HTML
from prompt_toolkit.application.current import get_app
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import get_app
from consolemenu import ConsoleMenu, SelectionMenu
from consolemenu.items import FunctionItem
from cryptography.fernet import Fernet
from colorama import init
from colorama import Fore, Back, Style

# Инициализация Colorama
init(autoreset=True)

# Форматирование справки командной строки
class CustomHelpFormatter(argparse.HelpFormatter):
    """
    Для кастомного форматирования справки командной строки, 
    который будет использоваться в argparse.
    """
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = 'Использование: '
        return super().add_usage(usage, actions, groups, prefix)
    
    def format_help(self):
        help_text = (
            '===============================================\n'
            'Проект: Insurance\n'
            'Автор: lyint\n'
            'github: github.com/lyintsec\n'
            'Описание: Отложенная отправка email по таймеру\n'
            'Лицензия: Apache 2.0\n'
            '===============================================\n\n'
        )
        help_text += super().format_help()
        help_text = help_text.replace('optional arguments:', 'Необязательные аргументы:')
        return help_text

    def add_argument(self, action):
        if action.option_strings == ['-h', '--help']:
            action.help = 'Вывести это справочное сообщение'
        super().add_argument(action)

# Функции для работы с файлом конфигурации
def load_configuration():
    """
    Загружает конфигурацию из файла или создает файл конфигурации 
    со стандартными значениями, если файл не существует.
    """
    
    global configuration

    # Дефолтная конфигурация для заполнения в файл
    default_configuration = {
        'duration': 86400,  # длительность таймера в секундах
        'sender': 'your_email@gmail.com', # Email отправителя
        'recipients': ['info@example.com', 'info2@example.com'], # Список получателей
        'subject': 'Важное сообщение', # Тема письма
        'body': 'Текст важного сообщения', # Текст письма
        'attachments': [], # Список прикрепленных файлов
        'server': 'smtp.gmail.com', # smpt сервер
        'port': 587, # smpt порт
        'username': 'your_email@gmail.com', # smpt логин
        'password': '', # smpt пароль
        'test_email': 'test@gmail.com', # тестовый email для тестового письма
        'configuration_names': { # Человеческие наименования параметров для ототбражения
            'duration': 'Длительность',
            'sender': 'Отправитель',
            'recipients': 'Получатели',
            'subject': 'Тема письма',
            'body': 'Текст письма',
            'attachments': 'Прикрепленные файлы',
            'server': 'SMTP сервер',
            'port': 'SMTP порт',
            'username': 'SMTP логин',
            'password': 'SMTP пароль',
            'test_email': 'Тестовый email',
        }
    }

    # Если есть файл конфигурации, то загружаем его
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf8') as file:
                configuration = json.load(file)
                    
        # Если во время загрузки json произошла ошибка
        except Exception as e:
            # Делаем бэкап файла
            datestamp = dt.now().strftime('%d%m%Y%H%M%S')
            backup_CONFIG_FILE = f"{CONFIG_FILE}.bkp{datestamp}"
            os.rename(CONFIG_FILE, backup_CONFIG_FILE)

            # Сохраняем в файо дефолтную конфигурацию
            configuration = default_configuration
            save_configuration()

            print(
                (
                    f'\n{Fore.RED}Ваш файл конфигурации сломан. Приложение создало новый дефолтный конфиг.{Style.RESET_ALL}\n'
                    f'{Fore.RED}Предыдущий конфиг переименован в {Style.RESET_ALL}{backup_CONFIG_FILE}\n'
                    f'{Fore.RED}Исправьте его вручную или заполните конфиг заново{Style.RESET_ALL}\n'
                    f'{Fore.RED}Подробный текст ошибки: {e}{Style.RESET_ALL}'
                )
            )
    else:
        # Если файла конфигурации не существует, заполняем дефолтом
        configuration = default_configuration
        save_configuration()

def save_configuration():
    """
    Сохраняет текущую конфигурацию в файл.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf8') as file:
            json.dump(configuration, file, indent=4, ensure_ascii=False)
            return True
    except Exception as e:
        print_formatted_text(HTML(f"\n<ansired>Ошбика при сохранении конфига: {e}</ansired>"))
        return False

def print_config():
    """
    Вывод текущей конфигурации в консоль
    """
    config = "\nТекущая конфигурация:\n"
    for key, value in configuration["configuration_names"].items():
        # Красивое отображение длительности
        if key == 'duration':
            if not configuration[key]:
                config += f'{configuration["configuration_names"][key]}: {Fore.RED}-{Style.RESET_ALL}\n' 
            else:
                config += (
                    f'{configuration["configuration_names"][key]}: '
                    f'{Fore.GREEN}{configuration[key]} сек. '
                    f'({format_time(int(configuration[key]))}){Style.RESET_ALL}\n'
                )
        # Превращаем список в последовательность значений
        elif key == 'recipients' or key == 'attachments':
            if not configuration[key]:
                config += f'{configuration["configuration_names"][key]}: {Fore.RED}-{Style.RESET_ALL}\n' 
            else:
                config += f'{configuration["configuration_names"][key]}: {Fore.GREEN}{", ".join(configuration[key])}{Style.RESET_ALL}\n'
                
        # Прикрываем пароль
        elif key == 'password':
            password_lenght = get_lenght_of_decrypted_password(configuration[key], CRYPT_KEY)
            if password_lenght > 0:
                config += (
                    f'{configuration["configuration_names"][key]}: '
                    f'{Fore.GREEN}{"*" * get_lenght_of_decrypted_password(configuration[key], CRYPT_KEY)}{Style.RESET_ALL}\n'
                )
            else:
                config += f'{configuration["configuration_names"][key]}: {Fore.RED}-{Style.RESET_ALL}\n'
        else:
            if not configuration[key]:
                config += f'{configuration["configuration_names"][key]}: {Fore.RED}-{Style.RESET_ALL}\n' 
            else:
                config += f'{configuration["configuration_names"][key]}: {Fore.GREEN}{configuration[key]}{Style.RESET_ALL}\n'

    return config

# Функции для работы с шифрованием
def generate_key(KEY_FILE):
    """
    Генерируем ключ для шифрования пароля
    """
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as file:
            file.write(key)

def load_key(KEY_FILE):
    """
    Загружаем ключ для шифрования пароля
    """
    if os.path.exists(KEY_FILE):
        return open(KEY_FILE, "rb").read()
    else:
        return None

def encrypt_password(password, key):
    """
    Шифрование пароля
    """
    fernet = Fernet(key)
    encrypted_password = fernet.encrypt(password.encode())
    return encrypted_password.decode()

def decrypt_password(encrypted_password, key):
    """
    Дешифрование пароля
    """
    if encrypted_password.strip() != '':
        try:
            fernet = Fernet(key)
            decrypted_password = fernet.decrypt(encrypted_password.encode())
            return decrypted_password.decode(), True
        except Exception as e:
            if encrypted_password.strip() != '':
                print(f'Ошибка расшифровки пароля {e}')
            return encrypted_password, False
        
    return '', False

def get_lenght_of_decrypted_password(encrypted_password, key):
    """
    Получение длины расшифрованного пароля
    Используется для определения количества звездочек при печати конфига
    """
    try:
        fernet = Fernet(key)
        decrypted_password = fernet.decrypt(encrypted_password.encode())
        return len(str(decrypted_password.decode()))
    except Exception as e:
        if encrypted_password.strip() != '':
                print(f'Ошибка расшифровки пароля {e}')
        return len(encrypted_password)

# Функции для работы с таймером
def start_timer(duration):
    """
    Запускает таймер на указанное количество секунд.
    По истечению таймера, отправляется email
    
    Args:
        duration (int): Длительность таймера в секундах.
    """
    global timer_running, start_time
    timer_running = True
    start_time = time.time()

    elapsed = 0
    while elapsed < duration and timer_running:
        time.sleep(1)
        elapsed = time.time() - start_time

    if timer_running:
        send_email(configuration['subject'], configuration['body'], configuration['recipients'])
    
    timer_running = False

def start_timer_thread():
    """
    Старт потока таймера
    """
    global timer_thread, update_timer_state, update_thread
    timer_thread = threading.Thread(target=start_timer, args=(configuration['duration'],))
    timer_thread.start()
    print(f"Таймер запущен на {configuration['duration']} секунд ({format_time(configuration['duration'])}).")
    
    if not update_timer_state:
        # Запуск потока для обновления текста
        update_timer_state = True
        update_thread = threading.Thread(target=update_text)
        update_thread.start()

def stop_timer_thread():
    """
    Остановка потока таймера
    """
    global timer_running, timer_thread, update_timer_state, update_thread
    timer_running = False
    timer_thread.join()

    print("Таймер остановлен.")
    update_timer_state = False
    update_thread.join()

def restart_timer_thread():
    """
    Рестарт потока таймера
    """
    global timer_running, timer_thread, update_timer_state, update_thread
    timer_running = False
    timer_thread.join()
    timer_thread = threading.Thread(target=start_timer, args=(configuration['duration'],))
    timer_thread.start()
    if update_timer_state and update_thread.is_alive():
        # Запуск потока для обновления текста
        update_timer_state = False
        update_thread.join()

        update_timer_state = True
        update_thread = threading.Thread(target=update_text)
        update_thread.start()

    print(f"Таймер перезапущен на {configuration['duration']} секунд ({format_time(configuration['duration'])}).")

def get_timer_status():
    """
    Получение текущего статуса таймера
    """
    global timer_thread, start_time
    if timer_thread and timer_thread.is_alive():
        elapsed_time = time.time() - start_time
        remaining_time = max(0, configuration['duration'] - elapsed_time)
        print(f"Таймер работает, осталось {int(remaining_time)} секунд ({format_time(int(remaining_time))}).")
    else:
        print("Таймер не запущен.")

def update_text():
    """
    Обновление состояния таймера внутри input пользователя на главной странице
    """
    global prompt, update_timer_state, start_time

    while update_timer_state:
        time.sleep(1)
        elapsed_time = time.time() - start_time
        remaining_time = max(0, configuration['duration'] - elapsed_time)
        new_text = HTML(f"> INSURANCE[<ansigreen>{int(remaining_time)}</ansigreen>]: ")
        
        # Новый промт
        prompt = new_text

        # временно перенаправляем стандартный вывода
        # для избежания вывода постороннего текста в консоль
        with patch_stdout():
            # Текущее приложение
            app = get_app()
            if app: # Обновляем приложение если оно есть
                app.invalidate()

    update_timer_state = False
    prompt = HTML(f"> INSURANCE[<ansired>OFF</ansired>]: ")

# Дополнительные функции
def help_command():
    """
    Вывод команды help в консоль в обычном режиме
    """
    help_text = (
        'Доступные команды:\n'
        'start    - запустить таймер\n'
        'stop     - остановить таймер\n'
        'restart  - перезапустить таймер\n'
        'status   - проверить состояние таймера\n'
        'config   - просмотр и изменение текущей конфигурации\n'
        'test     - отправить тестовое письмо\n'
        'print    - вывести текущую конфигурацию\n'
        'exit     - выход из программы'
    )
    print(help_text)

def test_command():
    """
    Отправка тестового сообщения на тестовый email
    """
    test_subject = "Тестовое письмо"
    test_body = "Это тестовое письмо для проверки конфигурации."
    send_email(test_subject, test_body, [configuration['test_email']])

def format_time(seconds):
    """
    Форматирует время в человеческом виде (дни, часы, минуты, секунды).
    
    Args:
        seconds (int): Время в секундах.
        
    Returns:
        str: Отформатированная строка времени.
    """
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        if days == 1:
            days_string = 'день'
        elif days == 2 or days == 3 or days == 4:
            days_string = 'дня'
        else:
            days_string = 'дней'
        parts.append(f"{days} {days_string}")
    if hours > 0:
        if hours == 1:
            hours_string = 'час'
        elif hours == 2 or days == 3 or days == 4:
            hours_string = 'часа'
        else:
            hours_string = 'часов'
        parts.append(f"{hours} {hours_string}")
    if minutes > 0:
        if minutes == 1:
            minutes_string = 'минута'
        elif minutes == 2 or days == 3 or days == 4:
            minutes_string = 'минуты'
        else:
            minutes_string = 'минут'
        parts.append(f"{minutes} {minutes_string}")
    if seconds > 0:
        if seconds == 1:
            seconds_string = 'секунда'
        elif seconds == 2 or days == 3 or days == 4:
            seconds_string = 'секунды'
        else:
            seconds_string = 'секунд'
        parts.append(f"{seconds} {seconds_string}")
    
    human_readable = ", ".join(parts)
    return human_readable

# Функция отправки email сообщения
def send_email(subject, body, recipients):
    """
    Отправляет email всем получателям, указанным в параметре.
    
    Args:
        subject (str): Тема письма.
        body (str): Текст письма.
        recipients (list): Список получателей.
    """
    global timer_running, update_timer_state

    try:
        msg = MIMEMultipart()
        msg['From'] = configuration['sender']
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))

        if configuration['attachments']:
            for f in configuration['attachments']:
                with open(f, "rb") as fil: 
                    file_extension = f.split('.')[-1:]
                    attachedfile = MIMEApplication(fil.read(), _subtype = file_extension)
                    attachedfile.add_header(
                        'content-disposition', 'attachment', filename=os.path.basename(f) )
                msg.attach(attachedfile)

        server = smtplib.SMTP(configuration['server'], configuration['port'])
        server.starttls()
        password, password_status = decrypt_password(configuration['password'], CRYPT_KEY)
        server.login(configuration['username'], password)
        server.sendmail(configuration['sender'], recipients, msg.as_string())
        server.quit()

        print(f"\n{Fore.GREEN}Письмо успешно отправлено.{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"\n{Fore.RED}Ошибка отправки email: {e}{Style.RESET_ALL}\n")
    
    timer_running = False
    update_timer_state = False

# Функция запуска приложения в режиме демона
def daemon_mode():
    """
    Функция для запуска таймера в режиме демона.
    """
    global timer_thread, timer_running, start_time

    print("Программа запущена в режиме демона.")
    print(f'При необходимости внесите правки в файл {CONFIG_FILE}')
    print(print_config())
    print('\nДля выхода из приложения нажмите ctrl + c\n')
    
    # Запуск потока таймера
    timer_thread = threading.Thread(target=start_timer, args=(configuration['duration'],))
    timer_thread.start()

    try:
        # Вывод статуса таймера каждые 10 секунд
        while timer_thread.is_alive():
            elapsed_time = time.time() - start_time
            remaining_time = max(0, configuration['duration'] - elapsed_time)
            print(f"Таймер работает, осталось {int(remaining_time)} секунд ({format_time(int(remaining_time))}).")
            time.sleep(10)
    except KeyboardInterrupt:
        print('\nЗавершение работы демона...')
        timer_running = False
        timer_thread.join()

    # Ожидание заверешения потока
    timer_thread.join()

# Функция изменения значений в конфигурационном файле
def config_command():
    """
    Команда для просмотра и изменения текущей конфигурации.
    """
    global configuration

    def simple_change_config_param(param):
        """
        Внутреннее меню для смены простых переменных в конфигурации
        """
        global sigint_status

        # Если sigint_status True, значит нужно игнорировать новые данные в input
        sigint_status = False

        # Удобное название параметра конфигурации
        readable_param_name = configuration["configuration_names"][param]
        try:
            print(f"Введите новое значение для {Fore.GREEN}{readable_param_name}{Style.RESET_ALL} ('{stop_word_colored}' или '{ctrl_c_hotkey}' для отмены)")
            # Изменение пароля
            if param == 'password':
                # Получение расшифрованного пароля и статуса шифрования (пароль зашифрован или нет)
                decrypted_password, password_encrypted = decrypt_password(configuration[param], CRYPT_KEY)
                if password_encrypted:
                    print(f'Текущее шифрованное значение: {configuration[param]}')
                    print(f'Текущее расшифрованное значение: {Fore.LIGHTBLACK_EX}{Back.WHITE} {decrypted_password} {Style.RESET_ALL}')
                else:
                    if decrypted_password.strip() != '': # Если расшифровать не удалось
                        print('Похоже, что ваш пароль не зашифрован или использован другой ключ')
                        print('Для шифрования пароля необходимо задать его используя встроенный функционал программы')
                        print(f'Текущее значение: {Style.DIM}{configuration[param]}{Style.RESET_ALL}')
                    else: # Если пароль не задан
                        print('Шифрованный пароль не задан в конфигурации')

                # Ввод нового значения пароля
                new_value = input(f">>> ").strip()
                
                if new_value != '' and new_value != stop_word:
                    # Шифруем пароль
                    new_value = encrypt_password(new_value, CRYPT_KEY)
                    
            else:
                # Для всех остальных значений
                print(f'Текущие значение: {configuration[param]}')
                new_value = input(f">>> ").strip()
        
            if sigint_status:
                new_value = stop_word

        except: # Если произошла ошибка, или был нажат ctrl + C
            new_value = stop_word

        # Смена второй строчки в меню через переменную menu.subtitle
        if new_value.strip().lower() == stop_word:
            menu.subtitle = f'> {Fore.YELLOW}Изменения {param} отменены.'
        else:
            try:
                # duration и port конвертируются в числа
                if param == 'duration' or param == 'port':
                    configuration[param] = int(new_value)
                    if param == 'duration':
                        menu.current_item.text = f'{readable_param_name}: {Fore.GREEN}{new_value} сек. ({format_time(int(new_value))}){Style.RESET_ALL}'
                    else:
                        menu.current_item.text = f'{readable_param_name}: {Fore.GREEN}{new_value}{Style.RESET_ALL}'
                else:
                    configuration[param] = new_value
                    if param == 'password':
                        password_lenght = get_lenght_of_decrypted_password(new_value, CRYPT_KEY)
                        if password_lenght > 0:
                            menu.current_item.text = f'{readable_param_name}: {Fore.GREEN}{"*" * password_lenght}{Style.RESET_ALL}'
                        else:
                            menu.current_item.text = f'{readable_param_name}: {Fore.RED}-{Style.RESET_ALL}'
                    else:
                        menu.current_item.text = f'{readable_param_name}: {Fore.GREEN}{new_value}{Style.RESET_ALL}'

                if param == 'password':
                    menu.subtitle = (
                        f'> {Fore.GREEN}Новое значение {Style.RESET_ALL}"{readable_param_name}" = '
                        f'{"*" * get_lenght_of_decrypted_password(new_value, CRYPT_KEY)}'
                    )
                else:
                    menu.subtitle = f'> {Fore.GREEN}Новое значение {Style.RESET_ALL}"{readable_param_name}" = {new_value}'

                # Сохраняем новую конфигурацию
                save_configuration()

            except Exception as e:
                menu.subtitle = f'> {Fore.RED}Ошибка: {e}. {param} != {new_value}{Style.RESET_ALL}'

    def show_submenu(name):
        """
        Отображение внутреннего меню для смены списка из конфигурации
        С выбором действия из submenu_options_list
        """
        global sigint_status

        # Если sigint_status True, значит нужно игнорировать новые данные в input
        sigint_status = False
    
        # Удобное название параметра
        configuration_name = configuration['configuration_names'][name]

        # На UNIX ctrl + c работать не будет
        # Поэтому меняем имя кнопки выхода
        if os.name == 'nt':
            selection_menu_exit_text = f'Возврат ({ctrl_c_hotkey})'
        else:
            selection_menu_exit_text = f'Возврат'

        # Инициализация внутреннего меню
        selection_menu = SelectionMenu(
            submenu_options_list,
            title=f'> Изменение списка "{configuration_name}"',
            subtitle=f'{configuration[name]}',
            exit_option_text=selection_menu_exit_text
        )

        # Отображение внутреннего меню
        selection_menu.show()

        # Сохранение выбора пользователя
        selection_index = selection_menu.selected_option

        # Если пользователь не выбрал выход (3) или не нажал ctrl + C (-1)
        if selection_index >= 0 and selection_index != 3:
            # Запуск функции обработки выбора пользователя
            submenu_change_config_param(selection_index, name)
        else:
            menu.subtitle = f'> {Fore.YELLOW}Изменения параметра "{configuration_name}" отменены.'

    def submenu_change_config_param(selection, name):
        """
        Функция обработки выбора во внутреннем меню
        После выбора, например 'Добавить элемент' функция
        обработает ввод пользователя в зависимости от выбора в подменю

        Args:
            selection (int):
                0: Добавить запись
                1: Удалить запись
                2: Заменить все
                3: Выход
            name (str): Название параметра конфигурации
        """
        global sigint_status

        # Если sigint_status True, значит нужно игнорировать новые данные в input
        sigint_status = False

        readable_param_name = configuration['configuration_names'][name]
        print(f'Выбрано: {Fore.GREEN}{submenu_options_list[selection]}{Style.RESET_ALL} в "{Fore.GREEN}{readable_param_name}{Style.RESET_ALL}"')
        print(f"Введите новые данные, разделенные запятой ('{stop_word_colored}' или '{ctrl_c_hotkey}' для отмены)")
        print(f'Текущие: {configuration[name]}')

        if name == 'attachments':
            # Список файлов в текущей папке
            current_dir_files = list(filter(lambda x: os.path.isfile(x), os.listdir(os.curdir)))
            try:
                # Удаляем стандартные файлы приложения в текущей папке
                current_dir_files.remove('insurance.py')
                current_dir_files.remove('insurance.key')
                current_dir_files.remove('insurance.config')
                current_dir_files.remove('requirements.txt')
                current_dir_files.remove('run.sh')
            except:
                pass
            print(f'Файлы в этой директории: {current_dir_files}')

        try:
            new_data_raw = input(">>> ").strip()
            new_data = new_data_raw.split(',')
        except:
            menu.subtitle = f'> {Fore.YELLOW}Изменения параметра "{readable_param_name}" отменены.'
            return 1
        
        # Выход, если на linux нажато ctrl+c
        if sigint_status:
            new_data = stop_word
        
        if stop_word in new_data:
            menu.subtitle = f'> {Fore.YELLOW}Изменения параметра "{readable_param_name}" отменены.'
            return 0

        # Если добавить
        if selection == 0:
            excluded_data = []
            validated_data = []

            new_data = [r.strip() for r in new_data]
            for data in new_data:
                if data not in configuration[name] and data.strip() != '':
                    validated_data.append(data)
                else:
                    excluded_data.append(data)

            if validated_data and not excluded_data:
                if configuration[name] != '':
                    configuration[name].extend(validated_data)
                else:
                    configuration[name] = validated_data
                save_configuration()

                menu.subtitle = (
                    f'> {Fore.GREEN}Данные {validated_data} добавлены в {Style.RESET_ALL}'
                    f'"{configuration["configuration_names"][name]}". \nПолный список: {configuration[name]}'
                )

            elif not validated_data and excluded_data:
                menu.subtitle = (
                    f'> Список "{configuration["configuration_names"][name]}" {Fore.YELLOW}не был изменен.{Style.RESET_ALL}\n'
                    f'{Fore.RED}Данные {excluded_data}{Style.RESET_ALL} уже существуют и {Fore.RED}не были добавлены{Style.RESET_ALL}.\n'
                    f'\nПолный список: {configuration[name]}'
                )
            else:
                configuration[name].extend(validated_data)
                save_configuration()

                menu.subtitle = (
                    f'> Данные {Fore.GREEN}{validated_data} добавлены в {Style.RESET_ALL}'
                    f'"{configuration["configuration_names"][name]}".\n'
                    f'{Fore.RED}Данные {excluded_data}{Style.RESET_ALL} уже существуют и {Fore.RED}не были добавлены{Style.RESET_ALL}.\n'
                    f'\nПолный список: {configuration[name]}'
                )

        # Если удалить
        elif selection == 1: 
            if new_data_raw in configuration[f'{name}']:
                data_to_remove = [r.strip() for r in new_data]
                configuration[f'{name}'] = [r for r in configuration[f'{name}'] if r not in data_to_remove]
                save_configuration()

                menu.subtitle = (
                    f'> {Fore.GREEN}Данные {data_to_remove} удалены из {Style.RESET_ALL}'
                    f'"{configuration["configuration_names"][name]}".\n'
                    f'Полный список: {configuration[name]}'
                    f''
                )
            else:
                menu.subtitle = f'> {Fore.RED}Ошибка: Данные {new_data} не существуют в "{readable_param_name}"!'
        
        # Если заменить
        elif selection == 2:
            old_data = configuration[f'{name}']

            new_data = [r.strip() for r in new_data if r.strip() != '']
            configuration[f'{name}'] = new_data
            save_configuration()

            menu.subtitle = (
                f'> {Fore.GREEN}Замена в {Style.RESET_ALL}{old_data}'
                f'"{configuration["configuration_names"][name]}".\n'
                f'{Fore.GREEN}->{Style.RESET_ALL} {new_data}'
            )

        # Изменение цвета и штучного наименования
        if len(configuration[name]) > 1:
            menu.current_item.text = (
                f'{configuration["configuration_names"][name]}: '
                f'{Fore.GREEN}{len(configuration[name])} шт.{Style.RESET_ALL}'
            )
        else:
            if not configuration[name]:
                menu.current_item.text = (
                    f'{configuration["configuration_names"][name]}: '
                    f'{Fore.RED}-{Style.RESET_ALL}'
                )
            else:
                menu.current_item.text = (
                    f'{configuration["configuration_names"][name]}: '
                    f'{Fore.GREEN}{", ".join(configuration[name])}{Style.RESET_ALL}'
                )
          
    def menu_print_config():
        """
        Вывод текущей конфигурации в меню
        """
        print(print_config())
        print(f'{Fore.YELLOW}Нажмине Enter для выхода{Style.RESET_ALL}', end="")
        try:
            # Ждем нажатия enter от пользователя
            input()
        except:
            pass

    # Список действий со списком
    submenu_options_list = [
            "Добавить элемент", 
            "Удалить элемент", 
            "Заменить полностью все элементы",
        ]

    # Разные надпись для горячих клавиш в зависимости от ОС
    if os.name == 'nt':
        ctrl_c_hotkey = f'{Fore.YELLOW}ctrl + c{Style.RESET_ALL}'
    else:
        ctrl_c_hotkey = f'{Fore.YELLOW}ctrl + с + Enter{Style.RESET_ALL}'

    # Надпись для кнопки выхода
    exit_text = f'Выход ({ctrl_c_hotkey})'

    # Надпись для кнопки выхода во внутреннем меню
    submenu_exit_text = f'Возврат ({ctrl_c_hotkey})'

    # Слово для отмены ввода новых значений
    stop_word = 'cancel'
    stop_word_colored = f'{Fore.YELLOW}cancel{Style.RESET_ALL}'

    # Инициализация ConsoleMenu
    menu = ConsoleMenu(
        f"{Back.GREEN} Конфигурация {Style.RESET_ALL}",
        "> Введите номер параметра для изменения и нажмине Enter", 
        exit_option_text=exit_text,
        exit_menu_char='0'
        )
    
    # Перехват SIGINT на linux
    # Блок кода для UNIX подобных систем, что бы 
    # правильно обрабатывать SIGINT во время работы console-menu.
    # Проблема в том, что при нажатии ctrl+c происходит некорректное поведение
    if os.name != 'nt':
        def handle_sigint(signal_number, frame):
            global sigint_status
            """
            Обработчик сигнала SIGINT для linux
            """
            os.system('clear') # Очищаем терминал
            print(f'Нажмите {Fore.GREEN}Enter{Style.RESET_ALL} для продолжения ...')
            sigint_status = True # Единственное место откуда этот флаг может стать True
            menu.exit() # завершаем работу menu

        # Привязываем вызов функции при сигнале SIGINT (ctrl+c)
        signal.signal(signal.SIGINT, handle_sigint)

    # Описание пунктов основого меню
    try:
        # Описываем пункт для печати конфигурации внутри меню
        print_config_item = FunctionItem("Печать конфигурации", menu_print_config)

        # Добавляем каждый пункт в меню из конфигурационного файла
        for key, value in configuration["configuration_names"].items():
            
            # Отдельно для списочных параметров, для отображения всех значений через знак ','
            if key == 'recipients' or key == 'attachments':
                item_text = (
                    f'{configuration["configuration_names"][key]}: '
                    f'{Fore.RED}-{Style.RESET_ALL}' 
                    if not configuration[key]
                    else f'{configuration["configuration_names"][key]}: '
                    f'{Fore.GREEN}{", ".join(configuration[key])}{Style.RESET_ALL}'
                )
                
                # Если длина списка больше 1, то отображаем общее количество
                if len(configuration[key]) > 1:
                    item_text = f'{configuration["configuration_names"][key]}: {Fore.GREEN}{len(configuration[key])} шт.{Style.RESET_ALL}'

                # Создаем пункт с вызовом функции для внутреннего меню (редактирование списков)
                item = FunctionItem(
                    item_text, 
                    show_submenu,
                    [key]
                )
            
            # Для обычных параметров
            else:
                # Отдельно для password, что бы закрыть пароль знаком '*'
                if key == 'password':
                    item_text = (
                        f'{configuration["configuration_names"][key]}: '
                        f'{Fore.RED}-{Style.RESET_ALL}' 
                        if not configuration[key] 
                        else f'{configuration["configuration_names"][key]}: '
                        f'{Fore.GREEN}{"*" * get_lenght_of_decrypted_password(configuration[key], CRYPT_KEY)}{Style.RESET_ALL}'
                    )
                else: # Для всех остальных
                    item_text = (
                        f'{configuration["configuration_names"][key]}: '
                        f'{Fore.RED}-{Style.RESET_ALL}' 
                        if not configuration[key] 
                        else f'{configuration["configuration_names"][key]}: '
                        f'{Fore.GREEN}{configuration[key]}{Style.RESET_ALL}'
                    )

                # Создаем пункт с вызовом функции для простой функции
                item = FunctionItem(
                    item_text,
                    simple_change_config_param,
                    [key]
                )
            
            # Добавляем созданный пункт в меню 
            menu.append_item(item)

        # Отдельно добавляем пункт печати конфигурации
        menu.append_item(print_config_item) 

        menu.show() # Открываем меню

    except KeyboardInterrupt:
        # Игнорирование ctrl+c помогает вернуться на главную страницу
        # Преимущественно для windows
        pass 
    
    except Exception as e:
        # Если были ошибки чтения конфигурации
        print_formatted_text(
                HTML(
                    (
                        '\n<ansired>Ваш конфигурационный файл содержит ошибки значений или синтаксиса.\n'
                        f'Пожалуйста, исправьте ошибки или удалите сломанный файл {CONFIG_FILE}.\n'
                        f'Подробнее: {e}</ansired>\n'
                    )
                )
            )
    
    return

# Функция обработки команд пользователя на главном экране
async def get_user_input(session):
    """
    Получение ввода от пользователя на главной странице
    """
    global prompt, timer_thread, timer_running, start_time, update_thread, update_timer_state

    while True:
        # асинхронно ожидаем ввод пользователя, не блокируя основной поток
        command = await session.prompt_async(lambda: prompt)

        # Запускаем таймер
        if command == 'start':
            if not timer_running:
                start_timer_thread()
            else:
                print("Таймер уже запущен.")

        # Останавливаем таймер
        elif command == 'stop':
            if timer_thread and timer_thread.is_alive():
                stop_timer_thread()
            else:
                print("Таймер не запущен.")

        # Перезапускаем таймер
        elif command == 'restart':
            if timer_thread and timer_thread.is_alive():
                restart_timer_thread()
            else:
                start_timer_thread() # Если таймер еще не был запущен

        # Получаем статус таймера
        elif command == 'status':
            get_timer_status()
        
        # Вывод доступных команд
        elif command == 'help':
            help_command()
        
        # Интерактивная настрйока конфигурационного файла 
        elif command == 'config':
            config_command()
        
        # Тестовая отправка email сообщения
        # Что бы убедиттся, что приложение правильно настроено
        elif command == 'test':
            test_command()
        
        # Вывод текущих значений конфигурации
        elif command == 'print':
            print(print_config())

        # Выход из программы
        elif command == 'exit':
            timer_running = False
            update_timer_state = False
            print('\nЗавершение программы...')
            sys.exit(0)
        else:
            print(f"Неизвестная команда. Введите '{Fore.GREEN}help{Style.RESET_ALL}' для списка команд.")

# Главная функция
def main():
    """
    Функция главной страницы
    """
    global timer_thread, timer_running, start_time, update_timer_state

    # Создание парсера аргументов командной строки
    parser = argparse.ArgumentParser(
        formatter_class=CustomHelpFormatter,
            usage='insurance.py [-h] [--daemon]'
        )
    
    # Добавление аргументов к парсеру
    parser.add_argument('-d', '--daemon', action='store_true', help="Запустить программу в режиме демона")
    parser.add_argument('-t', '--test', action='store_true', help="Отправить тестовое письмо")
    parser.add_argument('-p', '--print', action='store_true', help="Вывести текущую конфигурацию")
    
    # Разбор аргументов
    args = parser.parse_args()

    # Загружаем данные из конфигурационного файла
    load_configuration()

    # Если запуск в режиме демона
    if args.daemon:
        daemon_mode()
        return
    
    # Если нужно отправить тестовое письмо
    if args.test:
        test_command()
        return
    
    # Если нужно отправить тестовое письмо
    if args.print:
        print(print_config())
        return

    # Продолжение работы в нормальном режиме
    print(f'\nВведите комманду: [{Fore.GREEN}help{Style.RESET_ALL}, start, stop, restart, status, config, test, print, exit]')

    # Создание цикла событий
    loop = asyncio.get_event_loop()

    # Создание сеанса ввода
    session = PromptSession()

    try:
        loop.run_until_complete(get_user_input(session))
    except KeyboardInterrupt:
        # Выключаем таймеры при нажатии ctrl + c
        update_timer_state = False
        timer_running = False
        print('\nПрограмма завершена.')
    finally:
        loop.close()

# Инициализация констант
CONFIG_FILE = 'insurance.config' # Кофигурационный файл
KEY_FILE = 'insurance.key' # Файл ключа шифрования

# Словарь со значениями из конфигурационного файла
configuration = {}

# Инициализация переменных для таймера
timer_running = False # Статус работы таймера
timer_thread = None # Поток таймера
start_time = None # Время начала отсчета
update_timer_state = False # Статус обновления надписи в input

# Глобальная переменная, означающая что было нажато ctrl+c
# На UNIX подобных системах обработка SIGINT происходит не так, как хотелось бы
# Отсюда этот костыль
sigint_status = False

# Начальная строчка ввода команд
prompt = HTML(f"> INSURANCE[<ansired>OFF</ansired>]: ")

# Генерация и загрузка ключа для шифрования
generate_key(KEY_FILE)
CRYPT_KEY = load_key(KEY_FILE)

if __name__ == "__main__":
    main()
