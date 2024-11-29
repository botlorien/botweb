# BotWeb

BotWeb é uma ferramenta poderosa para automação de operações web, combinando as bibliotecas Selenium e Requests. Este projeto foi projetado para simplificar tarefas como scraping de dados, interações em sites e testes automatizados.

## Funcionalidades

- **Automatização com Selenium:** Controle completo de navegadores para interagir com elementos de páginas web.
- **Requisições HTTP com Requests:** Realize requisições GET, POST e outras operações HTTP.
- **Integração entre Selenium e Requests:** Flexibilidade para usar o melhor das duas bibliotecas em suas operações web.

## Requisitos

- Python 3.10 ou superior.
- Navegador compatível com o Selenium (ex.: Chrome, Firefox, Edge).

## Instalação

### Passo 1: Instalar o Pacote

O pacote estará disponível no PyPI. Para instalá-lo, execute:

```bash
pip install botweb
```

### Passo 2: Verificar a Instalação

Certifique-se de que o pacote foi instalado corretamente:

```bash
python -m botweb --help
```

Se você vir as opções de comando, a instalação foi bem-sucedida.

## Exemplo de Uso

```python
from botweb import BotWeb

class MyBot(BotWeb):
    def __init__(self, *args, **kwargs):
        super().__init__(
            prefix_env="WEB_SYSTEM", # The prefix name to be concatenated with the credentials_keys eg. WEB_SYSTEM_USERNAME, WEB_SYSTEM_PASSWORD these variables will be setted as environment variables with the values asked from the terminal
            credentials_keys=["USERNAME", "PASSWORD"]
            )
    
    def login(self):
        """My login logic here! (Abstract method needs to be implemented)"""
        pass

if __name__=='__main__':
    with MyBot() as mybot:
        mybot.init_browser(headless=False, browser="firefox")
        mybot.open(
            "https://github.com/login"
        )
        mybot.login()

```

## Contribuições

Contribuições são bem-vindas! Para contribuir:

1. Fork este repositório.
2. Crie um branch para sua funcionalidade ou correção:
   ```bash
   git checkout -b minha-funcionalidade
   ```
3. Envie suas alterações:
   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```
4. Submeta um pull request.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## Contato

Para mais informações ou suporte, visite o [repositório no GitHub](https://github.com/botlorien/botweb).

