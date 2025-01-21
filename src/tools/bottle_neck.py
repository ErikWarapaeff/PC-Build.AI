import json
from fuzzywuzzy import process
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def calculate_bottleneck(processor: str, gpu: str, resolution: str = "1080p") -> dict:
    """
    Расчет процента узкого горлышка операций между процессором и видеокартой при выбранном разрешении.

    Args:
        processor (str): Название процессора.
        gpu (str): Название видеокарты.
        resolution (str): Разрешение экрана. По умолчанию '1080p'.

    Returns:
        dict: Результаты расчета в формате JSON.
    """
    # Настройка браузера для работы в безголовом режиме
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Запуск драйвера
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    driver.get("https://bottleneckcalculator.help/")

    try:
        # Функция для поиска наиболее похожего элемента из списка
        def get_best_match(input_text, elements_list):
            best_match = process.extractOne(input_text, elements_list)
            return best_match[0] if best_match else ""

        # 1. Заполнение поля для процессора
        processor_input = wait.until(EC.presence_of_element_located((By.ID, "processor")))

        processor_input.send_keys(processor)
        processor_list = [element.text for element in wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='p-2']//span")))]
        processor_input.clear()
        processor_input.send_keys(get_best_match(processor, processor_list))

        # 2. Заполнение поля для GPU
        gpu_input = wait.until(EC.presence_of_element_located((By.ID, "graphics")))
        gpu_input.send_keys(gpu)
        gpu_list = [element.text for element in wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='p-2']//span")))]
        gpu_input.clear()
        gpu_input.send_keys(get_best_match(gpu, gpu_list))

        # Скрытие перекрывающего элемента с помощью JavaScript
        driver.execute_script(""" 
            var element = document.querySelector('a.text-2xl');
            if (element) {
                element.style.display = 'none';
            }
        """)

        # 3. Клик по кнопке "Calculate Bottleneck"
        try:
            calculate_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Calculate Bottleneck']")))
            driver.execute_script("arguments[0].scrollIntoView();", calculate_button)
            calculate_button.click()
        except Exception as e:
            # print(f"Ошибка при клике на кнопку: {e}")
            driver.execute_script("arguments[0].click();", calculate_button)

        # Извлечение информации
        cpu_performance = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='CPU Performance']/following-sibling::span"))).text
        gpu_performance = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='GPU Performance']/following-sibling::span"))).text
        bottleneck_percentage = wait.until(EC.presence_of_element_located((By.XPATH, "//h3[text()='Bottleneck Percentage']/following-sibling::p"))).text

        # 4. Получение производительности в разных сценариях
        performance_scenarios = {scenario.find_element(By.XPATH, ".//h6").text: scenario.find_element(By.XPATH, ".//p").text
                                 for scenario in driver.find_elements(By.XPATH, "//div[contains(@class, 'flex flex-col items-center text-center')]")
                                 if scenario.find_element(By.XPATH, ".//h6").text in ["Gaming", "Content Creation", "Streaming"]}

        # 5. Рекомендации
        recommendations = []
        
        # Собираем все возможные рекомендации
        performance_recommendations = driver.find_elements(By.XPATH, "//p[contains(text(), 'limiting')]")
        recommendations.extend([rec.text for rec in performance_recommendations])
        other_recommendations = driver.find_elements(By.XPATH, "//ul[@class='list-disc list-inside space-y-2 text-gray-700 ml-0']//li")
        recommendations.extend([rec.text for rec in other_recommendations])

        # Формирование JSON-ответа
        results = {
            "Input Parameters": {
                "Processor": processor,
                "GPU": gpu,
                "Resolution": resolution,
                "Best Processor Match": get_best_match(processor, processor_list),
                "Best GPU Match": get_best_match(gpu, gpu_list)
            },
            "Results": {
                "CPU Performance": cpu_performance,
                "GPU Performance": gpu_performance,
                "Bottleneck Percentage": bottleneck_percentage,
                "Performance Scenarios": performance_scenarios,
                "Recommendations": recommendations
            }
        }

        return results

    finally:
        # Закрытие браузера
        driver.quit()

# Пример вызова функции
if __name__ == "__main__":
    processor = "Intel core i9-13900K"
    gpu = "GeForce RTX 3070"
    resolution = "1440p"
    result = calculate_bottleneck(processor, gpu, resolution)
    print(json.dumps(result, indent=4, ensure_ascii=False))
