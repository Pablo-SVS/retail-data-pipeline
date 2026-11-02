# Como explicar o projeto

## Demonstração em cinco minutos

1. Explique a pergunta comercial e a origem pública dos dados.
2. Execute os testes e mostre o comando único do pipeline.
3. Mostre a contagem de entrada = aceitos + quarentena e uma regra de rejeição.
4. Abra o SQL dos marts e explique por que pedido e item são granularidades diferentes.
5. Mostre a conciliação em milésimos de libra e as limitações dos créditos.

## Perguntas para praticar

- Por que SQLite nesta versão? Como migraria para PostgreSQL?
- Por que não apagar todas as linhas com cliente ausente?
- Como provar que reexecutar não duplica registros?
- Por que possíveis duplicatas não são apagadas automaticamente?
- Qual é o risco de comparar dezembro/2011 com novembro/2011?
- O que falta para produção: observabilidade operacional, retry/backoff, publicação atômica conjunta dos arquivos, orquestração e controle de acesso?

Apresente somente aquilo que consegue explicar e executar. O painel só deve ser apresentado como publicado quando houver um link público verificado.
