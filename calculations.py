# calculations.py

def format_currency_br(value):
    """
    Formata um número para o padrão brasileiro de moeda.
    Exemplo: 1000.5 -> '1.000,50'
    """
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_currency_br(value):
    """
    Converte uma string no formato brasileiro de moeda para float.
    Exemplo: '1.000,50' -> 1000.50
    """
    return float(value.replace(".", "").replace(",", "."))


# Melhorias aplicadas ao arquivo