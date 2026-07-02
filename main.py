import pandas as pd
import requests
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def gerar_dados_simulados():
    # Função de fallback com dados de contingência
    return [
        {"src_ip": "10.0.50.10", "dst_ip": "10.0.20.10", "packets": 1, "bytes": 2048},
        {"src_ip": "10.0.50.10", "dst_ip": "10.0.30.10", "packets": 1, "bytes": 320},
        {"src_ip": "10.0.60.10", "dst_ip": "10.0.20.10", "packets": 3, "bytes": 4500},
        {"src_ip": "10.0.60.10", "dst_ip": "10.0.60.20", "packets": 1, "bytes": 64},
        {"src_ip": "10.0.60.20", "dst_ip": "10.0.20.10", "packets": 2, "bytes": 9000},
        {"src_ip": "10.0.60.20", "dst_ip": "10.0.30.10", "packets": 1, "bytes": 850}
    ]

@app.get("/gerar-matriz")
def calcular_matriz():
    try:
        # Tenta buscar os dados reais na VM1 passando Usuário e Senha
        resposta = requests.get('http://10.0.20.10/api/v1/flows/', auth=('admin', 'admin123'), timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        status_origem = "REAL (Dados Coletados da VM1)"
        
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        # Captura de forma resiliente quedas de rede ou erro de autenticação
        dados = gerar_dados_simulados()
        status_origem = "SIMULADO (Fallback Ativo - VM1 Offline ou Bloqueada)"

    # --- PROCESSAMENTO DOS DADOS COM PANDAS ---
    df = pd.DataFrame(dados)

    # Normalização dos tipos de dados para evitar erros de agregação
    df['packets'] = pd.to_numeric(df.get('packets', 0), errors='coerce').fillna(0).astype(int)
    df['bytes'] = pd.to_numeric(df.get('bytes', 0), errors='coerce').fillna(0).astype(int)

    # Agrupamento Lógico por Fluxo (Origem -> Destino) somando métricas
    df_agrupado = df.groupby(['src_ip', 'dst_ip'], as_index=False).agg({
        'packets': 'sum',
        'bytes': 'sum'
    })

    # Tradução do vocabulário da VM1 para o contrato esperado pela Dashboard
    df_agrupado = df_agrupado.rename(columns={
        'src_ip': 'ip_origem',
        'dst_ip': 'ip_destino',
        'packets': 'qtd_pacotes',
        'bytes': 'volume_total_bytes'
    })

    # Conversão do DataFrame estruturado para JSON nativo
    matriz_trafego = df_agrupado.to_dict(orient="records")

    return {
        "status_origem_dados": status_origem,
        "matriz_de_trafego": matriz_trafego
    }

if __name__ == "__main__":
    # Escuta em todas as interfaces na porta 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
