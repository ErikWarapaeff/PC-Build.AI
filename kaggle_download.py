import shutil
import os

# Укажите путь к исходной папке с файлами
source_dir = r"C:\Users\Erik\.cache\kagglehub\datasets\warcoder\pc-parts\versions\1"

# Укажите путь к целевой папке
target_dir = r"C:\Users\Erik\Documents\VSCode\PC-Build.AI\data"

# Если целевая папка не существует, создаем её
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# Перемещаем все файлы из исходной папки в целевую
for filename in os.listdir(source_dir):
    file_path = os.path.join(source_dir, filename)
    if os.path.isfile(file_path):
        shutil.move(file_path, os.path.join(target_dir, filename))

print(f"Файлы успешно перемещены из {source_dir} в {target_dir}")
