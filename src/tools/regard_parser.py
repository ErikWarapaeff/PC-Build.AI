from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Инициализация драйвера (например, Chrome)
driver = webdriver.Chrome()

# Открытие веб-страницы
driver.get('https://www.regard.ru/catalog?search=Видеокарта+RTX+4070')

# Ожидание загрузки страницы
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.CardText_title__7bSbO.CardText_listing__6mqXC')))

# Функция для парсинга первого товара
def parse_first_product():
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Извлечение первого предложения с сайта
    first_paragraph = soup.find('p')
    if first_paragraph:
        first_sentence = first_paragraph.get_text().split('.')[0] + '.'
        print("Первое предложение:", first_sentence)
    else:
        print("Не удалось найти первое предложение.")

# Функция для выбора сортировки
def apply_sorting(sort_text):
    # Нахождение кнопки сортировки по классу и клик на нее
    sort_button = driver.find_element(By.CSS_SELECTOR, '.SelectableList_wrap__uvkMK.SelectableList_inline__ZMCCF')
    ActionChains(driver).move_to_element(sort_button).click().perform()

    # Ожидание появления выпадающего списка
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//span[text()='{sort_text}']")))

    # Нахождение нужной опции и клик на нее
    sort_option = driver.find_element(By.XPATH, f"//span[text()='{sort_text}']")
    ActionChains(driver).move_to_element(sort_option).click().perform()

    # Ожидание появления первого товара после применения сортировки
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.CardText_title__7bSbO.CardText_listing__6mqXC')))

    # Парсинг первого товара после применения сортировки
    parse_first_product()

# Список сортировок, которые нужно обработать
sort_options = [
    "Сначала с низкой ценой",
    "Сначала дорогие",
    "Сначала популярные"
]

# Парсинг для каждой сортировки
for sort_text in sort_options:
    print(f"Товар после сортировки: {sort_text}")
    apply_sorting(sort_text)

# Закрытие браузера после выполнения
driver.quit()
