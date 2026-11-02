# Regras de negócio

1. Chave de documento/item ausente, data inválida, quantidade nula/zero/fracionária, preço nulo/não positivo e cancelamento C com quantidade positiva vão para quarentena.
2. ID de cliente inválido ou fracionário e preço com mais de três casas interrompem a execução: são violações de contrato que exigem investigação.
3. Vendas brutas = soma dos valores positivos das linhas aceitas. Créditos = módulo da soma das linhas negativas aceitas. Movimentação líquida = vendas brutas − créditos.
4. Ticket médio bruto = vendas brutas / documentos com venda. Não dividir pelo total de documentos que inclui cancelamentos.
5. Participação dos créditos = créditos / vendas brutas, no mesmo filtro de período e país. Não é taxa de devolução por coorte: um crédito pode se referir a venda anterior ao período.
6. Quantidade vendida e quantidade creditada são medidas separadas; não atribuir significado financeiro a linhas com preço zero rejeitadas.
7. Créditos sem prefixo C continuam classificados pela quantidade negativa. A nomenclatura evita assumir que todos são devoluções.
8. Códigos de frete, taxas e ajustes com quantidade/preço válidos permanecem na movimentação; o projeto não classifica receita exclusivamente de mercadorias.
9. Duplicatas candidatas são preservadas. A fonte não permite provar se são repetições acidentais ou lançamentos distintos.
10. A base termina em 09/12/2011. Dezembro de 2011 é incompleto; não comparar com meses completos como se fosse queda real de vendas.

## Limites de interpretação

Não há custo, lucro, margem, estoque, identificação nominal de cliente nem vínculo garantido entre venda e crédito. Não inferir esses indicadores. Os valores representam movimentação dos registros aceitos, não demonstração contábil auditada ou faturamento líquido fiscal.

## Evolução possível

Migrar o modelo para PostgreSQL, adicionar dimensões conformadas e publicar em uma camada cloud conectada ao BI. Uma carga incremental só deve ser adicionada quando a fonte oferecer chave estável e semântica de atualização; esta base é um snapshot histórico.
