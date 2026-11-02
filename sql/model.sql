CREATE UNIQUE INDEX ix_source_row ON fact_invoice_line(source_row);
CREATE INDEX ix_invoice ON fact_invoice_line(InvoiceNo);
CREATE INDEX ix_date_country ON fact_invoice_line(invoice_date, Country);

CREATE VIEW mart_invoice AS
SELECT InvoiceNo AS invoice_id,
       invoice_date,
       Country AS country,
       CustomerID AS customer_id,
       COUNT(*) AS line_count,
       SUM(CASE WHEN movement_type = 'sale' THEN Quantity ELSE 0 END) AS units_sold,
       SUM(CASE WHEN movement_type = 'credit' THEN -Quantity ELSE 0 END) AS units_credited,
       MAX(CASE WHEN movement_type = 'sale' THEN 1 ELSE 0 END) AS sale_invoice_count,
       MAX(CASE WHEN movement_type = 'credit' THEN 1 ELSE 0 END) AS credit_invoice_count,
       SUM(CASE WHEN movement_type = 'sale' THEN amount_mills ELSE 0 END) AS gross_mills,
       SUM(CASE WHEN movement_type = 'credit' THEN -amount_mills ELSE 0 END) AS credit_mills,
       SUM(amount_mills) AS net_mills,
       SUM(CASE WHEN movement_type = 'sale' THEN amount_mills ELSE 0 END) / 1000.0 AS gross_sales_gbp,
       SUM(CASE WHEN movement_type = 'credit' THEN -amount_mills ELSE 0 END) / 1000.0 AS credits_gbp,
       SUM(amount_mills) / 1000.0 AS net_movement_gbp
FROM fact_invoice_line
GROUP BY InvoiceNo, invoice_date, Country, CustomerID;

CREATE VIEW mart_daily_country AS
SELECT invoice_date, country,
       SUM(sale_invoice_count) AS sale_invoice_count,
       SUM(credit_invoice_count) AS credit_invoice_count,
       SUM(units_sold) AS units_sold,
       SUM(units_credited) AS units_credited,
       SUM(gross_mills) / 1000.0 AS gross_sales_gbp,
       SUM(credit_mills) / 1000.0 AS credits_gbp,
       SUM(net_mills) / 1000.0 AS net_movement_gbp
FROM mart_invoice
GROUP BY invoice_date, country;
