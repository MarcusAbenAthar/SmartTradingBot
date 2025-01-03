# SmartTradingBot

<img src="https://github.com/MarcusAbenAthar/SmartTradingBot/blob/main/assets/image/smarttradingbot_logo.png" alt="SmartTradingBot Logo" width="200" height="200">


**Um bot de trading automatizado e dinâmico para operar na Bybit, baseado em sinais de indicadores técnicos e com funcionalidades avançadas de otimização, gerenciamento de risco e inteligência artificial.**

**Descrição:**

Este bot foi projetado para operar de forma autônoma na exchange de criptomoedas Bybit. Ele utiliza uma combinação de indicadores técnicos para gerar sinais de compra e venda, além de implementar estratégias de gerenciamento de risco e otimização de parâmetros para maximizar os lucros e minimizar as perdas.

**Funcionalidades:**

* **Análise técnica avançada:** Utiliza uma variedade de indicadores técnicos, incluindo Ichimoku Cloud , Parabolic SAR  e padrões de candles , para gerar sinais de trading precisos.
* **Múltiplos timeframes:** Analisa o mercado em diferentes timeframes para identificar oportunidades de trading em diversas escalas de tempo .
* **Gerenciamento de risco:** Implementa estratégias de gerenciamento de risco, como stop-loss, take-profit e trailing stop , para proteger o capital e maximizar os lucros.
* **Otimização de parâmetros:** Permite a otimização dos parâmetros do bot para encontrar as configurações mais eficientes para diferentes condições de mercado .
* **Análise de sentimento:** Integra análise de sentimento do mercado para incorporar informações adicionais na tomada de decisão .
* **Aprendizado de máquina:** Utiliza algoritmos de aprendizado de máquina para melhorar a precisão dos sinais de trading e a adaptação às condições do mercado .
* **Interface amigável:** Possui uma interface web intuitiva para monitorar o desempenho do bot e ajustar as configurações .
* **Alertas via Telegram:** Envia alertas via Telegram com informações sobre os sinais de trading e o desempenho do bot (implementado).

**Funcionalidades Adicionais (não no Roadmap original):**

* **Cálculo da alavancagem dinâmica:** Implementamos o cálculo da alavancagem dinamicamente com base na força do sinal e nas condições de mercado, utilizando indicadores como volatilidade, distância do stop-loss, ADX, RSI e Estocástico.
* **Tratamento de erros robusto:** Adicionamos tratamento de erros abrangente em todo o código, incluindo tratamento de exceções e mensagens de erro informativas, para garantir a estabilidade e a confiabilidade do bot.
* **Sistema de logging completo:** Implementamos um sistema de logging completo utilizando o `loguru`, que registra as informações importantes sobre a execução do bot, incluindo mensagens de debug, para facilitar a análise e a resolução de problemas.
* **Correção de erros e otimizações:** Corrigimos diversos erros no código e implementamos otimizações para melhorar o desempenho e a eficiência do bot.

**Roadmap:**

O desenvolvimento do bot está dividido em quatro fases:

* **Fase 1:** Melhorias na análise técnica e mensagens do Telegram. (em andamento)
* **Fase 2:** Monitoramento, relatórios e testes. 
* **Fase 3:** Otimização e automação. 
* **Fase 4:** Análise de sentimento e inteligência artificial. 

**Como usar:**

1. Clone o repositório: `git clone https://github.com/MarcusAbenAthar/SmartTradingBot.git`
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente:
    * Crie um arquivo `.env` na pasta raiz do projeto.
    * Defina as variáveis de ambiente, como a API key e a API secret da Bybit, o token do bot do Telegram e o ID do chat do Telegram.
4. Execute o bot: `python main.py`

**Contribuições:**

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests para relatar problemas, sugerir melhorias ou contribuir com novas funcionalidades.

**Licença:**

Este projeto está licenciado sob a licença MIT - consulte o arquivo [LICENSE](LICENSE) para obter detalhes.

**Aviso Legal:**

Este bot de trading é fornecido apenas para fins educacionais e informativos. O uso deste bot é de sua inteira responsabilidade. Os desenvolvedores não se responsabilizam por quaisquer perdas financeiras que possam ocorrer como resultado do uso deste bot.

**Lembre-se:**

* **Investir em criptomoedas envolve riscos.** Faça sua própria pesquisa e invista apenas o que você pode perder.
* **Este bot não garante lucros.** O mercado de criptomoedas é volátil e imprevisível, e não há garantia de que o bot será lucrativo.
* **Monitore o desempenho do bot.** Acompanhe o desempenho do bot de perto e ajuste as configurações conforme necessário.

**Espero que este bot seja útil para você!** 😊
