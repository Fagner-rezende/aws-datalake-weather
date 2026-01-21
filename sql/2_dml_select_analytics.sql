-- Análise Exploratória: Temperatura acima de 20 graus
SELECT 
  name as cidade,
  main_temp as temperatura,
  main_humidity as humidade,
  from_unixtime(dt) as data_medicao,
  processed_at
FROM db_clima_fagner.tbl_clima
WHERE main_temp > 20
ORDER BY processed_at DESC
LIMIT 50;