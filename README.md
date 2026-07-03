# Motor Analítico (VM6) - Plataforma Distribuída de Redes

**Aluno:** Matheus Pissarra Lauer  
**Instituição:** Instituto Federal do Espírito Santo (IFES) - Campus Guarapari  
**Curso:** Engenharia Elétrica  
**Disciplina:** Laboratório de Redes  

---

## 1. Objetivos
O objetivo deste projeto é a implementação da máquina virtual VM6, designada como "Motor Analítico". A VM6 atua como o processador central (*middleware*) da topologia de rede, responsável por consumir os fluxos brutos capturados, agregar as informações por IP de origem e destino, e gerar uma Matriz de Tráfego otimizada em formato JSON para consumo dos módulos de Dashboard (VM2) e Alertas (VM7).

## 2. Arquitetura
A VM6 foi instanciada no ambiente OpenStack, posicionada na VLAN 20 (Rede Server) com o IP interno `10.0.20.20`. A arquitetura foi estruturada em três pilares em Python 3:
* **Camada de Ingestão:** Consome a API REST da VM1 (`10.0.20.10`) utilizando a biblioteca `requests`, transpondo a autenticação do Proxy Reverso.
* **Camada de Processamento:** Utiliza a biblioteca `pandas` para transformar milhares de pacotes brutos em um *DataFrame* e calcular a volumetria agregada.
* **Camada de Serviço:** Um servidor web assíncrono construído com `FastAPI` e `uvicorn` rodando continuamente na porta 8000.

## 3. Configuração Realizada
O ambiente foi preparado em Ubuntu. A configuração base consistiu em:
* Instalação do gerenciador `pip` e das bibliotecas: `pandas`, `fastapi`, `uvicorn`, `requests`.
* Criação do diretório de produção em `/opt/motor_analitico/`.
* Criação e habilitação de um *daemon* nativo do Linux (`motor.service` no *systemd*) para garantir que a API funcione como um serviço de *background* resiliente.

## 4. Comandos Utilizados
Os principais comandos de implantação executados no console do OpenStack foram:

### Atualização e Instalação de Dependências
```bash
apt update && apt install python3-pip -y
pip3 install pandas fastapi uvicorn requests
```

### Criação do ambiente
```Bash

mkdir -p /opt/motor_analitico
cd /opt/motor_analitico
nano main.py
```

Gerenciamento do Serviço (Daemon)
```
systemctl daemon-reload
systemctl enable motor.service
systemctl start motor.service
```

## 5. Acesso e Navegação de Rede

### Navegação via SSH

O ambiente do projeto estava dentro de uma nuvem privada (OpenStack), o que exigiu a realização de saltos entre as máquinas para chegar ao destino.

Acesso à máquina ponte (Jump Host / Máquina do Joab-VM11):
```
ssh root@10.10.1.22
```
Inicia uma conexão segura (Secure Shell) a partir do computador físico do laboratório para a máquina que serve como porta de entrada da nuvem.

Acesso à VM6 (Motor Analítico):
```  
ssh root@10.0.20.20
```
Uma vez dentro da máquina ponte, este comando faz um novo salto para a máquina virtual isolada na rede interna da nuvem (VLAN 20).

### Túneis SSH (Port Forwarding)
Como as máquinas virtuais possuíam IPs privados, o navegador físico não conseguia acessá-las diretamente. A solução foi criar túneis.


### Túnel para acessar a API Central (VM1):
```
ssh -L 8080:10.0.20.10:80 root@10.10.1.22
```
Mapeia a porta 8080 do localhost (PC físico) para a porta 80 da VM1 (10.0.20.10), passando por dentro da máquina ponte.


### Túnel para acessar a API do Motor (VM6):
 ```
ssh -L 8000:10.0.20.20:8000 root@10.10.1.22
 ```
Mapeia a porta 8000 do localhost para a porta 8000 da VM6 (10.0.20.20), permitindo visualizar a Matriz de Tráfego final pelo navegador do laboratório.


## 6. O Código do Motor Analítico (main.py)

Foi desenvolvido em Python. O script atua como uma API RESTful que consome os dados da VM1, normaliza, agrupa e exporta para JSON.
```
Python

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
        # Tenta buscar os dados reais na VM1 com Autenticação Básica
        resposta = requests.get('[http://10.0.20.10/api/v1/flows/](http://10.0.20.10/api/v1/flows/)', auth=('admin', 'admin123'), timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        status_origem = "REAL (Dados Coletados da VM1)"
        
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        # Captura de forma resiliente falhas de rede ou erro de proxy
        dados = gerar_dados_simulados()
        status_origem = "SIMULADO (Fallback Ativo - VM1 Offline ou Bloqueada)"

    # Processamento com Pandas (Normalização e Agrupamento)
    df = pd.DataFrame(dados)
    df['packets'] = pd.to_numeric(df.get('packets', 0), errors='coerce').fillna(0).astype(int)
    df['bytes'] = pd.to_numeric(df.get('bytes', 0), errors='coerce').fillna(0).astype(int)

    df_agrupado = df.groupby(['src_ip', 'dst_ip'], as_index=False).agg({
        'packets': 'sum',
        'bytes': 'sum'
    })

    df_agrupado = df_agrupado.rename(columns={
        'src_ip': 'ip_origem',
        'dst_ip': 'ip_destino',
        'packets': 'qtd_pacotes',
        'bytes': 'volume_total_bytes'
    })

    return {
        "status_origem_dados": status_origem,
        "matriz_de_trafego": df_agrupado.to_dict(orient="records")
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## 7. Serviço de Background (systemd)

Para garantir a alta disponibilidade da aplicação, o código não é executado diretamente no terminal, mas sim acoplado ao gerenciador de serviços do Linux. Foi criado o arquivo /etc/systemd/system/motor.service:

```
[Unit]
Description=API Motor Analitico - Equipe de Redes (VM6)
After=network.target

[Service]
User=root
WorkingDirectory=/opt/motor_analitico
ExecStart=/opt/motor_analitico/venv/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Verificação do status de saúde do serviço:
```
systemctl status motor.service
```


## 8. Tolerância a Falhas e Resiliência

Um requisito fundamental atendido no projeto foi a resiliência a quedas de rede. O script foi projetado com blocos try-except que identificam anomalias na comunicação com a API Central (Timeout, Erro 401 de Autenticação ou Queda de Conexão). Caso a VM1 fique inacessível, o sistema não "quebra", mas simula uma tabela de roteamento de contingência para manter as Dashboards funcionando (Fallback).


## 9. Testes e Validações Finais

Antes de expor a API para a rede externa, o sistema foi validado internamente via linha de comando (CLI) na própria máquina:

```
curl -s http://localhost:8000/gerar-matriz
```

O resultado final, acessado via túnel SSH no navegador, comprova a ingestão e agregação dos dados reais da rede, formatados em JSON:
