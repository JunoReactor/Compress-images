import os
import argparse
from PIL import Image, UnidentifiedImageError
from datetime import datetime, timedelta

Image.MAX_IMAGE_PIXELS = None

def convert_bytes_to_mb(bytes):
    return bytes / (1024 * 1024)

def is_optimized(file_path):
    with Image.open(file_path) as img:
        return img.info.get('progressive', False)

     
def optimize_image(file_path):
    original_size = os.path.getsize(file_path)
    resize_text = ''
    
    with Image.open(file_path) as img:
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

        img.save(file_path, 'JPEG', quality=85, optimize=True, progressive=True)
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

def process_directory(directory, days):
    processed_files = 0
    error_files = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.jpg') or file.lower().endswith('.jpeg'):
                file_path = os.path.join(root, file)
                if is_recently_created(file_path, days):
                    try:
                        if not is_optimized(file_path):
                            original_size, optimized_size, resize_text = optimize_image(file_path)
                            print(f'Оптимизация; {file_path}; (Объем: {convert_bytes_to_mb(original_size):.2f} -> {convert_bytes_to_mb(optimized_size):.2f} Мб{resize_text})')
                            processed_files += 1
                        else:
                            print(f'Пропуск; {file_path}; (уже оптимизирован)')

                    except UnidentifiedImageError:
                        print(f"Ошибка: Невозможно идентифицировать файл изображения: {file_path}")
                        error_files += 1
                    except Exception as e:
                        print(f"Произошла ошибка: {e}")
                        error_files += 1

    print(f'Обработано файлов: {processed_files}')
    print(f'Проблемных файлов: {error_files}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Оптимизация JPG файлов.')
    parser.add_argument('--directory', type=str, required=True, help='Путь к директории для обработки')
    parser.add_argument('--days', type=int, default=1, help='Количество дней для фильтрации файлов')
    
    args = parser.parse_args()
    process_directory(args.directory, args.days)
