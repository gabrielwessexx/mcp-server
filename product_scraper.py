from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from typing import List, Dict

class ProductScraper:
    def __init__(self):
        self.url = "https://innovare-eletromoveis.rdi.store"
        self.setup_driver()

    def setup_driver(self):
        """Configura o driver do Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Executa em modo headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_products(self) -> List[Dict]:
        """Coleta informações dos produtos do site"""
        try:
            print("Acessando o site...")
            self.driver.get(self.url)
            
            # Aguarda a página carregar
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "product-item"))
            )
            
            # Coleta todos os produtos
            products = []
            product_elements = self.driver.find_elements(By.CLASS_NAME, "product-item")
            
            for element in product_elements:
                try:
                    name = element.find_element(By.CLASS_NAME, "product-name").text
                    price = element.find_element(By.CLASS_NAME, "product-price").text
                    
                    # Tenta obter o estoque (pode variar dependendo da estrutura do site)
                    try:
                        stock = element.find_element(By.CLASS_NAME, "product-stock").text
                    except:
                        stock = "Informação não disponível"
                    
                    products.append({
                        "nome": name,
                        "preco": price,
                        "estoque": stock
                    })
                except Exception as e:
                    print(f"Erro ao processar um produto: {str(e)}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"Erro ao acessar o site: {str(e)}")
            return []
        
        finally:
            self.driver.quit()

    def format_report(self, products: List[Dict]) -> str:
        """Formata o relatório dos produtos"""
        if not products:
            return "Não foi possível coletar informações dos produtos."
        
        report = "📊 Relatório de Produtos da Innovare Eletromóveis\n\n"
        
        for product in products:
            report += f"🏷️ Nome: {product['nome']}\n"
            report += f"💰 Preço: {product['preco']}\n"
            report += f"📦 Estoque: {product['estoque']}\n"
            report += "-------------------\n"
        
        return report

def main():
    scraper = ProductScraper()
    products = scraper.get_products()
    report = scraper.format_report(products)
    print(report)

if __name__ == "__main__":
    main()