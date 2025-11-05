#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

url = "https://codigo-postal.org/pt-br/brasil/rj/niteroi/"

try:
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Procura pela lista de bairros (ul com id="ul_list")
        ul_list = soup.find('ul', {'id': 'ul_list'})
        if ul_list:
            links = ul_list.find_all('a')
            bairros = []
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Extrai o slug do href
                if '/niteroi/' in href:
                    slug = href.split('/niteroi/')[1].rstrip('/')
                    if slug and slug != 'niteroi':
                        bairros.append({
                            "nome": text,
                            "slug": slug,
                            "url": href
                        })
            
            print(f"✓ Encontrados {len(bairros)} bairros\n")
            
            # Salva JSON
            with open("bairros_niteroi.json", "w", encoding="utf-8") as f:
                json.dump(bairros, f, ensure_ascii=False, indent=2)
            
            # Mostra alguns
            for b in bairros[:5]:
                print(f"  - {b['nome']} ({b['slug']})")
            print(f"  ... e mais {len(bairros) - 5}")
            
            print(f"\n✓ Salvo em bairros_niteroi.json")
        else:
            print("✗ Lista de bairros não encontrada")
    else:
        print(f"✗ Erro {resp.status_code}")
except Exception as e:
    print(f"✗ Erro: {e}")
