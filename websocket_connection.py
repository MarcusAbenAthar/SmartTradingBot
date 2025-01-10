import asyncio
import websockets
import ssl


async def conectar_websocket(endpoint):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        # Conectando ao WebSocket
        async with websockets.connect(endpoint, ssl=ssl_context) as websocket:
            print(f"Conectado ao WebSocket: {endpoint}")

            # Enviando uma mensagem para o servidor de echo
            await websocket.send("Olá, servidor WebSocket!")
            print("Mensagem enviada: 'Olá, servidor WebSocket!'")

            # Aguardando a resposta do servidor
            dados = await websocket.recv()
            print(f"Resposta recebida: {dados}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")


# Teste com o WebSocket de echo
endpoint = "wss://echo.websocket.org"  # Teste com o servidor de echo
asyncio.run(conectar_websocket(endpoint))
