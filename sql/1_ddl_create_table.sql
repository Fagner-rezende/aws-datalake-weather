-- Criação do Banco de Dados
CREATE DATABASE IF NOT EXISTS db_clima_fagner;

-- Criação da Tabela Externa (Aponta para o S3)
CREATE EXTERNAL TABLE IF NOT EXISTS db_clima_fagner.tbl_clima (
  `name` string,
  `id` int,
  `timezone` int,
  `dt` bigint,
  `base` string,
  `visibility` int,
  `ingestion_date` timestamp,
  -- Campos renomeados (ponto substituído por underline)
  `coord_lon` double,
  `coord_lat` double,
  `main_temp` double,
  `main_feels_like` double,
  `main_temp_min` double,
  `main_temp_max` double,
  `main_pressure` int,
  `main_humidity` int,
  `wind_speed` double,
  `wind_deg` int,
  `sys_country` string,
  `sys_sunrise` bigint,
  `sys_sunset` bigint,
  `clouds_all` int
)
PARTITIONED BY (
  `ano` string,
  `mes` string, 
  `dia` string
)
STORED AS PARQUET
LOCATION 's3://SEU-BUCKET-AQUI/silver/'
TBLPROPERTIES ("parquet.compression"="SNAPPY");

-- Comando vital para reconhecer novas partições
MSCK REPAIR TABLE db_clima_fagner.tbl_clima;