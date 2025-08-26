#!/usr/bin/env python3
"""
Demo script to showcase the enhanced CLI features.
This script demonstrates:
1. Import success messages
2. Data visualization commands
3. Enhanced reporting
"""

import subprocess
import sys
import os
import pandas as pd
from datetime import date, timedelta

def run_command(cmd, description):
    """Run a CLI command and show its output."""
    print(f"\n{'='*60}")
    print(f"🔹 {description}")
    print(f"💻 Comando: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def create_demo_data():
    """Create larger demo datasets for testing."""
    print("📊 Criando dados de demonstração...")
    
    # Create larger entrada dataset
    entrada_data = {
        'codigo': ['MED001', 'MED002', 'MED003', 'MED004', 'MED005'] * 4,
        'quantidade': ['10 FR', '25 MG', '5 AMP', '100 ML', '50 CPR'] * 4,
        'data_entrada': [
            '2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19',
            '2024-01-20', '2024-01-21', '2024-01-22', '2024-01-23', '2024-01-24',
            '2024-01-25', '2024-01-26', '2024-01-27', '2024-01-28', '2024-01-29',
            '2024-01-30', '2024-01-31', '2024-02-01', '2024-02-02', '2024-02-03'
        ],
        'lote': [f'L{i:03d}' for i in range(1, 21)],
        'data_validade': [
            '2025-06-15', '2025-08-16', '2025-12-17', '2025-04-18', '2025-10-19',
            '2025-07-20', '2025-09-21', '2025-11-22', '2025-05-23', '2025-03-24',
            '2025-08-25', '2025-06-26', '2025-10-27', '2025-12-28', '2025-04-29',
            '2025-07-30', '2025-09-31', '2025-11-01', '2025-05-02', '2025-08-03'
        ],
        'valor_unitario': [
            '15.50', '8.75', '22.30', '12.00', '5.25',
            '16.00', '9.50', '23.75', '11.50', '5.80',
            '15.25', '8.90', '21.50', '12.25', '5.45',
            '16.75', '9.10', '24.00', '11.75', '6.00'
        ],
        'representante': [
            'Fornecedor A', 'Fornecedor B', 'Fornecedor C', 'Fornecedor D', 'Fornecedor E'
        ] * 4,
        'responsavel': [
            'João Silva', 'Maria Santos', 'Pedro Lima', 'Ana Costa', 'Carlos Souza'
        ] * 4,
        'pago': [1, 0, 1, 1, 0] * 4
    }
    
    # Create larger saida dataset
    saida_data = {
        'codigo': ['MED001', 'MED002', 'MED003', 'MED001', 'MED004'] * 3,
        'quantidade': ['2 FR', '5 MG', '1 AMP', '3 FR', '10 ML'] * 3,
        'data_saida': [
            '2024-01-20', '2024-01-21', '2024-01-22', '2024-01-23', '2024-01-24',
            '2024-01-25', '2024-01-26', '2024-01-27', '2024-01-28', '2024-01-29',
            '2024-01-30', '2024-01-31', '2024-02-01', '2024-02-02', '2024-02-03'
        ],
        'lote': [f'L{i:03d}' for i in range(1, 16)],
        'paciente': [
            'Paciente A', 'Paciente B', 'Paciente C', 'Paciente D', 'Paciente E'
        ] * 3,
        'responsavel': [
            'Dr. Ana', 'Dr. Carlos', 'Dr. Beatriz', 'Dr. Diego', 'Dr. Elena'
        ] * 3,
        'descarte': [0, 0, 0, 0, 1] * 3
    }
    
    # Save datasets
    pd.DataFrame(entrada_data).to_excel('/tmp/demo_entrada.xlsx', index=False)
    pd.DataFrame(saida_data).to_excel('/tmp/demo_saida.xlsx', index=False)
    
    print("✅ Datasets criados: /tmp/demo_entrada.xlsx e /tmp/demo_saida.xlsx")

def main():
    """Run the complete demo."""
    print("🚀 DEMO: Funcionalidades Aprimoradas do CLI do Sistema de Estoque")
    print("="*70)
    
    # Create demo data
    create_demo_data()
    
    # Initialize database
    run_command("python app.py migrate", "Inicializando banco de dados")
    
    # Add some products (needed for foreign key constraints)
    print("\n📦 Adicionando produtos necessários...")
    run_command("""python -c "
from estoque.infra.repositories import ProdutoRepo
from estoque.config import DB_PATH

produtos = [
    {'codigo': 'MED004', 'nome': 'Medicamento D', 'categoria': 'Vitamina', 
     'controle_lotes': 1, 'controle_validade': 1, 'quantidade_minima': 20.0},
    {'codigo': 'MED005', 'nome': 'Medicamento E', 'categoria': 'Suplemento', 
     'controle_lotes': 1, 'controle_validade': 1, 'quantidade_minima': 15.0}
]

repo = ProdutoRepo(DB_PATH)
repo.upsert(produtos)
print('✅ Produtos adicionais cadastrados!')
" """, "Cadastrando produtos adicionais")
    
    # Test import with success messages
    run_command("python app.py entrada-lotes /tmp/demo_entrada.xlsx", 
                "1. IMPORTAÇÃO DE ENTRADAS com mensagem de sucesso aprimorada")
    
    run_command("python app.py saida-lotes /tmp/demo_saida.xlsx", 
                "2. IMPORTAÇÃO DE SAÍDAS com mensagem de sucesso aprimorada")
    
    # Test data visualization commands
    run_command("python app.py lista resumo", 
                "3. VISUALIZAÇÃO: Resumo geral dos dados")
    
    run_command("python app.py lista entradas --limite 5", 
                "4. VISUALIZAÇÃO: Listagem das últimas 5 entradas")
    
    run_command("python app.py lista saidas --limite 5", 
                "5. VISUALIZAÇÃO: Listagem das últimas 5 saídas")
    
    # Test enhanced reports
    run_command("python app.py rel ruptura", 
                "6. RELATÓRIO APRIMORADO: Produtos em risco de ruptura")
    
    run_command("python app.py rel reposicao", 
                "7. RELATÓRIO APRIMORADO: Produtos para reposição")
    
    run_command("python app.py rel vencimentos --janela-dias 365", 
                "8. RELATÓRIO APRIMORADO: Produtos próximos ao vencimento")
    
    # Show JSON format option
    run_command("python app.py rel ruptura --formato json", 
                "9. RELATÓRIO EM JSON: Mesmo relatório em formato JSON")
    
    print(f"\n{'='*70}")
    print("✅ DEMO CONCLUÍDA!")
    print("📋 Resumo das funcionalidades implementadas:")
    print("   • Mensagens de sucesso aprimoradas para importações")
    print("   • Comandos de visualização de dados (lista)")
    print("   • Relatórios formatados com tabelas legíveis")
    print("   • Opção de formato JSON para relatórios")
    print("   • Tratamento de erros com mensagens claras")
    print("="*70)

if __name__ == "__main__":
    main()