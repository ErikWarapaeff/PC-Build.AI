import pickle
from random import randint
from time import sleep as pause
from typing import List, Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from pydantic import BaseModel

class ComponentInput(BaseModel):
    type: str  # Тип компонента (cpu, gpu, memory, etc.)
    name: str  # Наименование компонента

class ComponentOutput(BaseModel):
    type: str  # Тип компонента (cpu, gpu, memory, etc.)
    name: str  # Наименование компонента
    price: int  # Цена (в числовом формате для сортировки)
    url: str  # Ссылка

class ExtremeProductsOutput(BaseModel):
    type: str  # Тип компонента
    cheapest: Optional[ComponentOutput]  # Самый дешевый продукт
    most_expensive: Optional[ComponentOutput]  # Самый дорогой продукт

class Product(BaseModel):
    url: str
    name: str
    price: int

def generate_url(component_type: str, name: str, page: int) -> str:
    """Генерирует URL для заданного типа компонента и названия."""
    base_urls = {
        "cpu": "https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/?q={name}&p={page}",
        "gpu": "https://www.dns-shop.ru/catalog/17a89aab16404e77/videokarty/?q={name}&p={page}",
        "memory": "https://www.dns-shop.ru/catalog/17a89a3916404e77/operativnaya-pamyat-dimm/?q={name}&p={page}",
        "cpu-cooler": "https://www.dns-shop.ru/catalog/17a9cc2d16404e77/kulery-dlya-processorov/?q={name}&p={page}",
        "case": "https://www.dns-shop.ru/catalog/17a8a01d16404e77/korpusa/?q={name}&p={page}",
        "motherboard": "https://www.dns-shop.ru/catalog/17a89a0416404e77/materinskie-platy/?q={name}&p={page}",
        "power-supply": "https://www.dns-shop.ru/catalog/17a89c2216404e77/bloki-pitaniya/?q={name}&p={page}",
    }
    if component_type not in base_urls:
        raise ValueError(f"Unknown component type: {component_type}")
    return base_urls[component_type].format(name=name.replace(" ", "+"), page=page)

def get_urls_from_page(driver) -> List[Product]:
    """Собирает все ссылки, названия и цены на текущей странице и возвращает как список объектов Product."""
    soup = BeautifulSoup(driver.page_source, 'lxml')
    elements = soup.find_all('a', class_="catalog-product__name ui-link ui-link_black")
    names = [element.text.strip() for element in elements]
    prices = soup.find_all('div', class_="product-buy__price")
    prices = [int(price.text.strip().replace(' ', '')[:-3]) for price in prices]
    urls = ['https://www.dns-shop.ru' + element.get("href") + 'characteristics/' for element in elements]
    return [Product(url=url, name=name, price=price) for url, name, price in zip(urls, names, prices)]

def get_all_category_page_urls(driver, component: ComponentInput) -> List[ComponentOutput]:
    """Получает все товары для заданного компонента и возвращает их как список объектов ComponentOutput."""
    page = 1
    url = generate_url(component.type, component.name, page)
    driver.get(url=url)
    pause(10)

    soup = BeautifulSoup(driver.page_source, 'lxml')
    span_tags = soup.find_all('span')
    number_of_pages = []
    for i in span_tags:
        if bool(str(i).find('data-role="items-count"') != -1):
            number_of_pages = [int(x) for x in str(i) if x.isdigit()]
    res = int(''.join(map(str, number_of_pages)))
    pages_total = ((res // 18) + 1)
    print(f'Всего в категории {pages_total} страницы')

    products = []
    while True:
        page_products = get_urls_from_page(driver)
        products.extend(page_products)

        if page >= pages_total:
            break

        page += 1
        url = generate_url(component.type, component.name, page)
        driver.get(url)
        pause(randint(6, 9))

    return [ComponentOutput(type=component.type, name=product.name, price=product.price, url=product.url) for product in products]

def find_extreme_products(products: List[ComponentOutput]) -> ExtremeProductsOutput:
    """Находит самую дешевую и самую дорогую компоненту из списка."""
    if not products:
        return ExtremeProductsOutput(type="", cheapest=None, most_expensive=None)
    cheapest = min(products, key=lambda x: x.price)
    most_expensive = max(products, key=lambda x: x.price)
    return ExtremeProductsOutput(
        type=products[0].type,
        cheapest=cheapest,
        most_expensive=most_expensive
    )

def main():
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")  # Новый headless режим
    # options.add_argument("--disable-gpu")  # Отключение GPU для headless-режима
    # options.add_argument("--no-sandbox")  # Полезно для окружений без GUI
    # options.add_argument("--disable-dev-shm-usage")  # Устранение проблем с памятью в Docker и Linux

    # Запуск браузера с установленными опциями
    driver = uc.Chrome(options=options)
    input_data = [
        ComponentInput(type="cpu", name="AMD Ryzen 9 7950X3D"),
        ComponentInput(type="gpu", name="Geforce RTX 4080 SUPER"),
        ComponentInput(type="gpu", name="Asus DUAL OC 2C GeForce RTX 3060"),
        ComponentInput(type="motherboard", name="MSI MAG B660M MORTAR WIFI"),
        ComponentInput(type="memory", name="Kingston FURY Renegade 16 GB"),
        ComponentInput(type="power-supply", name="Corsair SF750"),
        ComponentInput(type="cpu-cooler", name="Deepcool AK400"),
    ]

    results = []

    for component in input_data:
        print(f'Обработка компонента {component.type}: {component.name}')
        try:
            products = get_all_category_page_urls(driver, component)
            extreme_products = find_extreme_products(products)
            results.append(extreme_products)
            print(f"Для {component.type}: Самый дешевый: {extreme_products.cheapest.name} за {extreme_products.cheapest.price} ₽")
            print(f"Самый дорогой: {extreme_products.most_expensive.name} за {extreme_products.most_expensive.price} ₽")
        except Exception as e:
            print(f'Ошибка для {component.type}: {e}')
    driver.quit()
    
    return results
    


    # # Сохранение результатов
    # with open('extreme_components.pkl', 'wb') as file:
    #     pickle.dump(results, file)

    # # Вывод результатов
    # print("\nРезультаты обработки:")
    # for result in results:
    #     print(result.json(indent=4, ensure_ascii=False))
    

if __name__ == '__main__':
    main()
