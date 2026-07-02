# Motor Analítico (VM6) - Plataforma Distribuída de Redes

**Aluno:** Matheus Pissarra Lauer 
**Disciplina:** Laboratório de Redes  

---

## 🎯 1. Objetivos
O objetivo deste projeto é a implementação da máquina virtual VM6, designada como "Motor Analítico". A VM6 atua como o processador central (*middleware*) da topologia de rede, responsável por consumir os fluxos brutos capturados, agregar as informações por IP de origem e destino, e gerar uma Matriz de Tráfego otimizada em formato JSON para consumo dos módulos de Dashboard (VM2) e Alertas (VM7).

## 🏗️ 2. Arquitetura
A VM6 foi instanciada no ambiente OpenStack, posicionada na VLAN 20 (Rede Server) com o IP interno `10.0.20.20`. A arquitetura foi estruturada em três pilares em Python 3:
* **Camada de Ingestão:** Consome a API REST da VM1 (`10.0.20.10`) utilizando a biblioteca `requests`, transpondo a autenticação do Proxy Reverso.
* **Camada de Processamento:** Utiliza a biblioteca `pandas` para transformar milhares de pacotes brutos em um *DataFrame* e calcular a volumetria agregada.
* **Camada de Serviço:** Um servidor web assíncrono construído com `FastAPI` e `uvicorn` rodando continuamente na porta 8000.

## ⚙️ 3. Configuração Realizada
O ambiente foi preparado em Ubuntu. A configuração base consistiu em:
* Instalação do gerenciador `pip` e das bibliotecas: `pandas`, `fastapi`, `uvicorn`, `requests`.
* Criação do diretório de produção em `/opt/motor_analitico/`.
* Criação e habilitação de um *daemon* nativo do Linux (`motor.service` no *systemd*) para garantir que a API funcione como um serviço de *background* resiliente.

## 💻 4. Comandos Utilizados
Os principais comandos de implantação executados no console do OpenStack foram:

```bash
# Atualização e Instalação de Dependências
apt update && apt install python3-pip -y
pip3 install pandas fastapi uvicorn requests

# Criação do ambiente
mkdir -p /opt/motor_analitico
cd /opt/motor_analitico
nano main.py

# Gerenciamento do Serviço (Daemon)
systemctl daemon-reload
systemctl enable motor.service
systemctl start motor.service
