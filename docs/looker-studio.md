# Looker Studio: montagem e publicação

**Status: não publicado.** Este repositório entrega os dados e a especificação; não contém um relatório Looker Studio já criado. A integração disponível nesta sessão não permite criar ou publicar o relatório na conta Google.

## Fonte

Execute o pipeline e use `data/processed/mart_invoice.csv`. Crie uma fonte pelo conector de upload CSV no Looker Studio e depois um relatório vazio. IDs devem ser Texto; `invoice_date` deve ser Data; medidas devem ser Número, com agregação Soma; medidas GBP devem usar moeda GBP.

O upload é um snapshot, sem conexão automática com o SQLite. Ao atualizar, substitua/remova o conteúdo anterior antes de enviar um snapshot completo: anexar a mesma exportação duplicaria os valores. Para este conjunto histórico, uma carga validada basta para demonstrar o painel.

## Layout: visão comercial

Página 1440 × 1000; fundo #F5F7FA; títulos #14213D; destaque #167D8D; créditos #C46637. Título: **Online Retail | Vendas e créditos**. Subtítulo: **Base histórica UCI · valores em GBP · dez/2010 a dez/2011**.

1. Filtros no topo: período e país.
2. Cartões: Vendas brutas, Créditos, Movimentação líquida e Documentos com venda.
3. Série temporal mensal: vendas brutas e créditos. Indicar explicitamente dezembro/2011 parcial.
4. Barras horizontais: 10 países por movimentação líquida.
5. Tabela por país: vendas, créditos, movimentação líquida, documentos com venda e ticket médio bruto.
6. Rodapé: atribuição UCI, link para o repositório, definição de créditos e limitações da base.

Campos calculados agregados:

```text
Ticket médio bruto = SUM(gross_sales_gbp) / SUM(sale_invoice_count)
Participação dos créditos = SUM(credits_gbp) / SUM(gross_sales_gbp)
```

Exiba nulo quando o denominador for zero. Não tire média de tickets calculados por linha. `COUNT_DISTINCT(customer_id)` serve somente para clientes identificados e deve excluir nulos; não somar clientes únicos por país ou mês.

## Validação antes de publicar

Sem filtros, compare os três cartões monetários com `quality_report.json`, arredondando apenas a exibição para duas casas. Compare a soma de `sale_invoice_count` com a consulta SQL correspondente. Teste um país e um intervalo de datas. Verifique tipos de IDs e campos de data, para evitar agregações e filtros incorretos.

## Publicar

No compartilhamento do relatório, habilite visualização por qualquer pessoa com o link, conforme as opções permitidas pela conta. Abra o link em janela anônima e confirme que o relatório carrega sem solicitar login. Cole o link real no README e no perfil apenas depois dessa validação.

Referências oficiais consultadas:
- https://docs.cloud.google.com/data-studio/upload-csv-files
- https://docs.cloud.google.com/data-studio/ways-to-share-your-reports
