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

Para instalar o pacote, execute:

```bash
pip install botweb
```

## Exemplo de Uso

```python
from botweb import BotWeb


class MyBot(BotWeb):
    def __init__(self, *args, **kwargs):
        super().__init__(
            # The prefix name to be concatenated with the credentials_keys
            # eg. WEB_SYSTEM_USERNAME, WEB_SYSTEM_PASSWORD
            # these variables will be setted as environment variables
            # with the values asked from the terminal.
            # To prevent of every run ask the credentials from the terminal
            # restart the IDE after provide the credentials values
            prefix_env="WEB_SYSTEM",
            credentials_keys=["USERNAME", "PASSWORD"]
            )

    def login(self):
        """My login logic here! (Abstract method needs to be implemented)"""
        # self._enter_username(self.credentials['USERNAME'])
        # self._enter_password(self.credentials['PASSWORD'])
        # self._submit()

        # This method sets the cookies into the self.session: requests.Session
        # It enable making requests inside the system
        # see the post_example() method bellow
        self.get_cookies()

    def post_example(self):
        # The headers inspected from the network request
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": "",
            "content-type": "application/json;charset=UTF-8",
        }

        # If the system store the token in the local storage it would work,
        # else override it with your own logic to get the token authorization
        headers.update({
            "authorization": self.get_token_authorization_from_storage()
            })

        # The payload inspected from the network request
        body = 'a=something&b=anotherthing'
        response = self.session.post(
            "https://example.com.br",
            headers=headers,
            data=body,
        )
        if response.status_code == 200:
            print(response.json())


if __name__ == '__main__':
    with MyBot() as mybot:
        mybot.init_browser(headless=False, browser="firefox")
        mybot.open(
            "https://github.com/login"
        )
        mybot.login()
        # mybot.post_example()
        input("Digite algo para continuar...")

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

