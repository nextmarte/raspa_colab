# Raspa Colab - Web Scraper para Colab.re

Um scraper web automatizado para coletar posts de reclamações da plataforma [Colab.re](https://colab.re) utilizando Playwright e BeautifulSoup.

## 📋 Descrição

Este projeto automatiza a coleta de posts (reclamações de cidadãos) da plataforma Colab.re, permitindo análise em massa dos dados coletados. O scraper:

- ✅ Realiza autenticação automatizada com CPF, email e senha
- ✅ Navega pela plataforma com delays aleatórios para evitar detecção de bot
- ✅ Implementa scroll infinito para carregar todos os posts disponíveis
- ✅ Filtra posts por período configurável (últimos N dias)
- ✅ Converte timestamps relativos em datas absolutas
- ✅ Exporta dados em formato JSON estruturado

## 🚀 Começando

### Pré-requisitos

- Python 3.8+
- Gerenciador de pacotes `uv`

### Instalação

1. Clone ou navegue até o diretório do projeto:
```bash
cd raspa_colab
```

2. Configure as dependências com `uv`:
```bash
uv sync
```

Ou instale manualmente:
```bash
pip install playwright beautifulsoup4 python-dotenv
playwright install chromium
```

### Configuração

Crie um arquivo `.env` na raiz do projeto com suas credenciais:

```env
CPF=seu_cpf_aqui
EMAIL=seu_email@exemplo.com
PASSWORD=sua_senha_aqui
DAYS_BACK=7
```

**Variáveis de Ambiente:**

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|------------|
| `CPF` | CPF para autenticação (sem formatação) | - | ✅ Sim |
| `EMAIL` | Email cadastrado na plataforma | - | ✅ Sim |
| `PASSWORD` | Senha da conta | - | ✅ Sim |
| `DAYS_BACK` | Número de dias para coletar posts | 7 | ❌ Não |

## 💻 Uso

Execute o scraper:

```bash
python main.py
```

Ou com `uv`:

```bash
uv run python main.py
```

### Processo de Execução

1. **Autenticação**: Acessa a página de login e preenche CPF, email e senha
2. **Navegação**: Aguarda carregamento da página de posts
3. **Coleta**: Implementa scroll infinito para carregar todos os posts
4. **Filtragem**: Verifica a data de cada post e para quando atingir a data limite
5. **Exportação**: Salva os dados em `colab_posts.json`

## 📊 Formato de Saída

O scraper gera um arquivo `colab_posts.json` com a seguinte estrutura:

```json
[
  {
    "autor": "Nome do Autor",
    "local": "Cidade, Estado",
    "tempo": "há 2 horas",
    "data_calculada": "05/11/2025 14:30",
    "titulo": "Título da reclamação",
    "descricao": "Descrição completa do post...",
    "imagem": "https://app.colab.re/image.jpg",
    "link": "https://app.colab.re/post/123456"
  },
  ...
]
```

**Campos:**

| Campo | Descrição |
|-------|-----------|
| `autor` | Nome da pessoa que fez a reclamação |
| `local` | Localização geográfica (cidade/estado) |
| `tempo` | Tempo relativo do post (ex: "há 2 horas") |
| `data_calculada` | Data e hora calculadas a partir do tempo relativo |
| `titulo` | Título/resumo da reclamação |
| `descricao` | Descrição completa do post |
| `imagem` | URL da imagem anexada (se houver) |
| `link` | URL do post na plataforma |

## 🔧 Funcionalidades Técnicas

### Autenticação com Delays Aleatórios

O scraper implementa delays aleatórios entre **3 e 7 segundos** em cada etapa para simular comportamento humano:

- Após carregamento da página de login
- Após preenchimento do CPF
- Após clique no botão CONTINUAR
- Após preenchimento do email
- Após preenchimento da senha
- Após clique no botão ENTRAR
- Após cada scroll de carregamento de posts

### Parsing de Timestamps Relativos

A função `parse_tempo_to_datetime()` converte timestamps em português para datetime absoluto:

```
"há 6 minutos"  → 2025-11-05 14:24:00
"há 2 horas"    → 2025-11-05 12:30:00
"há 1 dia"      → 2025-11-04 16:30:00
"há 2 semanas"  → 2025-10-22 16:30:00
"há 3 meses"    → 2025-08-05 16:30:00
```

### Scroll Inteligente com Cutoff de Data

O scraper implementa:

1. **Scroll Infinito**: Carrega posts continuamente até atingir limite
2. **Detecção de Fim**: Para após 3 scrolls sem novos posts
3. **Cutoff de Data**: Para quando post mais antigo for anterior à data limite
4. **Filtragem Final**: Remove posts fora do período especificado

### Seletores CSS com Fallbacks

Utiliza múltiplos seletores para garantir compatibilidade:

```python
# Exemplo: Campo de email
"input[placeholder*='e-mail'], input[placeholder*='email'], input[type='email'], input[name='email']"
```

## 📈 Estrutura do Projeto

```
raspa_colab/
├── main.py                 # Script principal
├── .env                    # Credenciais (não versionado)
├── colab_posts.json        # Saída dos posts coletados
├── pyproject.toml          # Configuração do projeto
├── README.md               # Este arquivo
```

## ⚙️ Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| `playwright` | ^1.40.0 | Automação de navegador |
| `beautifulsoup4` | ^4.12.0 | Parsing de HTML |
| `python-dotenv` | ^1.0.0 | Carregamento de variáveis de ambiente |

## 🔒 Segurança

- **Credenciais**: Nunca commit do arquivo `.env` com credenciais reais
- **Git Ignore**: Adicione `.env` ao `.gitignore`
- **Headless Mode**: Browser executa sem interface visual
- **Random Delays**: Evita bloqueio por detecção de bot

## ⚠️ Limitações e Considerações

1. **Dependência de UI**: O scraper é sensível a mudanças na estrutura HTML do site
2. **Taxa de Limite**: Implementar delays evita bloqueios, mas coleta é mais lenta
3. **Sessão**: Uma sessão de browser é aberta e fechada a cada execução
4. **JavaScript**: Utiliza Playwright para executar JavaScript (necessário para SPA)

## 🐛 Troubleshooting

### "Inputs encontrados: 0"
- Verifique se a página de login carregou corretamente
- Tente aumentar o timeout no `wait_for_selector`

### "Cards não encontrados"
- A estrutura HTML pode ter mudado
- Verifique se o seletor `.ant-card.ant-card-bordered` ainda é válido
- Abra o DevTools para inspecionar a página

### "Erro ao parsear tempo"
- Alguns formatos de tempo podem não ser reconhecidos
- Verifique o console para mensagens de erro

## 📝 Logs e Debug

O script exibe logs no console indicando:

```
Acessando página de login...
Aguardando redirecionamento após login...
URL atual após login: https://app.colab.re/...
Página carregada, coletando posts da última semana...
Coletando posts dos últimos 7 dias (limite: 04/11/2025 16:30)
Posts carregados: 15
Posts carregados: 28
Sem novos posts. Tentativa 1/3
Post mais antigo encontrado: 04/11/2025 10:15 (anterior ao limite)
Finalizando coleta...
48 posts coletados dos últimos 7 dias.
```

## 🎯 Melhorias Futuras

- [ ] Adicionar suporte a múltiplas sessões paralelas
- [ ] Implementar cache para evitar recoleta
- [ ] Adicionar filtros por categoria/palavra-chave
- [ ] Exportar para CSV, Excel ou banco de dados
- [ ] Agendar execução periódica com APScheduler
- [ ] Adicionar logging estruturado com Python logging
- [ ] Implementar proxy rotation para escalabilidade

## 📄 Licença

Este projeto é fornecido como está, sem garantias. Use de forma responsável e respeitando os termos de serviço da plataforma Colab.re.

## 📧 Contato

Para dúvidas ou sugestões sobre o projeto, entre em contato com o desenvolvedor.

---

**Última atualização**: 5 de novembro de 2025
