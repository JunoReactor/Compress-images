import os
import argparse
from PIL import Image, UnidentifiedImageError
from datetime import datetime, timedelta
from tqdm import tqdm
import colorama

Image.MAX_IMAGE_PIXELS = None

GREEN   = colorama.Fore.GREEN
SALAD_GREEN = '\033[92m'
GRAY    = colorama.Fore.LIGHTBLACK_EX
WHITE   = colorama.Fore.WHITE
RESET   = colorama.Fore.RESET
YELLOW  = colorama.Fore.YELLOW
RED     = colorama.Fore.RED
CYAN    = colorama.Fore.CYAN

def convert_bytes_to_mb(bytes):
    return bytes / (1024 * 1024)

def is_optimized(file_path):
    with Image.open(file_path) as img:
        return img.info.get('progressive', False)

def optimize_image(file_path):
    original_size = os.path.getsize(file_path)
    resize_text = ''

    with tqdm(total=100, desc=f'Обработка: {file_path}', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} завершено', leave=False) as pbar:
    
        with Image.open(file_path) as img:
            # Проверяем, не является ли изображение пустым
            if img.size == (0, 0):
                raise ValueError("Изображение пустое")
            pbar.update(15)
            # Преобразуем RGBA в RGB, если необходимо
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            pbar.update(30)
            # Проверяем разрешение изображения
            if img.width > 1920 or img.height > 1080:  # Проверка на FHD
                # Вычисляем новое разрешение с сохранением соотношения сторон
                aspect_ratio = img.width / img.height
                if aspect_ratio > 1:  # Широкоформатное изображение
                    new_width = 1920
                    new_height = int(1920 / aspect_ratio)
                else:  # Вертикальное изображение
                    new_height = 1080
                    new_width = int(1080 * aspect_ratio)

                img = img.resize((new_width, new_height))  # Изменяем размер до FHD
                resize_text = ', Размер уменьшен до FHD'
                pbar.update(40)
             
            img.save(file_path, 'JPEG', quality=85, optimize=True, progressive=True)
            pbar.update(15)
            pbar.update(100)
    optimized_size = os.path.getsize(file_path)
    return original_size, optimized_size, resize_text

def is_recently_modified(file_path, days):
    modification_time = os.path.getmtime(file_path)
    file_date = datetime.fromtimestamp(modification_time)
    return file_date >= datetime.now() - timedelta(days=days)

def is_recently_created(file_path, days):
    creation_time = os.path.getctime(file_path)
    file_date = datetime.fromtimestamp(creation_time)
    return file_date >= datetime.now() - timedelta(days=days)

def process_directory(directory, days, log):
    processed_files = 0
    error_files = 0
    zero_kb_files = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg'):
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) == 0:
                    print(f"{YELLOW}Пропуск: Файл 0 Кб: {file_path}{RESET}")
                    zero_kb_files += 1
                    continue  # Пропускаем файл 0 Кб

                if is_recently_created(file_path, days):
                    try:
                        if not is_optimized(file_path):
                            original_size, optimized_size, resize_text = optimize_image(file_path)
                            print(f'{SALAD_GREEN}Оптимизация; {file_path}; (Объем: {convert_bytes_to_mb(original_size):.2f} -> {convert_bytes_to_mb(optimized_size):.2f} Мб{resize_text}){RESET}')
                            processed_files += 1
                        else:
                            if(log == 1):
                                print(f'Пропуск; {file_path}; (уже оптимизирован)')

                    except UnidentifiedImageError:
                        print(f"{RED}Ошибка: Невозможно идентифицировать файл изображения: {file_path}{RESET}")
                        error_files += 1
                    except Exception as e:
                        print(f"{RED}Ошибка: {e}; {file_path}{RESET}")
                        error_files += 1

    print(f'Обработано файлов: {processed_files}')
    print(f'Проблемных файлов: {error_files}')
    print(f'Файлов 0 Кб: {zero_kb_files}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Оптимизация JPG файлов.')
    parser.add_argument('--directory', type=str, required=True, help='Путь к директории для обработки')
    parser.add_argument('--days', type=int, default=1, help='Количество дней для фильтрации файлов (берется за основу дата создания)')
    parser.add_argument('--log', type=int, default=1, help='Уровень уведомлений: 0 min, 1 max')
    
    args = parser.parse_args()
    process_directory(args.directory, args.days, args.log)
