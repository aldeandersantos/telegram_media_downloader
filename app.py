from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
import os
from dotenv import load_dotenv
import datetime
import asyncio
import importlib.util

load_dotenv()

has_cryptg = importlib.util.find_spec('cryptg') is not None

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')

SESSION_NAME = 'session'

MEDIA_DIR = 'media'
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

client = TelegramClient(
    SESSION_NAME, 
    api_id, 
    api_hash,
    connection_retries=10,
    retry_delay=1,
    auto_reconnect=True,
    request_retries=5
)

async def download_media(message, download_dir):
    try:
        path = await client.download_media(
            message,
            file=download_dir,
            progress_callback=None,
        )
        if path:
            return path, None
        return None, "Arquivo não disponível"
    except Exception as e:
        return None, str(e)

async def main():
    print(f"Iniciando sessão ({SESSION_NAME})...")
    await client.start()
    
    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Sessão ativa para: {me.first_name} (@{me.username})")
    else:
        print("AVISO: Sessão não encontrada ou expirada.")
        print("Você precisará fazer login apenas desta vez.")
        
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
    
    
    if option == "1":
        chat_input = input("Digite o nome de usuário (com ou sem @): ").strip()
        if not chat_input.startswith("@"):
            chat_input = "@" + chat_input
    elif option == "2":
        chat_input = input("Digite o link do grupo/canal: ").strip()
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
        
        download_dir = os.path.join(MEDIA_DIR, f"{chat_name.replace('/', '_').replace(' ', '_')}_{timestamp}")
        os.makedirs(download_dir, exist_ok=True)
        
        print(f"\n📥 Baixando mídias de: {chat_name}")
        print(f"📁 Salvando em: {download_dir}")
        
        limit_option = input("Deseja limitar a quantidade de mensagens? (s/n): ")
        limit = None
        if limit_option.lower() == 's':
            try:
                limit = int(input("Digite o número máximo de mensagens a verificar: "))
            except ValueError:
                print("Valor inválido. Não será aplicado limite.")
        
        try:
            default_concurrent = 10 if has_cryptg else 5
            max_concurrent = int(input(f"Quantidade de downloads simultâneos (recomendado: {default_concurrent}-{default_concurrent*2}): "))
            if max_concurrent < 1:
                max_concurrent = default_concurrent
        except ValueError:
            max_concurrent = default_concurrent
            print(f"Valor inválido. Usando {default_concurrent} downloads simultâneos por padrão.")
            
        print("\nIniciando download... (Isto pode demorar dependendo do tamanho do chat)")
        
        count = 0
        total_messages = 0
        media_messages = []
        
        start_time = datetime.datetime.now()
        total_bytes_downloaded = 0
        
        print("Analisando mensagens...")
        async for message in client.iter_messages(chat, reverse=True, limit=limit):
            total_messages += 1
            if message.media:
                media_messages.append(message)
            
            if total_messages % 100 == 0:
                print(f"Analisado: {total_messages} mensagens, {len(media_messages)} com mídia encontradas.")
        
        print(f"\nAnálise completa: {total_messages} mensagens, {len(media_messages)} mídias para download.")
        
        total_media = len(media_messages)
        
        semaphore = asyncio.Semaphore(max_concurrent)
        count = 0
        
        async def download_with_semaphore(message, index):
            nonlocal count
            async with semaphore:
                path, error = await download_media(message, download_dir)
                if path:
                    count += 1
                    print(f"✅ Mídia {count}/{total_media} baixada: {os.path.basename(path)}")
                else:
                    print(f"❌ Falha ao baixar mídia: {error}")
                
                if count % max(1, min(5, max_concurrent//2)) == 0:
                    print(f"Progresso: {count}/{total_media} ({int((count/total_media)*100)}%)")
        
        tasks = [download_with_semaphore(message, i) for i, message in enumerate(media_messages)]
        await asyncio.gather(*tasks)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✨ Download concluído em {duration:.1f} segundos!")
        if duration > 0:
            print(f"🚀 Velocidade média: {total_bytes_downloaded/duration/1024:.1f} KB/s")
        
        print(f"\n📊 Estatísticas:")
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