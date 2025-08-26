# tests/test_integration_saidas.py
"""
Teste de integração para o fluxo completo de saídas.
"""

import tempfile
import pandas as pd
from pathlib import Path

from estoque.adapters.gds_loader import load_saidas_from_xlsx
from estoque.usecases.registrar_saida import run_saida_lote
from estoque.infra.migrations import apply_migrations
from estoque.infra.repositories import ProdutoRepo
import sqlite3


def test_integration_saidas_xlsx_to_db():
    """Teste integração completo: XLSX -> load_saidas_from_xlsx -> run_saida_lote -> DB"""
    
    # 1. Criar arquivo Excel de teste
    test_data = {
        'Data Saída': ['2024-01-15', '2024-01-16'],
        'Código': ['MED001', 'MED002'],
        'Quantidade': ['1 FR', '2 CP'],
        'Lote': ['L001', 'L002'],
        'Data Validade': ['2025-12-31', '2025-06-30'],
        'Custo': ['10.50', '25.00'],
        'Paciente': ['João Silva', 'Maria Santos'],
        'Nome do Produto': ['Medicamento A', 'Medicamento B'],
        'Descarte': ['não', 'sim']
    }
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df = pd.DataFrame(test_data)
        df.to_excel(tmp_file.name, index=False)
        xlsx_path = tmp_file.name
    
    # 2. Preparar banco de dados
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Aplicar migrações
        apply_migrations(db_path)
        
        # Criar produtos para satisfazer FK constraints
        prod_repo = ProdutoRepo(db_path)
        prod_repo.upsert([
            {
                'codigo': 'MED001',
                'nome': 'Medicamento A',
                'categoria': 'Medicamento',
                'controle_lotes': 1,
                'controle_validade': 1,
                'lote_min': 1.0,
                'lote_mult': 1.0,
                'quantidade_minima': 0.0
            },
            {
                'codigo': 'MED002', 
                'nome': 'Medicamento B',
                'categoria': 'Medicamento',
                'controle_lotes': 1,
                'controle_validade': 1,
                'lote_min': 1.0,
                'lote_mult': 1.0,
                'quantidade_minima': 0.0
            }
        ])
        
        # 3. Executar o fluxo completo
        result = run_saida_lote(xlsx_path, db_path)
        
        # 4. Verificações
        assert result['linhas_inseridas'] == 2
        
        # Verificar dados no banco
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT * FROM saida ORDER BY codigo")
            rows = cursor.fetchall()
            
            # Deve ter 2 registros
            assert len(rows) == 2
            
            # Verificar estrutura da primeira linha
            cursor = conn.execute("SELECT codigo, produto, paciente, descarte_flag FROM saida WHERE codigo = 'MED001'")
            row = cursor.fetchone()
            assert row[0] == 'MED001'  # codigo
            assert row[1] == 'Medicamento A'  # produto
            assert row[2] == 'João Silva'  # paciente
            assert row[3] == 0  # descarte_flag
            
            # Verificar segunda linha
            cursor = conn.execute("SELECT codigo, produto, descarte_flag FROM saida WHERE codigo = 'MED002'")
            row = cursor.fetchone()
            assert row[0] == 'MED002'
            assert row[1] == 'Medicamento B'
            assert row[2] == 1  # descarte_flag = sim
            
            # Verificar que não há campo responsavel
            cursor = conn.execute("PRAGMA table_info(saida)")
            columns = [row[1] for row in cursor.fetchall()]
            assert 'produto' in columns
            assert 'responsavel' not in columns
    
    finally:
        # Limpeza
        Path(xlsx_path).unlink()
        Path(db_path).unlink()