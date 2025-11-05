# colab_scraper.py
import asyncio
import os
import json
import re
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

CPF = os.getenv("CPF")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
DAYS_BACK = int(os.getenv("DAYS_BACK", "7"))
BASE_URL = "https://app.colab.re"


def get_random_delay():
    """Retorna um delay aleatório entre 3 e 7 segundos"""
    return random.uniform(3, 7)


def parse_tempo_to_datetime(tempo_text):
    """
    Converte texto de tempo relativo para datetime.
    Exemplos: "há 6 minutos", "há 2 horas", "há um dia", "há 5 dias"
    """
    now = datetime.now()

    if not tempo_text:
        return None

    tempo_text = tempo_text.lower().strip()

    # Extrai números do texto
    numbers = re.findall(r"\d+", tempo_text)

    try:
        if "minuto" in tempo_text:
            minutes = int(numbers[0]) if numbers else 1
            return now - timedelta(minutes=minutes)
        elif "hora" in tempo_text:
            hours = int(numbers[0]) if numbers else 1
            return now - timedelta(hours=hours)
        elif "dia" in tempo_text:
            days = int(numbers[0]) if numbers else 1
            return now - timedelta(days=days)
        elif "semana" in tempo_text:
            weeks = int(numbers[0]) if numbers else 1
            return now - timedelta(weeks=weeks)
        elif "mês" in tempo_text or "mes" in tempo_text:
            months = int(numbers[0]) if numbers else 1
            return now - timedelta(days=months * 30)
        else:
            return now
    except Exception as e:
        print(f"Erro ao parsear tempo '{tempo_text}': {e}")
        return now


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Acessando página de login...")
        await page.goto("https://minhaconta.colab.re/", wait_until="domcontentloaded")
        await page.wait_for_timeout(int(get_random_delay() * 1000))

        # Digita CPF e continua
        await page.fill("input[placeholder*='cpf'], input[name*='cpf']", CPF)
        await page.wait_for_timeout(int(get_random_delay() * 1000))
        await page.click("button:has-text('CONTINUAR')")
        await page.wait_for_timeout(int(get_random_delay() * 1000))

        # Aguarda um pouco e tenta encontrar o campo de email com múltiplos seletores
        try:
            await page.wait_for_selector(
                "input[placeholder*='e-mail'], input[placeholder*='email'], input[type='email'], input[name='email']",
                timeout=10000,
            )
        except Exception:
            # Tenta encontrar todos os inputs visíveis
            inputs = await page.query_selector_all("input:visible")
            print(f"Inputs encontrados: {len(inputs)}")
            for i, inp in enumerate(inputs):
                placeholder = await inp.get_attribute("placeholder")
                input_type = await inp.get_attribute("type")
                name = await inp.get_attribute("name")
                print(
                    f"Input {i}: placeholder='{placeholder}', type='{input_type}', name='{name}'"
                )
            raise

        # Preenche email e senha
        await page.fill(
            "input[placeholder*='e-mail'], input[placeholder*='email'], input[type='email'], input[name='email']",
            EMAIL,
        )
        await page.wait_for_timeout(int(get_random_delay() * 1000))
        await page.fill(
            "input[placeholder*='senha'], input[type='password'], input[name='password']",
            PASSWORD,
        )
        await page.wait_for_timeout(int(get_random_delay() * 1000))
        await page.click("button:has-text('ENTRAR')")
        await page.wait_for_timeout(int(get_random_delay() * 1000))

        # Aguarda um pouco após o login para ver para onde foi redirecionado
        print("Aguardando redirecionamento após login...")
        try:
            # Tenta esperar networkidle com timeout maior
            await page.wait_for_load_state("networkidle", timeout=20000)
        except Exception as e:
            print(f"Timeout em networkidle, continuando mesmo assim: {e}")
            # Aguarda um tempo fixo como fallback
            await page.wait_for_timeout(5000)

        # Verifica a URL atual
        current_url = page.url
        print(f"URL atual após login: {current_url}")

        # Se não redirecionou para app.colab.re, tenta esperar mais ou encontrar elementos
        if "app.colab.re" not in current_url:
            print(
                "Não foi redirecionado para app.colab.re. Verificando página atual..."
            )
            # Tenta encontrar algum elemento que indique sucesso ou erro
            try:
                # Espera um pouco mais para ver se aparece algum conteúdo
                await page.wait_for_timeout(3000)
                html = await page.content()
                if "erro" in html.lower() or "inválido" in html.lower():
                    print("Possível erro de login detectado no HTML")
            except Exception as e:
                print(f"Erro ao analisar página após login: {e}")

        # Espera específica pela página de posts do app.colab.re
        print("Aguardando carregamento da página de posts...")
        try:
            # Espera pela URL correta ou pelos cards
            await page.wait_for_function(
                """() => {
                    return window.location.href.includes('app.colab.re') ||
                           document.querySelector('.ant-card.ant-card-bordered') !== null;
                }""",
                timeout=20000,
            )
        except Exception as e:
            print(
                f"Timeout ao esperar página de posts: {e}. Tentando continuar...")

        # Tenta continuar mesmo sem redirecionamento correto
        try:
            # Se não tiver os cards, espera um pouco mais
            await page.wait_for_selector(".ant-card.ant-card-bordered", timeout=15000)
        except Exception as e:
            print(
                f"Cards não encontrados no timeout: {e}. Tentando fallback...")
            # Tenta fazer scroll para carregar os cards
            await page.evaluate("window.scrollTo(0, 500)")
            await page.wait_for_timeout(3000)
            print("Continuando mesmo sem aguardar todos os cards...")

        print("Página carregada, coletando posts da última semana...")

        # Define a data limite para coleta
        date_limit = datetime.now() - timedelta(days=DAYS_BACK)
        print(
            f"Coletando posts dos últimos {DAYS_BACK} dias (limite: {date_limit.strftime('%d/%m/%Y %H:%M')})"
        )

        # Faz scroll para carregar mais posts
        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_pauses = 0
        max_scroll_pauses = 3  # Para após 3 scrolls sem novos posts
        should_continue = True

        while scroll_pauses < max_scroll_pauses and should_continue:
            # Scroll para o final da página
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # Aguarda carregamento dos posts com delay aleatório
            await page.wait_for_timeout(int(get_random_delay() * 1000))

            # Calcula a nova altura
            new_height = await page.evaluate("document.body.scrollHeight")

            # Conta posts atuais
            current_posts = await page.evaluate(
                "document.querySelectorAll('.ant-card.ant-card-bordered').length"
            )

            print(f"Posts carregados: {current_posts}")

            if new_height == last_height:
                scroll_pauses += 1
                print(
                    f"Sem novos posts. Tentativa {scroll_pauses}/{max_scroll_pauses}")
            else:
                scroll_pauses = 0

            last_height = new_height

            # Verifica se há posts muito antigos na página
            html_current = await page.content()
            soup_current = BeautifulSoup(html_current, "html.parser")

            oldest_post_date = None
            for card in soup_current.select(".ant-card.ant-card-bordered"):
                tempo = card.select_one(".ant-card-extra")
                if tempo:
                    post_date = parse_tempo_to_datetime(tempo.text.strip())
                    if post_date:
                        if oldest_post_date is None or post_date < oldest_post_date:
                            oldest_post_date = post_date

            # Se o post mais antigo for anterior ao limite, para de fazer scroll
            if oldest_post_date and oldest_post_date < date_limit:
                print(
                    f"Post mais antigo encontrado: {oldest_post_date.strftime('%d/%m/%Y %H:%M')} (anterior ao limite)"
                )
                should_continue = False

        print("Finalizando coleta...")
        await page.wait_for_timeout(1000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        data = []
        date_limit = datetime.now() - timedelta(days=DAYS_BACK)

        for card in soup.select(".ant-card.ant-card-bordered"):
            autor = card.select_one(".ant-card-head-title span:first-child")
            local = card.select_one(".ant-typography-secondary")
            tempo = card.select_one(".ant-card-extra")
            titulo = card.select_one(
                ".ant-card-body > div.sc-48964794-0, .ckQViH")
            descricao = card.select_one(
                ".ant-card-body .ant-typography-ellipsis")
            imagem = card.select_one(".ant-card-cover img")
            link = card.select_one(".ant-card-cover a")

            # Calcula a data do post
            tempo_text = tempo.text.strip() if tempo else None
            post_date = parse_tempo_to_datetime(tempo_text)

            # Filtra posts anteriores ao limite de dias
            if post_date and post_date < date_limit:
                continue

            item = {
                "autor": autor.text.strip() if autor else None,
                "local": local.text.strip() if local else None,
                "tempo": tempo_text,
                "data_calculada": post_date.strftime("%d/%m/%Y %H:%M")
                if post_date
                else None,
                "titulo": titulo.text.strip() if titulo else None,
                "descricao": descricao.text.strip() if descricao else None,
                "imagem": BASE_URL + str(imagem["src"])
                if imagem and str(imagem.get("src", "")).startswith("/")
                else (str(imagem["src"]) if imagem else None),
                "link": BASE_URL + str(link["href"]) if link else None,
            }
            data.append(item)

        print(f"{len(data)} posts coletados dos últimos {DAYS_BACK} dias.")
        with open("colab_posts.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
