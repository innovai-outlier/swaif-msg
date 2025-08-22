# SWAIF-MSG

**Sistema de Análise Inteligente de Conversas WhatsApp**

## 📌 O que é

SWAIF-MSG é uma solução que analisa automaticamente conversas do WhatsApp entre clínicas médicas e seus pacientes, transformando mensagens brutas em insights acionáveis e tarefas organizadas.

## 🎯 O que entrega

### Para a Clínica
- **Resumos automáticos** de todas as conversas do dia
- **Identificação de pendências** operacionais em tempo real
- **Classificação de tarefas** por responsável (secretária, médica ou gestão)
- **Análise de sentimento** e urgência das interações
- **Histórico completo** de conversas por paciente

### Para a Gestão
- **Métricas de atendimento** consolidadas
- **Identificação de gargalos** no processo de comunicação
- **Relatórios de qualidade** do atendimento
- **Análise de conversão** (leads em agendamentos)
- **Insights para melhoria** contínua do atendimento

## 🔄 Como funciona (visão geral)

O sistema processa as conversas em **3 camadas inteligentes**:

1. **Formatação (L1)**: Captura e estrutura mensagens do WhatsApp
2. **Agrupamento (L2)**: Organiza mensagens em conversas completas
3. **Análise IA (L3)**: Gera resumos, extrai tarefas, monitora métricas da desempenho de conversas e classifica prioridades

## 💡 Filosofia

Seguindo os princípios da automação sábia, o SWAIF-MSG automatiza o trabalho mecânico de análise de conversas, liberando a equipe para focar no que realmente importa: **o cuidado humano**.

> *"Não é que temos pouco tempo, mas sim que desperdiçamos muito dele"* - Sêneca

## 🏥 Caso de Uso Principal

Clínicas médicas que:
- Recebem dezenas/centenas de mensagens diárias via WhatsApp
- Precisam garantir que nenhuma solicitação seja perdida
- Querem melhorar a qualidade e velocidade do atendimento
- Buscam dados concretos para tomada de decisão

## 🔐 Privacidade e Segurança

- Processamento local de dados sensíveis
- Criptografia de informações médicas
- Conformidade com LGPD
- Dados nunca saem do ambiente controlado da clínica

## 📊 Resultados Esperados

- **Redução de 70%** no tempo gasto organizando conversas
- **Zero mensagens** perdidas ou não respondidas
- **Visibilidade completa** das pendências operacionais
- **Melhoria contínua** baseada em dados reais

## 🚀 Status do Projeto

**Versão Alpha** - Em desenvolvimento ativo

Funcionalidades implementadas:
- ✅ Captura de mensagens WhatsApp (Evolution API)
- ✅ Formatação inicial de dados (L1)
- 🔄 Agrupamento de conversas (L2) - em desenvolvimento
- 📅 Análise com IA (L3) - próxima fase

---

## 🔧 Desenvolvimento

Instale o pacote em modo editável e execute os testes:

```bash
pip install -e .
pip install -r requirements.txt
pytest
```

Ou utilizando o Makefile:

```bash
make install
make test
```

Exemplo de uso do L2 Grouper com número de secretária customizado:

```python
from depths.layers.l2_grouper import L2Grouper

grouper = L2Grouper(secretary_phone="5511998681314")
```

---

*SWAIF-MSG - Transformando conversas em insights, liberando tempo para o cuidado humano.*
