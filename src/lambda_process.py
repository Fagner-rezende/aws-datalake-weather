"""
Módulo: Processamento e Refinamento (Silver Layer)
Descrição: Trigger S3 -> Converte JSON para Parquet (Colunar) -> Higienização de Schema.
Stack: AWS Lambda + Pandas (Layer) + PyArrow
"""

import json
import urllib.parse
import boto3
import pandas as pd
import io
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    logger.info("🚀 Starting Silver Processing (JSON -> Parquet)...")

    try:
        # 1. Parse Event (S3 Trigger)
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        # Decodifica URL (ex: "Sao%20Paulo" -> "Sao Paulo")
        bronze_key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')

        logger.info(f"📂 Processing file: {bronze_key}")

        # 2. Extract (Read from Bronze)
        response = s3_client.get_object(Bucket=bucket_name, Key=bronze_key)
        json_content = json.loads(response['Body'].read().decode('utf-8'))

        # 3. Transform (Pandas Magic)
        # Flattening: Transforma JSON aninhado em tabela flat
        df = pd.json_normalize(json_content)
        
        # Data Quality: Remove pontos dos nomes das colunas (Incompatível com SQL/Athena)
        df.columns = df.columns.str.replace('.', '_')
        
        # Add Metadata
        df['processed_at'] = datetime.now()
        
        # Type Casting (Segurança de Tipagem)
        if 'id' in df.columns:
            df['id'] = df['id'].astype(int)

        # 4. Load (Write to Silver as Parquet)
        silver_key = bronze_key.replace('bronze/', 'silver/').replace('.json', '.parquet')
        
        # In-Memory Buffer (Evita IO de disco no Lambda)
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow', compression='snappy')
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=silver_key,
            Body=parquet_buffer.getvalue()
        )

        logger.info(f"✅ Transformed & Saved: s3://{bucket_name}/{silver_key}")
        return {'statusCode': 200, 'body': "Silver Processing Done"}

    except Exception as e:
        logger.error(f"❌ Error processing {bronze_key}: {str(e)}")
        raise e