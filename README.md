# Meta Prediction

## Introdução

**Meta Prediction** é uma aplicação web desenvolvida para auxiliar usuários no gerenciamento de bancas de apostas ou investimentos. A plataforma permite o controle de saldos financeiros, definição de metas, adição de transações (depósitos e saques) e a visualização de progresso financeiro por meio de gráficos intuitivos.


---

## Funcionalidades Principais

1. **Gestão de Metas Financeiras:** Defina e acompanhe metas financeiras de forma simples.
2. **Adição de Transações:** Registre depósitos e saques rapidamente.
3. **Visualização Gráfica:** Acompanhe a evolução do saldo por meio de gráficos intuitivos.
4. **Autenticação Segura:** Login e gerenciamento de usuários.

---

## Guia de Instalação e Configuração

### Pré-requisitos

Certifique-se de ter instalado:

- Python 3.8+
- Pip (gerenciador de pacotes do Python)
- Virtualenv (opcional, mas recomendado)

### Passo a Passo

1. Clone o repositório:

   ```bash
   git clone https://github.com/NiellCast/meta_prediction.git
   cd meta_prediction
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate # Linux/Mac
   venv\Scripts\activate   # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure o banco de dados:

   ```bash
   python initialize_db.py
   ```

5. Inicie o servidor:

   ```bash
   python main.py
   ```

6. Acesse a aplicação no navegador em [http://localhost:5000](http://localhost:5000).

---

## Arquitetura do Projeto

A estrutura do projeto é modular e organizada da seguinte forma:

- **Frontend:** Desenvolvido com HTML, CSS e JavaScript para garantir uma interface responsiva e amigável ao usuário.
  - `static/`: Contém arquivos estáticos como CSS, JavaScript e imagens.
  - `templates/`: Contém os templates HTML que são renderizados pelo Flask.

- **Backend:** Baseado em Flask, utiliza SQLAlchemy como ORM e SQLite como banco de dados.
  - `main.py`: Ponto de entrada da aplicação.
  - `models.py`: Define os modelos de dados da aplicação.
  - `database.py`: Configuração e conexão com o banco de dados.
  - `banca_services.py`: Lógica de negócios relacionada às transações e metas.

- **Testes:**
  - `tests/`: Contém os testes automatizados escritos com pytest.

---

## Rodando os Testes

1. Certifique-se de que todas as dependências estão instaladas.

2. Execute os testes com o seguinte comando:

   ```bash
   pytest tests/
   ```

3. Para gerar um relatório de cobertura de testes:

   ```bash
   pytest --cov=.
   ```

---
