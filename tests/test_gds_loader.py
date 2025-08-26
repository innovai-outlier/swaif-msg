# tests/test_gds_loader.py
"""
Testes para o módulo gds_loader.
"""

import tempfile
import pandas as pd
from pathlib import Path

from estoque.adapters.gds_loader import load_saidas_from_xlsx, load_entradas_from_xlsx


def test_load_saidas_from_xlsx_with_produto_field():
    """Testa que load_saidas_from_xlsx inclui campo 'produto' e não inclui 'responsavel'."""
    # Criar dados de teste
    test_data = {
        'Data Saída': ['2024-01-15', '2024-01-16'],
        'Código': ['PROD001', 'PROD002'],
        'Quantidade': ['1 FR', '2 CP'],
        'Lote': ['L001', 'L002'],
        'Data Validade': ['2025-12-31', '2025-06-30'],
        'Custo': ['10.50', '25.00'],
        'Paciente': ['João Silva', 'Maria Santos'],
        'Produto': ['Medicamento A', 'Medicamento B'],
        'Descarte': ['não', 'sim']
    }
    
    # Criar arquivo temporário Excel
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp_file.name, index=False)
        tmp_path = tmp_file.name
    
    try:
        # Executar função
        result = load_saidas_from_xlsx(tmp_path)
        
        # Verificações
        assert len(result) == 2
        
        # Primeiro registro
        first_record = result[0]
        assert first_record['data_saida'] == '2024-01-15'
        assert first_record['codigo'] == 'PROD001'
        assert first_record['quantidade_raw'] == '1 FR'
        assert first_record['lote'] == 'L001'
        assert first_record['data_validade'] == '2025-12-31'
        assert first_record['custo'] == '10.50'
        assert first_record['paciente'] == 'João Silva'
        assert first_record['produto'] == 'Medicamento A'
        assert first_record['descarte_flag'] == 0
        
        # Verificar que não tem campo 'responsavel'
        assert 'responsavel' not in first_record
        
        # Verificar que tem campo 'produto'
        assert 'produto' in first_record
        
        # Segundo registro
        second_record = result[1]
        assert second_record['produto'] == 'Medicamento B'
        assert second_record['descarte_flag'] == 1
        assert 'responsavel' not in second_record
        
    finally:
        # Limpar arquivo temporário
        Path(tmp_path).unlink()


def test_load_saidas_from_xlsx_produto_aliases():
    """Testa mapeamento de diferentes variações de nomes para 'produto'."""
    test_data = {
        'Nome': ['Produto via Nome'],
        'Código': ['PROD001'],
        'Quantidade': ['1 UN']
    }
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp_file.name, index=False)
        tmp_path = tmp_file.name
    
    try:
        result = load_saidas_from_xlsx(tmp_path)
        assert len(result) == 1
        assert result[0]['produto'] == 'Produto via Nome'
        assert 'responsavel' not in result[0]
    finally:
        Path(tmp_path).unlink()


def test_load_saidas_from_xlsx_empty_produto():
    """Testa comportamento quando campo produto está vazio."""
    test_data = {
        'Código': ['PROD001'],
        'Quantidade': ['1 UN'],
        'Produto': [None]  # Produto vazio
    }
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp_file.name, index=False)
        tmp_path = tmp_file.name
    
    try:
        result = load_saidas_from_xlsx(tmp_path)
        assert len(result) == 1
        assert result[0]['produto'] is None
        assert 'responsavel' not in result[0]
    finally:
        Path(tmp_path).unlink()