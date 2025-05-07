# Telegram Media Downloader

Um script Python para baixar facilmente todos os arquivos de mídia de chats, grupos e canais do Telegram.

## Recursos

- Baixe mídias de qualquer chat, grupo ou canal acessível do Telegram
- Vários métodos para identificar o chat alvo (nome de usuário, link, nome, ID)
- Entre em grupos privados através de links de convite
- Downloads simultâneos para melhor desempenho
- Acompanhamento do progresso e estatísticas detalhadas

## Requisitos

- Python 3.6+
- Biblioteca Telethon
- python-dotenv

## Instalação

1. Clone este repositório ou baixe o script
2. Instale os pacotes necessários:
   ```
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` no mesmo diretório com suas credenciais da API do Telegram:
   ```
   API_ID=seu_api_id
   API_HASH=seu_api_hash
   ```

## Obtendo Credenciais da API do Telegram

1. Acesse https://my.telegram.org/auth
2. Faça login com seu número de telefone
3. Vá para "API development tools"
4. Crie uma nova aplicação
5. Copie o "App api_id" e "App api_hash" para o seu arquivo `.env`

## Como Usar

1. Execute o script:
   ```
   python app.py
   ```
2. Na primeira execução, você será solicitado a autenticar com sua conta do Telegram
3. Escolha como identificar o chat (nome de usuário, link, nome ou ID)
4. Defina os parâmetros de download (limite de mensagens, downloads simultâneos)
5. Aguarde o download ser concluído

## Opções de Download

- **Nome de usuário/grupo**: Insira com ou sem o símbolo @
- **Link de grupo/canal**: Insira o link t.me completo
- **Nome completo**: Insira o nome exato como mostrado no seu Telegram
- **ID numérico**: Insira o ID numérico do chat, se disponível

## Observações

- Os arquivos de mídia são armazenados em um diretório `media/[nome_do_chat]_[timestamp]`
- A primeira autenticação requer verificação por telefone
- Você deve ser membro de grupos privados para baixar mídia