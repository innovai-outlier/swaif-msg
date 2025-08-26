# tests/test_saida_migration.py
"""
Testes para verificar migração da tabela saida.
"""

import tempfile
import sqlite3
from pathlib import Path

from estoque.infra.migrations import apply_migrations
from estoque.infra.repositories import SaidaRepo


def test_saida_table_has_produto_not_responsavel():
    """Testa que a tabela saida tem coluna 'produto' e não tem 'responsavel' após migração."""
    # Criar banco temporário
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Aplicar migrações
        apply_migrations(tmp_path)
        
        # Verificar estrutura da tabela
        with sqlite3.connect(tmp_path) as conn:
            cursor = conn.execute("PRAGMA table_info(saida)")
            columns = [row[1] for row in cursor.fetchall()]  # row[1] é o nome da coluna
            
            # Verificar que tem coluna 'produto'
            assert 'produto' in columns
            
            # Verificar que NÃO tem coluna 'responsavel'
            assert 'responsavel' not in columns
            
            # Verificar outras colunas esperadas
            expected_columns = [
                'id', 'data_saida', 'codigo', 'quantidade_raw', 'lote',
                'data_validade', 'custo', 'paciente', 'produto', 'descarte_flag'
            ]
            for col in expected_columns:
                assert col in columns, f"Coluna '{col}' não encontrada na tabela saida"
    
    finally:
        Path(tmp_path).unlink()


def test_saida_repo_insert_with_produto():
    """Testa que SaidaRepo.insert funciona com campo 'produto'."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        apply_migrations(tmp_path)
        
        # Primeiro, criar um produto para satisfazer a constraint de FK
        with sqlite3.connect(tmp_path) as conn:
            conn.execute("""
                INSERT INTO produto (codigo, nome, categoria)
                VALUES ('PROD001', 'Produto Teste', 'Medicamento')
            """)
        
        repo = SaidaRepo(tmp_path)
        
        # Dados de teste
        saida_data = {
            'data_saida': '2024-01-15',
            'codigo': 'PROD001',
            'quantidade_raw': '1 FR',
            'lote': 'L001',
            'data_validade': '2025-12-31',
            'custo': '10.50',
            'paciente': 'João Silva',
            'produto': 'Medicamento A',
            'descarte_flag': 0
        }
        
        # Inserir registro
        repo.insert(saida_data)
        
        # Verificar que foi inserido corretamente
        with sqlite3.connect(tmp_path) as conn:
            cursor = conn.execute("SELECT * FROM saida WHERE codigo = ?", ('PROD001',))
            row = cursor.fetchone()
            assert row is not None
            
            # Verificar que dados foram salvos
            cursor = conn.execute(
                "SELECT produto, codigo, paciente FROM saida WHERE codigo = ?", 
                ('PROD001',)
            )
            row = cursor.fetchone()
            assert row[0] == 'Medicamento A'  # produto
            assert row[1] == 'PROD001'        # codigo
            assert row[2] == 'João Silva'     # paciente
    
    finally:
        Path(tmp_path).unlink()