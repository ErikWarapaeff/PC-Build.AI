from pydantic import BaseModel, Field
from typing import List, Optional, Union
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fuzzywuzzy import process
import time

# Определяем модель для FPS информации
class FPSInfo(BaseModel):
    resolution: str
    fps: str

# Основная модель для результата
class GameRequirementsResult(BaseModel):
    game: str
    cpu: str
    gpu: str
    ram: int
    requirements: Optional[str]
    fps_info: List[FPSInfo] = Field(default_factory=list)
    paragraphs: List[str] = Field(default_factory=list)
    error: Optional[str] = None

def check_game_requirements(game_name, cpu_model, gpu_model, ram_size) -> Union[GameRequirementsResult, str]:
    # Настройки для хедлесс-режима
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Запуск драйвера
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)

    try:
        # Открытие страницы
        driver.get("https://technical.city/ru/can-i-run-it")

        # Ввод названия игры
        game_name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.ui-autocomplete-input")))
        game_name_input.send_keys(game_name)

        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "ul.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.highlight.ui-front")))
        game_item = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@class='bold-text' and text()='{game_name}']")))
        game_item.click()

        # Ввод данных о процессоре
        cpu_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.select-input[placeholder='Выберите процессор']")))
        cpu_input.send_keys(cpu_model)

        # Ввод данных о видеокарте
        gpu_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.select-input[placeholder='Выберите видеокарту']")))
        gpu_input.send_keys(gpu_model)
        gpu_list = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.ui-menu.ui-widget.ui-widget-content.ui-autocomplete.highlight.ui-front li.ui-menu-item")))
        gpu_options = [gpu.text for gpu in gpu_list]
        best_match = process.extractOne(gpu_model, gpu_options)
        best_match_element = gpu_list[gpu_options.index(best_match[0])]
        best_match_element.click()

        # Ввод данных о оперативной памяти
        ram_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='selecter-selected']")))
        ram_dropdown.click()
        ram_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[@class='selecter-item' and @data-value='{ram_size}']")))
        ram_option.click()

        # Извлечение данных
        requirements_notice = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//p[@class='notice']")))
        print(requirements_notice)
        # requirements_notice = requirements_notice[0].text if requirements_notice else None
        
        paragraph_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH,  "//p")))

        resolution_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='fps_quality_resolution']")))
        fps_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='fps_value']/em[@class='green' or @class='yellow' or @class='red']")))

        fps_data = [
            FPSInfo(resolution=resolution_elements[i].text.strip(), fps=fps_elements[i].text.strip())
            for i in range(len(resolution_elements))
        ]
        # paragraph_elements = driver.find_elements(By.XPATH, "//p")

        # # Извлечение текста из каждого параграфа
        paragraphs = [paragraph_elements[i].text for i in [2, 5]]
        
        # return fps_data
        

        # Формируем результат
        return GameRequirementsResult(
            game=game_name,
            cpu=cpu_model,
            gpu=best_match[0],
            ram=ram_size,
            requirements=requirements_notice,
            fps_info=fps_data,
            paragraphs=paragraphs
        )

    except Exception as e:
        return GameRequirementsResult(
            game=game_name,
            cpu=cpu_model,
            gpu=gpu_model,
            ram=ram_size,
            error=str(e)
        )
    finally:
        driver.quit()



# Пример вызова функции
result = check_game_requirements("GTA V", "EPYC 9655P", "GeForce RTX 4090", 16)
# print(result.json(indent=4, ensure_ascii=False))
print(result)