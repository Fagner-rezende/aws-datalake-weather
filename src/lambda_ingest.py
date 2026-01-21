"""
Módulo: Ingestão de Dados Climáticos (Bronze Layer)
Descrição: Coleta dados da API OpenWeatherMap e armazena em formato JSON Raw no S3.
Autor: Fagner Rezende
Data: 2026-01-20
"""

import json
import urllib3
import os
import boto3
import logging
from datetime import datetime, timezone, timedelta

# Configuração de Logging Profissional
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Instâncias globais (Pattern: Singleton/Warm Start)
s3_client = boto3.client('s3')
http = urllib3.PoolManager()

def lambda_handler(event, context):
    """
    Função principal acionada pelo AWS EventBridge (Agendamento).
    
    Flow:
    1. Carrega variáveis de ambiente (Segurança).
    2. Request na API OpenWeather.
    3. Calcula data com fuso horário (BRT).
    4. Persiste no S3 com particionamento Hive (ano/mes/dia).
    """
    logger.info("🚀 Starting Bronze Ingestion...")

    try:
        # 1. Configurações de Ambiente (Environment Variables)
        # NUNCA colocar chaves hardcoded no código (Segurança)
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        bucket_name = os.environ.get('BUCKET_NAME')
        city = os.environ.get('CITY_NAME', 'Sao Paulo') # Default seguro

        if not api_key or not bucket_name:
            raise ValueError("❌ Erro de Configuração: Variáveis de ambiente ausentes.")

        # 2. Extract (API Call)
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        url = f"{base_url}?q={city}&appid={api_key}&units=metric"
        
        response = http.request('GET', url)
        data = json.loads(response.data.decode('utf-8'))
        
        if response.status != 200:
            raise Exception(f"API Error: {data.get('message', 'Unknown error')}")

        # 3. Transform (Timezone Aware Partitioning)
        # Ajuste para UTC-3 (Brasília)
        br_timezone = timezone(timedelta(hours=-3))
        now = datetime.now(br_timezone)

        partition_path = now.strftime("bronze/ano=%Y/mes=%m/dia=%d")
        filename = f"weather_{city.replace(' ', '_')}_{now.strftime('%H%M%S')}.json"
        full_path = f"{partition_path}/{filename}"

        # 4. Load (S3 Storage)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=full_path,
            Body=json.dumps(data),
            ContentType='application/json'
        )
        
        logger.info(f"💾 Ingestão concluída com sucesso: s3://{bucket_name}/{full_path}")
        
        return {
            'statusCode': 200, 
            'body': json.dumps({'message': 'Ingestion Successful', 'path': full_path})
        }

    except Exception as e:
        logger.error(f"❌ Critical Failure: {str(e)}")
        raise e