import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import process
import time

def check_game_requirements(game_name, cpu_model, gpu_model, ram_size):
    # Настройки для хедлесс-режима
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Запуск драйвера
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    result = {}  # Словарь для хранения результатов

    try:
        # Открытие страницы
        driver.get("https://technical.city/ru/can-i-run-it")

        # Ввод названия игры в поле поиска
        game_name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.ui-autocomplete-input")))
        game_name_input.send_keys(game_name)

        # Ожидание появления выпадающего списка
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.highlight.ui-front")))

        # Выбор элемента из выпадающего списка по тексту
        game_item = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@class='bold-text' and text()='{game_name}']")))
        game_item.click()

        result['game'] = game_name  # Сохраняем название игры

        # Ввод данных о процессоре
        cpu_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.select-input[placeholder='Выберите процессор']")))
        cpu_input.send_keys(cpu_model)
        result['cpu'] = cpu_model  # Сохраняем процессор

        # Ввод данных о видеокарте
        gpu_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.select-input[placeholder='Выберите видеокарту']")))
        gpu_input.send_keys(gpu_model)
        gpu_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.highlight.ui-front li.ui-menu-item")))

        # Список всех видеокарт в выпадающем списке
        gpu_options = [gpu.text for gpu in gpu_list]

        # Ищем наиболее релевантную видеокарту с помощью fuzzywuzzy
        best_match = process.extractOne(gpu_model, gpu_options)

        # Выбираем наилучшее совпадение
        best_match_element = gpu_list[gpu_options.index(best_match[0])]
        best_match_element.click()

        result['gpu'] = best_match[0]  # Сохраняем выбранную видеокарту

        # Ввод данных о количестве оперативной памяти
        ram_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='selecter-selected']")))

        # Кликнуть, чтобы открыть выпадающий список
        ram_dropdown.click()

        # Найти нужный элемент (оперативная память в зависимости от ввода)
        ram_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@class='selecter-item' and @data-value='{ram_size}']")))
        ram_option.click()

        result['ram'] = ram_size  # Сохраняем размер оперативной памяти

        # Извлечение информации из страницы
        requirements_notice = driver.find_element(By.XPATH, "//p[@class='notice']")
        result['requirements'] = requirements_notice.text

        # Извлечение данных из всех тегов <p>
        # gpu_comparison = WebDriverWait(driver, 10).until(
        #     EC.presence_of_all_elements_located((By.XPATH, "//p"))
        # )

        # # Извлечение текста из элементов <p>
        # paragraph_texts = [p.text for p in gpu_comparison]
        
        # result['component_rate'] = paragraph_texts.text
        
        resolution_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='fps_quality_resolution']"))
        )

        # Ожидаем появления всех элементов FPS с классами green, yellow или red
        fps_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='fps_value']/em[@class='green' or @class='yellow' or @class='red']"))
        )

        fps_data = []

        # Проверяем, что количество разрешений и FPS совпадает
        for i in range(len(resolution_elements)):
            try:
                resolution = resolution_elements[i].text.strip()
                fps = fps_elements[i].text.strip()
                fps_data.append({
                    'resolution': resolution,
                    'fps': fps
                })
            except Exception as e:
                print(f"Ошибка при извлечении данных: {e}")
                continue

        # Преобразуем в JSON
        result = {'fps_info': fps_data}


        # Возвращаем результат в формате JSON
        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        result['error'] = str(e)
        return json.dumps(result, ensure_ascii=False, indent=4)
    finally:
        # Закрытие браузера
        driver.quit()

# Пример вызова функции
result_json = check_game_requirements("GTA V", "EPYC 9655P", "GeForce RTX 4090", 16)
print(result_json)
