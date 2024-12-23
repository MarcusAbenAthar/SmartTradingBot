# Bot de Trading Autônomo

**Descrição**  
Bot de Trading Autônomo para o Mercado de Futuros com Análise Técnica e Gestão de Risco. Conectado à API da Bybit, o bot realiza operações automatizadas com base em indicadores técnicos e padrões de vela. Ele também oferece notificações em tempo real via WhatsApp ou Telegram.

---

## Tecnologias Usadas

- **Node.js**: Backend para integração com a API da Bybit e gerenciamento de ordens.
- **Python**: Para análise técnica e cálculos de indicadores, padrões de velas e gestão de risco.
- **TA-Lib**: Biblioteca para cálculos de indicadores técnicos.
- **pandas**: Para manipulação de dados de mercado e históricos.
- **Streamlit / Dash**: Para o desenvolvimento do dashboard acessível por PC e dispositivos móveis.
- **WhatsApp Business API**: Para envio de notificações via WhatsApp.
- **Telegram Bot API**: Para envio de notificações via Telegram.
- **Redis / RabbitMQ**: Para comunicação entre componentes e otimização de tarefas assíncronas.

---

## Funcionalidades

- **Análise Técnica**: Cálculos de indicadores técnicos e padrões de velas.
- **Gestão de Risco**: Regras de stop-loss, take-profit e limites de perdas.
- **Notificações Personalizadas**: Notificações via WhatsApp ou Telegram, configuráveis pelo usuário.
- **Dashboard Interativo**: Interface para monitoramento do desempenho e status do bot, acessível por PC e dispositivos móveis.
- **Backtesting**: Testes históricos para avaliar a performance do bot em diferentes cenários de mercado.

---

## Requisitos

- Conta na **Bybit** com acesso à API.
- Conta no **WhatsApp Business** (para notificações via WhatsApp).
- Conta no **Telegram** (para notificações via Telegram).
- Ambiente de desenvolvimento com **Node.js** e **Python**.

---

## Como Rodar o Projeto

1. **Clone este repositório**:

   ```bash
   git clone https://github.com/seu-usuario/nome-do-repositorio.git
   cd nome-do-repositorio
