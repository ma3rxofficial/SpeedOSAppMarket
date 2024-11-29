from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import os
import json
from datetime import datetime
import uuid

# Папка с приложениями
APPS_DIR = "apps"

if not os.path.exists(APPS_DIR):
    os.mkdir(APPS_DIR)

# Пути к файлам с описаниями, датами и пользователями
DESCRIPTIONS_FILE = "descriptions.json"
DATES_FILE = "dates.json"
USERS_FILE = "users.json"
UPLOADERS_FILE = "uploaders.json"
IDS2_FILE = "ids2.json"

# Загрузка описаний из файла
def load_descriptions():
    if os.path.exists(DESCRIPTIONS_FILE):
        with open(DESCRIPTIONS_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение описаний в файл
def save_description(app_name, description):
    descriptions = load_descriptions()
    descriptions[app_name] = description
    with open(DESCRIPTIONS_FILE, "w") as f:
        json.dump(descriptions, f)

# Получение описания приложения
def get_description(app_name):
    descriptions = load_descriptions()
    return descriptions.get(app_name, "No description")

# Загрузка дат загрузки из файла
def load_dates():
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение даты загрузки
def save_date(app_name):
    dates = load_dates()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dates[app_name] = now
    with open(DATES_FILE, "w") as f:
        json.dump(dates, f)

# Получение даты загрузки приложения
def get_date(app_name):
    dates = load_dates()
    return dates.get(app_name, "Unknown")

# Загрузка пользователей из файла
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение пользователей в файл
def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_uploaders():
    if os.path.exists(UPLOADERS_FILE):
        with open(UPLOADERS_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение описаний в файл
def save_uploader(app_name, uploader):
    uploaders = load_uploaders()
    uploaders[app_name] = uploader
    with open(UPLOADERS_FILE, "w") as f:
        json.dump(uploaders, f)

# Получение описания приложения
def get_uploader(app_name):
    uploaders = load_uploaders()
    return uploaders.get(app_name, "Unknown")

# Загрузка уникальных ID из файла
def load_ids2():
    if os.path.exists(IDS2_FILE):
        with open(IDS2_FILE, "r") as f:
            return json.load(f)
    return {}

# Сохранение ID
def save_id2(unique_name, filename):
    ids2 = load_ids2()
    ids2[unique_name] = filename
    with open(IDS2_FILE, "w") as f:
        json.dump(ids2, f)

# Получение ID приложения
def get_id2(unique_name):
    ids2 = load_ids2()
    return ids2.get(unique_name)

# Генерация уникального имени для файла
def generate_unique_filename(app_name):
    app_id = str(uuid.uuid4())  # Генерируем уникальный ID для каждого файла
    file_extension = os.path.splitext(app_name)[1]  # Получаем расширение файла
    return app_id + file_extension  # Уникальное имя файла

# Замена всех двойных кавычек на одинарные
def replace_double_quotes_with_single(string):
    return string.replace('"', "'")


class AppStoreHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)

        if parsed_path.path == "/apps":
            # Читаем список файлов из папки
            apps = []
            if os.path.exists(APPS_DIR) and os.path.isdir(APPS_DIR):
                for filename in os.listdir(APPS_DIR):
                    filepath = os.path.join(APPS_DIR, filename)
                    if os.path.isfile(filepath):
                        app_name = os.path.splitext(filename)[0]  # Оригинальное имя приложения
                        app_name2 = get_id2(app_name)
                        apps.append({
                            "name": app_name,
                            "name2": app_name2,
                            "size": os.path.getsize(filepath),
                            "description": get_description(app_name),
                            "date": get_date(app_name),
                            "date_obj": datetime.strptime(get_date(app_name), "%Y-%m-%d %H:%M"),
                            "uploader": get_uploader(app_name)
                        })


            apps.sort(key=lambda app: app["date_obj"], reverse=True)
            # Форматируем список приложений в Lua-таблицу
            response_text = "return {\n"
            for app in apps:
                response_text += f"  {{name = \"{app['name']}\", name2 = \"{app['name2']}\", size = {app['size']}, description = \"{app['description']}\", date = \"{app['date']}\", uploader = \"{app['uploader']}\"}},\n"
            response_text += "}"

            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(response_text.encode('utf-8'))

        elif parsed_path.path.startswith("/apps/"):
            # Отдаем конкретное приложение
            app_name = os.path.basename(parsed_path.path)
            filepath = os.path.join(APPS_DIR, app_name)

            if os.path.exists(filepath) and os.path.isfile(filepath):
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(filepath, "rb") as file:
                    self.wfile.write(file.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/apps":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Извлечение данных приложения и данных для авторизации
            app_data = urlparse.parse_qs(post_data)
            app_name = replace_double_quotes_with_single(app_data.get('name', [''])[0])
            app_content = app_data.get('content', [''])[0]
            app_description = replace_double_quotes_with_single(app_data.get("description", ["No description"])[0])
            username = replace_double_quotes_with_single(app_data.get('username', [''])[0])
            password = replace_double_quotes_with_single(app_data.get('password', [''])[0])

            if username and password:
                users = load_users()

                # Проверяем, что пользователь существует и пароль правильный
                if username in users and users[username] == password:
                    if app_name and app_content:
                        unique_filename = generate_unique_filename(app_name)
                        filepath = os.path.join(APPS_DIR, unique_filename)

                        save_id2(unique_filename, app_name)


                        with open(filepath, "w") as file:
                            file.write(app_content)

                        # Сохраняем описание и дату
                        save_description(unique_filename, app_description)
                        save_date(unique_filename)
                        save_uploader(unique_filename, username)

                        # Генерируем уникальный ID для приложения
                        app_id = str(uuid.uuid4())
                        save_id(app_name, app_id)

                        self.send_response(200)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(f"App {app_name} uploaded successfully!".encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Invalid app data!")
                else:
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b"Invalid credentials!")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing username or password!")

        elif self.path == "/register":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Извлечение данных для регистрации
            form_data = urlparse.parse_qs(post_data)
            username = replace_double_quotes_with_single(form_data.get('username', [''])[0])
            password = replace_double_quotes_with_single(form_data.get('password', [''])[0])

            if username and password:
                users = load_users()
                if username in users:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"User already exists!")
                else:
                    save_user(username, password)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"User registered successfully!")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid registration data!")

        elif self.path == "/login":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Извлечение данных для входа
            form_data = urlparse.parse_qs(post_data)
            username = replace_double_quotes_with_single(form_data.get('username', [''])[0])
            password = replace_double_quotes_with_single(form_data.get('password', [''])[0])

            users = load_users()
            if username in users and users[username] == password:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login successful!")
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Invalid credentials!")

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 5000), AppStoreHandler)
    print("Сервер запущен на порту 5000")
    server.serve_forever()
