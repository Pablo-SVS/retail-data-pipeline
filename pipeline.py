"""Reproducible UCI Online Retail -> pandas -> SQLite -> BI extracts."""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import logging
from pathlib import Path
import sqlite3
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

ROOT = Path(__file__).resolve().parent
URL = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
COLUMNS = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']


def extract(root: Path, refresh: bool = False) -> Path:
    raw = root / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / 'online-retail.zip'
    if refresh or not archive.exists():
        temporary = archive.with_suffix('.tmp')
        with urlopen(URL, timeout=120) as response, temporary.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with ZipFile(temporary) as source:
            if source.testzip() is not None:
                raise ValueError('Corrupted source archive')
        temporary.replace(archive)
    xlsx = raw / 'Online Retail.xlsx'
    with ZipFile(archive) as source:
        with source.open('Online Retail.xlsx') as stream, xlsx.open('wb') as output:
            output.write(stream.read())
    return xlsx


def transform(source: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if list(source.columns) != COLUMNS:
        raise ValueError(f'Unexpected source schema: {list(source.columns)}')
    df = source.copy()
    df.insert(0, 'source_row', range(2, len(df) + 2))
    for column in ['InvoiceNo', 'StockCode', 'Description', 'Country']:
        df[column] = df[column].astype('string').str.strip()
    df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='raise').astype('Int64').astype('string')
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    for column in ['Quantity', 'UnitPrice']:
        df[column] = pd.to_numeric(df[column], errors='coerce')
    # Preserve repeated source rows: the source provides no unique line identifier.
    duplicates = int(df.duplicated(subset=COLUMNS).sum())
    reason = pd.Series('', index=df.index, dtype='string')
    rules = {
        'missing_key': df['InvoiceNo'].isna() | df['StockCode'].isna() | df['InvoiceNo'].eq('') | df['StockCode'].eq(''),
        'invalid_date': df['InvoiceDate'].isna(),
        'invalid_quantity': df['Quantity'].isna() | df['Quantity'].eq(0) | df['Quantity'].mod(1).ne(0),
        'non_positive_price': df['UnitPrice'].isna() | df['UnitPrice'].le(0),
        'inconsistent_cancellation': df['InvoiceNo'].str.upper().str.startswith('C').fillna(False) & df['Quantity'].gt(0),
    }
    for label, mask in rules.items():
        reason.loc[mask.fillna(True)] += label + ';'
    rejected = df.loc[reason.ne('')].copy()
    rejected['rejection_reason'] = reason[reason.ne('')]
    clean = df.loc[reason.eq('')].copy()
    clean['Country'] = clean['Country'].fillna('Unknown').replace('', 'Unknown')
    clean['Description'] = clean['Description'].fillna('Unknown')
    clean['movement_type'] = clean['Quantity'].lt(0).map({True: 'credit', False: 'sale'})
    # Integer thousandths preserve prices such as 0.001 GBP, without binary drift.
    scaled = clean['UnitPrice'] * 1000
    if (scaled.sub(scaled.round()).abs() > 1e-6).any():
        raise ValueError('UnitPrice precision exceeds 3 decimals')
    clean['unit_price_mills'] = scaled.round().astype('int64')
    clean['Quantity'] = clean['Quantity'].astype('int64')
    clean['amount_mills'] = clean['unit_price_mills'] * clean['Quantity']
    clean['invoice_date'] = clean['InvoiceDate'].dt.strftime('%Y-%m-%d')
    clean['InvoiceDate'] = clean['InvoiceDate'].dt.strftime('%Y-%m-%d %H:%M:%S')
    for column in ['invoice_date', 'Country', 'CustomerID']:
        if clean.groupby('InvoiceNo')[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f'Invoice has conflicting {column}')
    report = {
        'source_rows': len(df), 'accepted_rows': len(clean), 'rejected_rows': len(rejected),
        'duplicate_candidate_rows_preserved': duplicates,
        'accepted_rows_without_customer': int(clean['CustomerID'].isna().sum()),
        'rejection_rule_counts': {k: int(v.fillna(True).sum()) for k, v in rules.items()},
        'gross_sales_mills': int(clean.loc[clean['movement_type'].eq('sale'), 'amount_mills'].sum()),
        'credits_mills': int(-clean.loc[clean['movement_type'].eq('credit'), 'amount_mills'].sum()),
        'net_movement_mills': int(clean['amount_mills'].sum()),
    }
    if len(df) != len(clean) + len(rejected) or clean.empty:
        raise ValueError('Row reconciliation failed or no valid rows')
    return clean, rejected, report


def load(clean: pd.DataFrame, rejected: pd.DataFrame, root: Path) -> dict:
    warehouse = root / 'data/warehouse'
    processed = root / 'data/processed'
    warehouse.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    temporary = warehouse / 'retail.tmp'
    temporary.unlink(missing_ok=True)
    with closing(sqlite3.connect(temporary)) as db:
        clean.to_sql('fact_invoice_line', db, index=False)
        rejected.to_sql('quarantine', db, index=False)
        db.executescript((ROOT / 'sql/model.sql').read_text(encoding='utf-8'))
        expected = int(clean['amount_mills'].sum())
        actual = db.execute('SELECT SUM(net_mills) FROM mart_invoice').fetchone()[0]
        if expected != actual:
            raise ValueError('Invoice mart financial reconciliation failed')
        for name in ['mart_invoice', 'mart_daily_country']:
            pd.read_sql_query(f'SELECT * FROM {name}', db).to_csv(processed / f'{name}.csv', index=False)
        counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                  for table in ['fact_invoice_line', 'quarantine', 'mart_invoice', 'mart_daily_country']}
    temporary.replace(warehouse / 'retail.sqlite')
    return counts


def run(root: Path, refresh: bool = False) -> dict:
    source = extract(root, refresh)
    logging.info('Reading %s', source)
    frame = pd.read_excel(source, engine='openpyxl', dtype={'InvoiceNo': 'string', 'StockCode': 'string'})
    clean, rejected, report = transform(frame)
    report['tables'] = load(clean, rejected, root)
    report['source_url'] = URL
    report['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    report['period_start'] = clean['invoice_date'].min()
    report['period_end'] = clean['invoice_date'].max()
    report['gross_sales_gbp'] = report['gross_sales_mills'] / 1000
    report['credits_gbp'] = report['credits_mills'] / 1000
    report['net_movement_gbp'] = report['net_movement_mills'] / 1000
    (root / 'data/processed/quality_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    logging.info('Completed: %s', json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=Path, default=ROOT)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    run(args.data_root, args.refresh)
