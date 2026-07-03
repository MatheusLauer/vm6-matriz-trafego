# Motor Analítico (VM6) - Plataforma Distribuída de Redes

**Aluno:** Matheus Pissarra Lauer 
**Disciplina:** Laboratório de Redes  

---

##  1. Objetivos
O objetivo deste projeto é a implementação da máquina virtual VM6, designada como "Motor Analítico". A VM6 atua como o processador central (*middleware*) da topologia de rede, responsável por consumir os fluxos brutos capturados, agregar as informações por IP de origem e destino, e gerar uma Matriz de Tráfego otimizada em formato JSON para consumo dos módulos de Dashboard (VM2) e Alertas (VM7).

##  2. Arquitetura
A VM6 foi instanciada no ambiente OpenStack, posicionada na VLAN 20 (Rede Server) com o IP interno `10.0.20.20`. A arquitetura foi estruturada em três pilares em Python 3:
* **Camada de Ingestão:** Consome a API REST da VM1 (`10.0.20.10`) utilizando a biblioteca `requests`, transpondo a autenticação do Proxy Reverso.
* **Camada de Processamento:** Utiliza a biblioteca `pandas` para transformar milhares de pacotes brutos em um *DataFrame* e calcular a volumetria agregada.
* **Camada de Serviço:** Um servidor web assíncrono construído com `FastAPI` e `uvicorn` rodando continuamente na porta 8000.

##  3. Configuração Realizada
O ambiente foi preparado em Ubuntu. A configuração base consistiu em:
* Instalação do gerenciador `pip` e das bibliotecas: `pandas`, `fastapi`, `uvicorn`, `requests`.
* Criação do diretório de produção em `/opt/motor_analitico/`.
* Criação e habilitação de um *daemon* nativo do Linux (`motor.service` no *systemd*) para garantir que a API funcione como um serviço de *background* resiliente.

##  4. Comandos Utilizados
Os principais comandos de implantação executados no console do OpenStack foram:

### Atualização e Instalação de Dependências
apt update && apt install python3-pip -y
pip3 install pandas fastapi uvicorn requests

### Criação do ambiente
mkdir -p /opt/motor_analitico
cd /opt/motor_analitico
nano main.py

### Gerenciamento do Serviço (Daemon)
systemctl daemon-reload
systemctl enable motor.service
systemctl start motor.service


5. Acesso e Navegação de Rede
1. Navegação via SSH

O ambiente do projeto estava dentro de uma nuvem privada (OpenStack), o que exigiu que você fizesse saltos entre as máquinas para chegar ao seu destino.

Acesso à máquina ponte (Jump Host / Máquina do Joab-VM11):
Bash

ssh root@10.10.1.22

    O que faz: Inicia uma conexão segura (Secure Shell) a partir do seu computador físico do laboratório para a máquina que serve como porta de entrada da nuvem.

Acesso à sua máquina (VM6 - Motor Analítico):
Bash

ssh root@10.0.20.20

    O que faz: Uma vez dentro da máquina ponte, este comando faz um novo salto para a sua máquina virtual isolada na rede interna da nuvem (VLAN 20).

2. Túneis SSH (Port Forwarding)

Como as máquinas virtuais possuíam IPs privados, o navegador físico não conseguia acessá-las diretamente. A solução foi criar túneis.

Túnel para acessar a API Central (VM1):
Bash

ssh -L 8080:10.0.20.10:80 root@10.10.1.22

    O que faz: Mapeia a porta 8080 do seu localhost (PC físico) para a porta 80 da VM1 (10.0.20.10), passando por dentro da máquina ponte (10.10.1.22).

Túnel para acessar a sua API (VM6):
Bash

ssh -L 8000:10.0.20.20:8000 root@10.10.1.22

    O que faz: Mapeia a porta 8000 do seu localhost para a porta 8000 da sua VM6 (10.0.20.20). Isso permitiu visualizar a sua Matriz de Tráfego final pelo Navegador do laboratório.
