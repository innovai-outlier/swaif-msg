# estoque/adapters/cli.py
"""
CLI do sistema de estoque (Typer).

Comandos principais:
- migrate                 -> aplica migrações e cria views
- params set/get/show     -> gerencia parâmetros globais
- verificar               -> executa o caso de uso de verificação do estoque
- entrada-unica           -> registra uma entrada via prompts no terminal
- entrada-lotes <xlsx>    -> registra entradas em lote a partir de um XLSX
- saida-unica             -> registra uma saída via prompts no terminal
- saida-lotes <xlsx>      -> registra saídas em lote a partir de um XLSX
"""

from __future__ import annotations

import json
from typing import Optional, List

import typer
from tabulate import tabulate

from estoque.config import DB_PATH, DEFAULTS
from estoque.infra.migrations import apply_migrations
from estoque.infra.views import create_views
from estoque.infra.repositories import ParamsRepo
from estoque.usecases.verificar_estoque import run_verificar
from estoque.usecases.registrar_entrada import run_entrada_unica, run_entrada_lote
from estoque.usecases.registrar_saida import run_saida_unica, run_saida_lote
from estoque.usecases.relatorios import (
    relatorio_alerta_ruptura,
    relatorio_produtos_a_vencer,
    relatorio_mais_consumidos,
    relatorio_reposicao,
)



app = typer.Typer(help="Estoque Clínica — CLI")


# -----------------------
# util
# -----------------------

def _print_json(obj) -> None:
    typer.echo(json.dumps(obj, ensure_ascii=False, indent=2))


# -----------------------
# comandos de infra
# -----------------------

