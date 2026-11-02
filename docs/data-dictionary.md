# Contrato e dicionário de dados

A entrada deve conter exatamente as oito colunas abaixo, nesta ordem. Mudança de esquema interrompe a execução. Cada linha representa um registro de item na fonte, não um pedido completo.

| Campo original | Tipo tratado | Significado |
| --- | --- | --- |
| InvoiceNo | texto | Identificador do documento; prefixo C indica cancelamento na fonte |
| StockCode | texto | Código do item; códigos não numéricos são preservados |
| Description | texto | Descrição; ausências viram Unknown |
| Quantity | inteiro | Quantidade; negativos são créditos/ajustes |
| InvoiceDate | data/hora | Momento do documento, sem fuso informado pela fonte |
| UnitPrice | número | Preço unitário em GBP |
| CustomerID | texto anulável | Identificador do cliente; não é medida somável |
| Country | texto | País do cliente; ausências viram Unknown |

## fact_invoice_line

Conserva os campos originais normalizados e acrescenta:

| Campo | Tipo | Regra |
| --- | --- | --- |
| source_row | inteiro único | Número da linha do XLSX, com cabeçalho na linha 1 |
| movement_type | texto | sale se quantidade positiva; credit se negativa |
| unit_price_mills | inteiro | UnitPrice × 1000; precisão validada |
| amount_mills | inteiro | Quantity × unit_price_mills, com sinal |
| invoice_date | texto ISO | Data YYYY-MM-DD |

## quarantine

Campos normalizados da fonte, `source_row` e `rejection_reason`. Uma linha pode violar mais de uma regra; por isso a soma das contagens por regra pode superar o número de linhas rejeitadas. Não usar esta tabela nas métricas de vendas.

## mart_invoice

Uma linha por `invoice_id`. Antes da carga, o pipeline exige data, país e cliente consistentes dentro de cada documento. Os demais campos são `invoice_date`, `country`, `customer_id`, `line_count`, `units_sold`, `units_credited`, `sale_invoice_count`, `credit_invoice_count`, `gross_mills`, `credit_mills`, `net_mills`, `gross_sales_gbp`, `credits_gbp` e `net_movement_gbp`.

Os campos `*_mills` são inteiros em milésimos de GBP; os campos `*_gbp` são valores em libras. Vendas e créditos são positivos em suas próprias medidas. `net_movement_gbp = gross_sales_gbp - credits_gbp`.

`sale_invoice_count` vale 1 se o documento tem venda; `credit_invoice_count` vale 1 se tem crédito. Não chamar a quantidade total de documentos de quantidade de pedidos de venda.

## mart_daily_country

Uma linha por data e país. Soma as medidas aditivas de mart_invoice. Não inclui contagem de clientes únicos, pois somar clientes distintos por dia superestimaria o total do período.
