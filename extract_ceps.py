#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

bairros = ["centro", "icarai", "charitas", "fonseca"]
dados = {}

for bairro in bairros:
    url = f"https://codigo-postal.org/pt-br/brasil/rj/niteroi/{bairro}/"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]
                ceps = []
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ceps.append({
                            "endereco": cols[0].get_text(strip=True),
                            "cep": cols[1].get_text(strip=True)
                        })
                dados[bairro] = ceps
                print(f"✓ {bairro}: {len(ceps)} CEPs")
            else:
                print(f"✗ {bairro}: sem tabela")
        else:
            print(f"✗ {bairro}: erro {resp.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"✗ {bairro}: {e}")

with open("ceps_amostra.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)
print("\n✓ Salvo em ceps_amostra.json")
