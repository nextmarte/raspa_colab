#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Carrega lista de bairros
with open("bairros_niteroi.json", "r") as f:
    bairros_list = json.load(f)

print(f"Extraindo CEPs de {len(bairros_list)} bairros...\n")

dados = {}
total_ceps = 0

for idx, bairro_info in enumerate(bairros_list, 1):
    bairro_slug = bairro_info['slug']
    bairro_nome = bairro_info['nome']
    
    url = f"https://codigo-postal.org/pt-br/brasil/rj/niteroi/{bairro_slug}/"
    
    try:
        print(f"[{idx}/{len(bairros_list)}] Buscando {bairro_nome}...", end=" ", flush=True)
        
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
                        endereco_text = cols[0].get_text(strip=True)
                        cep_text = cols[1].get_text(strip=True)
                        
                        # Ignora linhas com "ver todos"
                        if "ver todos" not in endereco_text.lower():
                            ceps.append({
                                "cep": endereco_text,
                                "rua": cep_text
                            })
                
                if ceps:
                    dados[bairro_slug] = {
                        "nome": bairro_nome,
                        "enderecos": ceps
                    }
                    total_ceps += len(ceps)
                    print(f"✓ {len(ceps)} CEPs")
                else:
                    print("✗ sem dados")
            else:
                print("✗ sem tabela")
        else:
            print(f"✗ erro {resp.status_code}")
        
        time.sleep(0.7)  # Delay para não sobrecarregar
        
    except requests.Timeout:
        print("✗ timeout")
    except Exception as e:
        print(f"✗ {e}")

print(f"\n{'='*50}")
print(f"Total: {len(dados)} bairros com CEPs")
print(f"Total de CEPs: {total_ceps}")
print(f"{'='*50}\n")

# Salva resultado
with open("ceps_todos_bairros.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print(f"✓ Salvo em ceps_todos_bairros.json ({len(dados)} bairros)")