@app.command("migrate")
def cmd_migrate(db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite")):
    """Aplica migrações e recria as views auxiliares."""
    apply_migrations(db_path)
    create_views(db_path)
    typer.echo(f">> Migrações aplicadas e views criadas em: {db_path}")


params_app = typer.Typer(help="Gerenciar parâmetros globais (nível de serviço e lead time).")
app.add_typer(params_app, name="params")


@params_app.command("set")
def cmd_params_set(
    nivel_servico: Optional[float] = typer.Option(None, help="Ex.: 0.95"),
    mu_t_dias_uteis: Optional[float] = typer.Option(None, help="Lead time médio em dias úteis (ex.: 6)"),
    sigma_t_dias_uteis: Optional[float] = typer.Option(None, help="Desvio do lead time em dias úteis (ex.: 1)"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Define parâmetros globais (apenas os informados são alterados)."""
    repo = ParamsRepo(db_path)
    items: List[tuple[str, str]] = []
    if nivel_servico is not None:
        items.append(("nivel_servico", str(nivel_servico)))
    if mu_t_dias_uteis is not None:
        items.append(("mu_t_dias_uteis", str(mu_t_dias_uteis)))
    if sigma_t_dias_uteis is not None:
        items.append(("sigma_t_dias_uteis", str(sigma_t_dias_uteis)))
    if not items:
        typer.echo("Nada a alterar. Informe pelo menos um parâmetro.")
        raise typer.Exit(code=1)
    repo.set_many(items)
    typer.echo(">> Parâmetros atualizados.")


@params_app.command("get")
def cmd_params_get(
    chave: str = typer.Argument(..., help="Ex.: nivel_servico | mu_t_dias_uteis | sigma_t_dias_uteis"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Mostra um parâmetro específico."""
    repo = ParamsRepo(db_path)
    val = repo.get(chave)
    if val is None:
        typer.echo("(None)")
    else:
        typer.echo(val)


@params_app.command("show")
def cmd_params_show(
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Exibe os parâmetros efetivos (com fallback para defaults)."""
    repo = ParamsRepo(db_path)
    out = {
        "nivel_servico": repo.get("nivel_servico", str(DEFAULTS.nivel_servico)),
        "mu_t_dias_uteis": repo.get("mu_t_dias_uteis", str(DEFAULTS.mu_t_dias_uteis)),
        "sigma_t_dias_uteis": repo.get("sigma_t_dias_uteis", str(DEFAULTS.sigma_t_dias_uteis)),
        "_defaults": {
            "nivel_servico": DEFAULTS.nivel_servico,
            "mu_t_dias_uteis": DEFAULTS.mu_t_dias_uteis,
            "sigma_t_dias_uteis": DEFAULTS.sigma_t_dias_uteis,
        },
        "_db": db_path,
    }
    _print_json(out)


# -----------------------
# comandos de verificação
# -----------------------

@app.command("verificar")
def cmd_verificar(db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite")):
    """
    Executa o cálculo completo: rebuild de demanda, métricas, SS/ROP e sugestões.
    Saída em JSON.
    """
    res = run_verificar(db_path=db_path)
    _print_json(res)


# -----------------------
# comandos de movimentação
# -----------------------

@app.command("entrada-unica")
def cmd_entrada_unica(db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite")):
    """Registra uma entrada única via prompts no terminal."""
    try:
        rec = run_entrada_unica(db_path=db_path)
        typer.echo("")
        typer.echo("✅ Entrada registrada com sucesso!")
        typer.echo("ℹ️  Use 'python app.py lista entradas' para visualizar todas as entradas.")
    except Exception as e:
        typer.echo(f"❌ Erro ao registrar entrada: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("entrada-lotes")
def cmd_entrada_lotes(
    path: str = typer.Argument(..., help="Caminho do XLSX de ENTRADAS"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Registra entradas em lote a partir de um XLSX."""
    try:
        info = run_entrada_lote(path, db_path=db_path)
        # Show user-friendly success message
        typer.echo(f"✅ Importação de entradas concluída com sucesso!")
        typer.echo(f"📁 Arquivo: {info['arquivo']}")
        typer.echo(f"📝 Registros inseridos: {info['linhas_inseridas']}")
        typer.echo(f"💾 Banco de dados: {db_path}")
        typer.echo("")
        typer.echo("ℹ️  Use 'python app.py lista entradas' para visualizar os dados importados.")
    except Exception as e:
        typer.echo(f"❌ Erro ao importar entradas: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("saida-unica")
def cmd_saida_unica(db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite")):
    """Registra uma saída única via prompts no terminal."""
    try:
        rec = run_saida_unica(db_path=db_path)
        typer.echo("")
        typer.echo("✅ Saída registrada com sucesso!")
        typer.echo("ℹ️  Use 'python app.py lista saidas' para visualizar todas as saídas.")
    except Exception as e:
        typer.echo(f"❌ Erro ao registrar saída: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("saida-lotes")
def cmd_saida_lotes(
    path: str = typer.Argument(..., help="Caminho do XLSX de SAÍDAS"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Registra saídas em lote a partir de um XLSX."""
    try:
        info = run_saida_lote(path, db_path=db_path)
        # Show user-friendly success message
        typer.echo(f"✅ Importação de saídas concluída com sucesso!")
        typer.echo(f"📁 Arquivo: {info['arquivo']}")
        typer.echo(f"📝 Registros inseridos: {info['linhas_inseridas']}")
        typer.echo(f"💾 Banco de dados: {db_path}")
        typer.echo("")
        typer.echo("ℹ️  Use 'python app.py lista saidas' para visualizar os dados importados.")
    except Exception as e:
        typer.echo(f"❌ Erro ao importar saídas: {e}", err=True)
        raise typer.Exit(code=1)


# -----------------------
# comandos de visualização
# -----------------------

lista_app = typer.Typer(help="Visualizar dados armazenados no banco de dados.")
app.add_typer(lista_app, name="lista")

@lista_app.command("entradas")
def lista_entradas(
    limite: int = typer.Option(10, "--limite", "-l", help="Número máximo de registros a exibir"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Lista as entradas mais recentes armazenadas no banco de dados."""
    try:
        from estoque.infra.db import connect
        
        with connect(db_path) as conn:
            cur = conn.execute("""
                SELECT 
                    ROWID,
                    data_entrada,
                    codigo,
                    quantidade_raw,
                    lote,
                    data_validade,
                    valor_unitario,
                    representante,
                    responsavel
                FROM entrada
                ORDER BY ROWID DESC
                LIMIT ?
            """, (limite,))
            rows = cur.fetchall()
        
        if not rows:
            typer.echo("📭 Nenhuma entrada encontrada no banco de dados.")
            typer.echo("💡 Use 'python app.py entrada-lotes <arquivo.xlsx>' para importar dados.")
            return
        
        # Format data for display
        headers = ["ID", "Data", "Código", "Quantidade", "Lote", "Validade", "Valor Unit.", "Representante", "Responsável"]
        table_data = []
        for row in rows:
            table_data.append([
                row[0],  # ID
                row[1] or "-",  # data_entrada
                row[2] or "-",  # codigo
                row[3] or "-",  # quantidade_raw
                row[4] or "-",  # lote
                row[5] or "-",  # data_validade
                row[6] or "-",  # valor_unitario
                row[7] or "-",  # representante
                row[8] or "-",  # responsavel
            ])
        
        typer.echo(f"📥 Últimas {len(rows)} entradas registradas:")
        typer.echo("")
        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        typer.echo("")
        typer.echo(f"💾 Total de registros exibidos: {len(rows)} de {limite} solicitados")
        
    except Exception as e:
        typer.echo(f"❌ Erro ao listar entradas: {e}", err=True)
        raise typer.Exit(code=1)

@lista_app.command("saidas")
def lista_saidas(
    limite: int = typer.Option(10, "--limite", "-l", help="Número máximo de registros a exibir"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Lista as saídas mais recentes armazenadas no banco de dados."""
    try:
        from estoque.infra.db import connect
        
        with connect(db_path) as conn:
            cur = conn.execute("""
                SELECT 
                    ROWID,
                    data_saida,
                    codigo,
                    quantidade_raw,
                    lote,
                    data_validade,
                    custo,
                    paciente,
                    responsavel,
                    descarte_flag
                FROM saida
                ORDER BY ROWID DESC
                LIMIT ?
            """, (limite,))
            rows = cur.fetchall()
        
        if not rows:
            typer.echo("📭 Nenhuma saída encontrada no banco de dados.")
            typer.echo("💡 Use 'python app.py saida-lotes <arquivo.xlsx>' para importar dados.")
            return
        
        # Format data for display
        headers = ["ID", "Data", "Código", "Quantidade", "Lote", "Validade", "Custo", "Paciente", "Responsável", "Descarte"]
        table_data = []
        for row in rows:
            descarte = "Sim" if row[9] == 1 else ("Não" if row[9] == 0 else "-")
            table_data.append([
                row[0],  # ID
                row[1] or "-",  # data_saida
                row[2] or "-",  # codigo
                row[3] or "-",  # quantidade_raw
                row[4] or "-",  # lote
                row[5] or "-",  # data_validade
                row[6] or "-",  # custo
                row[7] or "-",  # paciente
                row[8] or "-",  # responsavel
                descarte,  # descarte_flag
            ])
        
        typer.echo(f"📤 Últimas {len(rows)} saídas registradas:")
        typer.echo("")
        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        typer.echo("")
        typer.echo(f"💾 Total de registros exibidos: {len(rows)} de {limite} solicitados")
        
    except Exception as e:
        typer.echo(f"❌ Erro ao listar saídas: {e}", err=True)
        raise typer.Exit(code=1)

@lista_app.command("resumo")
def lista_resumo(
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
):
    """Mostra um resumo geral dos dados armazenados."""
    try:
        from estoque.infra.db import connect
        
        with connect(db_path) as conn:
            # Count totals
            total_entradas = conn.execute("SELECT COUNT(*) FROM entrada").fetchone()[0]
            total_saidas = conn.execute("SELECT COUNT(*) FROM saida").fetchone()[0]
            
            # Recent entries
            last_entrada = conn.execute("""
                SELECT data_entrada FROM entrada 
                ORDER BY ROWID DESC LIMIT 1
            """).fetchone()
            
            last_saida = conn.execute("""
                SELECT data_saida FROM saida 
                ORDER BY ROWID DESC LIMIT 1
            """).fetchone()
            
            # Unique products
            produtos_entrada = conn.execute("SELECT COUNT(DISTINCT codigo) FROM entrada WHERE codigo IS NOT NULL").fetchone()[0]
            produtos_saida = conn.execute("SELECT COUNT(DISTINCT codigo) FROM saida WHERE codigo IS NOT NULL").fetchone()[0]
        
        typer.echo("📊 Resumo geral do banco de dados:")
        typer.echo("")
        
        # Summary table
        summary_data = [
            ["Total de Entradas", total_entradas],
            ["Total de Saídas", total_saidas],
            ["Produtos com Entrada", produtos_entrada],
            ["Produtos com Saída", produtos_saida],
            ["Última Entrada", last_entrada[0] if last_entrada and last_entrada[0] else "Nenhuma"],
            ["Última Saída", last_saida[0] if last_saida and last_saida[0] else "Nenhuma"],
        ]
        
        typer.echo(tabulate(summary_data, headers=["Métrica", "Valor"], tablefmt="grid"))
        typer.echo("")
        typer.echo("💡 Comandos úteis:")
        typer.echo("   • python app.py lista entradas --limite 20")
        typer.echo("   • python app.py lista saidas --limite 20") 
        typer.echo("   • python app.py rel ruptura")
        typer.echo("   • python app.py rel reposicao")
        
    except Exception as e:
        typer.echo(f"❌ Erro ao gerar resumo: {e}", err=True)
        raise typer.Exit(code=1)


rel_app = typer.Typer(help="Relatórios de estoque")
app.add_typer(rel_app, name="rel")

@rel_app.command("ruptura")
def rel_ruptura(
    horizonte_dias: int = typer.Option(7, help="Dias de cobertura máxima para alerta"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
    formato: str = typer.Option("tabela", "--formato", help="Formato de saída: 'tabela' ou 'json'"),
):
    """Relatório de produtos com risco de ruptura de estoque."""
    res = relatorio_alerta_ruptura(horizonte_dias=horizonte_dias, db_path=db_path)
    
    if formato == "json":
        _print_json(res)
        return
    
    if not res:
        typer.echo(f"✅ Nenhum produto com risco de ruptura nos próximos {horizonte_dias} dias!")
        return
    
    typer.echo(f"⚠️  Relatório de Risco de Ruptura (próximos {horizonte_dias} dias):")
    typer.echo("")
    
    headers = ["Código", "Nome", "Tipo Consumo", "Unidade", "Estoque Atual", "Demanda/Dia", "Cobertura (dias)"]
    table_data = []
    
    for item in res:
        table_data.append([
            item.get("codigo", "-"),
            (item.get("nome") or "-")[:30],  # Truncate long names
            item.get("tipo_consumo", "-"),
            item.get("unidade_alvo", "-"),
            f"{item.get('estoque_alvo', 0):.2f}",
            f"{item.get('mu_d', 0):.2f}",
            f"{item.get('cobertura_dias', 0):.1f}",
        ])
    
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    typer.echo("")
    typer.echo(f"🚨 Total de produtos em risco: {len(res)}")

@rel_app.command("vencimentos")
def rel_vencimentos(
    janela_dias: int = typer.Option(60, help="Dias até o vencimento"),
    detalhar_por_lote: bool = typer.Option(True, help="True=detalhe por lote; False=agregado por produto"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
    formato: str = typer.Option("tabela", "--formato", help="Formato de saída: 'tabela' ou 'json'"),
):
    """Relatório de produtos próximos ao vencimento."""
    res = relatorio_produtos_a_vencer(janela_dias=janela_dias, detalhar_por_lote=detalhar_por_lote, db_path=db_path)
    
    if formato == "json":
        _print_json(res)
        return
    
    if not res:
        typer.echo(f"✅ Nenhum produto vence nos próximos {janela_dias} dias!")
        return
    
    if detalhar_por_lote:
        typer.echo(f"📅 Produtos com Vencimento nos próximos {janela_dias} dias (por lote):")
        typer.echo("")
        
        headers = ["Código", "Lote", "Data Vencimento", "Qtd. Apresentação", "Qtd. Unidade"]
        table_data = []
        
        for item in res:
            qtd_apres = f"{item.get('qtd_apres_num', 0):.2f} {item.get('qtd_apres_un', '') or ''}".strip()
            qtd_unid = f"{item.get('qtd_unid_num', 0):.2f} {item.get('qtd_unid_un', '') or ''}".strip()
            
            table_data.append([
                item.get("codigo", "-"),
                item.get("lote", "-"),
                item.get("data_validade", "-"),
                qtd_apres or "-",
                qtd_unid or "-",
            ])
        
        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        
    else:
        typer.echo(f"📅 Produtos com Vencimento nos próximos {janela_dias} dias (agregado):")
        typer.echo("")
        
        headers = ["Código", "Primeira Validade", "Qtd. Total Apresentação", "Qtd. Total Unidade"]
        table_data = []
        
        for item in res:
            qtd_apres = f"{item.get('qtd_apres_num', 0):.2f} {item.get('qtd_apres_un', '') or ''}".strip()
            qtd_unid = f"{item.get('qtd_unid_num', 0):.2f} {item.get('qtd_unid_un', '') or ''}".strip()
            
            table_data.append([
                item.get("codigo", "-"),
                item.get("primeira_validade", "-"),
                qtd_apres or "-",
                qtd_unid or "-",
            ])
        
        typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    typer.echo("")
    typer.echo(f"⚠️  Total de itens com vencimento próximo: {len(res)}")

@rel_app.command("top-consumo")
def rel_top_consumo(
    inicio_ano_mes: str = typer.Option(..., help="YYYY-MM (início)"),
    fim_ano_mes: str = typer.Option(..., help="YYYY-MM (fim)"),
    top_n: int = typer.Option(20, help="Top N produtos"),
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
    formato: str = typer.Option("tabela", "--formato", help="Formato de saída: 'tabela' ou 'json'"),
):
    """Relatório dos produtos mais consumidos no período."""
    res = relatorio_mais_consumidos(inicio_ano_mes=inicio_ano_mes, fim_ano_mes=fim_ano_mes, top_n=top_n, db_path=db_path)
    
    if formato == "json":
        _print_json(res)
        return
    
    if not res:
        typer.echo(f"📭 Nenhum consumo encontrado no período de {inicio_ano_mes} a {fim_ano_mes}.")
        return
    
    typer.echo(f"📈 Top {len(res)} Produtos Mais Consumidos ({inicio_ano_mes} a {fim_ano_mes}):")
    typer.echo("")
    
    headers = ["Ranking", "Código", "Nome do Produto", "Quantidade Total"]
    table_data = []
    
    for i, item in enumerate(res, 1):
        table_data.append([
            f"{i}º",
            item.get("codigo", "-"),
            (item.get("nome") or "-")[:40],  # Truncate long names
            f"{item.get('qtd_total', 0):.2f}",
        ])
    
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    typer.echo("")
    typer.echo(f"📊 Período analisado: {inicio_ano_mes} a {fim_ano_mes}")
    typer.echo(f"🏆 Total de produtos listados: {len(res)}")

@rel_app.command("reposicao")
def rel_reposicao_cmd(
    db_path: str = typer.Option(DB_PATH, "--db", help="Caminho do SQLite"),
    formato: str = typer.Option("tabela", "--formato", help="Formato de saída: 'tabela' ou 'json'"),
):
    """Relatório de produtos que precisam ser repostos."""
    res = relatorio_reposicao(db_path=db_path)
    
    if formato == "json":
        _print_json(res)
        return
    
    if not res:
        typer.echo("✅ Nenhum produto precisa de reposição no momento!")
        return
    
    typer.echo("🔄 Relatório de Reposição de Produtos:")
    typer.echo("")
    
    headers = ["Código", "Nome", "Status", "Estoque Atual", "Necessidade", "Sugestão Compra", "Unidade"]
    table_data = []
    
    for item in res:
        status_icon = "🔴" if item.get("status") == "CRITICO" else "🟡"
        table_data.append([
            item.get("codigo", "-"),
            (item.get("nome") or "-")[:25],  # Truncate long names
            f"{status_icon} {item.get('status', '-')}",
            f"{item.get('estoque_atual', 0):.2f}",
            f"{item.get('necessidade', 0):.2f}",
            f"{item.get('q_sug_apresentacao', 0):.2f}",
            item.get("unidade_apresentacao", "-"),
        ])
    
    typer.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    typer.echo("")
    
    criticos = sum(1 for item in res if item.get("status") == "CRITICO")
    repor = len(res) - criticos
    
    typer.echo(f"🔴 Produtos críticos: {criticos}")
    typer.echo(f"🟡 Produtos para repor: {repor}")
    typer.echo(f"📋 Total de itens: {len(res)}")
    
# Entry point opcional:
def main():
    app()


if __name__ == "__main__":
    main()
