from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
import os
from dotenv import load_dotenv
import datetime
import asyncio

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém as credenciais da API do Telegram
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

# Define o nome do usuário atual para a sessão
SESSION_NAME = 'session'

# Garante que o diretório para mídia existe
MEDIA_DIR = 'media'
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# Inicializa o cliente com o nome de sessão personalizado
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# Função para baixar uma única mídia
async def download_media(message, download_dir):
    try:
        path = await client.download_media(message, file=download_dir)
        if path:
            return path, None
        return None, "Arquivo não disponível"
    except Exception as e:
        return None, str(e)

async def main():
    # Inicia o cliente (usando o arquivo de sessão existente se disponível)
    print(f"Iniciando sessão ({SESSION_NAME})...")
    await client.start()
    
    # Verifica se o usuário está autenticado
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Sessão ativa para: {me.first_name} (@{me.username})")
    else:
        print("AVISO: Sessão não encontrada ou expirada.")
        print("Você precisará fazer login apenas desta vez.")
        
        # Se a autenticação for necessária, guia o usuário
        phone = input("Digite seu número de telefone com código do país (ex: +5511999999999): ")
        await client.send_code_request(phone)
        code = input("Digite o código recebido por SMS/Telegram: ")
        try:
            await client.sign_in(phone, code)
            print("Login realizado com sucesso! Não será necessário fazer login novamente.")
        except Exception as e:
            if "password" in str(e).lower():
                password = input("Digite sua senha de duas etapas: ")
                await client.sign_in(password=password)
                print("Login realizado com sucesso! Não será necessário fazer login novamente.")
            else:
                print(f"Erro no login: {e}")
                return
    
    # Timestamp para o nome da pasta
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n=== TELEGRAM MEDIA DOWNLOADER ===")
    print("Escolha como você quer encontrar o chat:")
    print("1 - Nome de usuário/grupo (ex: @pythonbrasil)")
    print("2 - Link do grupo (ex: t.me/pythonbrasil)")
    print("3 - Nome completo do grupo/canal")
    print("4 - ID numérico do chat")
    print("0 - Sair")
    
    option = input("\nEscolha uma opção (0-4): ")
    
    if option == "0":
        print("Encerrando o programa...")
        return
    
    # Processa a opção escolhida
    # ...código existente para processar opções...
    
    # O código para tratar as opções permanece o mesmo
    if option == "1":
        chat_input = input("Digite o nome de usuário (com ou sem @): ").strip()
        if not chat_input.startswith("@"):
            chat_input = "@" + chat_input
    elif option == "2":
        chat_input = input("Digite o link do grupo/canal: ").strip()
        # Verifica se é um link de convite privado
        if "t.me/+" in chat_input or "+t.me/" in chat_input:
            invite_hash = chat_input.split("+")[-1]
            try:
                print(f"Detectado link de convite privado. Tentando entrar no grupo...")
                updates = await client(ImportChatInviteRequest(invite_hash))
                chat_id = updates.chats[0].id
                chat_input = chat_id
                print(f"Grupo acessado com sucesso!")
            except Exception as e:
                print(f"Erro ao entrar no grupo: {e}")
                return
        # Link normal
        elif "t.me/" in chat_input:
            chat_input = chat_input.split("t.me/")[1]
    elif option == "3":
        chat_input = input("Digite o nome completo do grupo/canal: ").strip()
    elif option == "4":
        chat_input = input("Digite o ID numérico do chat: ").strip()
        if chat_input.isdigit():
            chat_input = int(chat_input)
    else:
        print("Opção inválida! Encerrando...")
        return
    
    try:
        print(f"\nProcurando por: {chat_input}")
        
        # Se for busca por nome completo
        if option == "3":
            found = False
            print("Buscando nos seus diálogos recentes...")
            
            async for dialog in client.iter_dialogs():
                if chat_input.lower() in dialog.name.lower():
                    confirm = input(f"Encontrado: '{dialog.name}'. É este o grupo correto? (s/n): ")
                    if confirm.lower() == 's':
                        chat = dialog.entity
                        chat_name = dialog.name
                        found = True
                        break
            
            if not found:
                print("Chat não encontrado. Tente usando o nome de usuário (@) ou ID.")
                return
        else:
            chat = await client.get_entity(chat_input)
            chat_name = getattr(chat, 'title', getattr(chat, 'username', chat_input))
        
        # Cria uma pasta específica para este download
        download_dir = os.path.join(MEDIA_DIR, f"{chat_name.replace('/', '_').replace(' ', '_')}_{timestamp}")
        os.makedirs(download_dir, exist_ok=True)
        
        print(f"\n📥 Baixando mídias de: {chat_name}")
        print(f"📁 Salvando em: {download_dir}")
        
        # Opções de limite
        limit_option = input("Deseja limitar a quantidade de mensagens? (s/n): ")
        limit = None
        if limit_option.lower() == 's':
            try:
                limit = int(input("Digite o número máximo de mensagens a verificar: "))
            except ValueError:
                print("Valor inválido. Não será aplicado limite.")
        
        # Nova opção para controlar o paralelismo
        try:
            max_concurrent = int(input("Quantidade de downloads simultâneos (recomendado: 5-10): "))
            if max_concurrent < 1:
                max_concurrent = 5
        except ValueError:
            max_concurrent = 5
            print("Valor inválido. Usando 5 downloads simultâneos por padrão.")
            
        print("\nIniciando download... (Isto pode demorar dependendo do tamanho do chat)")
        
        # Contadores
        count = 0
        total_messages = 0
        pending_downloads = []
        media_messages = []
        
        # Primeiro, coletamos todas as mensagens com mídia
        print("Analisando mensagens...")
        async for message in client.iter_messages(chat, reverse=True, limit=limit):
            total_messages += 1
            if message.media:
                media_messages.append(message)
            
            # Mostrar progresso a cada 100 mensagens durante a análise
            if total_messages % 100 == 0:
                print(f"Analisado: {total_messages} mensagens, {len(media_messages)} com mídia encontradas.")
        
        print(f"\nAnálise completa: {total_messages} mensagens, {len(media_messages)} mídias para download.")
        
        # Agora baixamos as mídias em lotes
        total_media = len(media_messages)
        for i in range(0, total_media, max_concurrent):
            # Pega um lote de mensagens
            batch = media_messages[i:i + max_concurrent]
            
            # Baixa o lote simultaneamente
            tasks = [download_media(message, download_dir) for message in batch]
            results = await asyncio.gather(*tasks)
            
            # Processa os resultados
            for path, error in results:
                if path:
                    count += 1
                    print(f"✅ Mídia {count}/{total_media} baixada: {os.path.basename(path)}")
                else:
                    print(f"❌ Falha ao baixar mídia: {error}")
            
            # Mostra o progresso geral
            print(f"Progresso: {min(i + max_concurrent, total_media)}/{total_media} ({int((min(i + max_concurrent, total_media)/total_media)*100)}%)")
        
        print(f"\n✨ Download concluído!")
        print(f"📊 Estatísticas:")
        print(f"   - Total de mensagens verificadas: {total_messages}")
        print(f"   - Total de mídias encontradas: {total_media}")
        print(f"   - Total de mídias baixadas com sucesso: {count}")
        print(f"   - Local de armazenamento: {download_dir}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nSugestões para resolver problemas:")
        print("- Verifique se você é membro do grupo/canal")
        print("- Certifique-se que o nome/link está correto")
        print("- Tente usar o nome de usuário (@) em vez do nome completo")
        print("- Se possível, obtenha o ID numérico do chat")

with client:
    client.loop.run_until_complete(main())