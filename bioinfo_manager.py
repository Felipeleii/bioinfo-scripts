#!/usr/bin/env python3
"""
Gerenciador de Ferramentas de Bioinformática
Sistema centralizado para executar e gerenciar scripts de bioinformática.

Autor: Felipe Lei
Versão: 2.0
Data: 2025-06-22
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json

class BioinfoToolsManager:
    def __init__(self):
        self.tools = {
            "fastq_renamer": {
                "name": "Renomeador de FASTQ",
                "description": "Renomeia arquivos FASTQ mantendo padrões específicos",
                "script": "fastq_renamer.py",
                "category": "file_management"
            },
            "fasta_renamer": {
                "name": "Renomeador de FASTA", 
                "description": "Renomeia arquivos FASTA com diferentes padrões",
                "script": "fasta_renamer.py",
                "category": "file_management"
            },
            "contig_separator": {
                "name": "Separador de Contigs",
                "description": "Separa contigs multi-FASTA em arquivos individuais",
                "script": "contig_separator.py",
                "category": "sequence_analysis"
            },
            "bactopia_gui": {
                "name": "Bactopia GUI",
                "description": "Interface gráfica para pipeline Bactopia",
                "script": "bactopia_gui.py",
                "category": "pipeline"
            },
            "assembly_renamer": {
                "name": "Renomeador de Assembly",
                "description": "Renomeia arquivos assembly_contigs.fasta",
                "script": "assembly_renamer.py",
                "category": "file_management"
            }
        }
        
        self.categories = {
            "file_management": "Gerenciamento de Arquivos",
            "sequence_analysis": "Análise de Sequências", 
            "pipeline": "Pipelines e Workflows",
            "quality_control": "Controle de Qualidade",
            "annotation": "Anotação Genômica"
        }
    
    def list_tools(self, category: Optional[str] = None) -> None:
        """Lista ferramentas disponíveis."""
        print("=" * 60)
        print("FERRAMENTAS DE BIOINFORMÁTICA DISPONÍVEIS")
        print("=" * 60)
        
        if category:
            tools_to_show = {k: v for k, v in self.tools.items() if v["category"] == category}
            if not tools_to_show:
                print(f"Nenhuma ferramenta encontrada na categoria: {category}")
                return
        else:
            tools_to_show = self.tools
        
        # Agrupar por categoria
        by_category = {}
        for tool_id, tool_info in tools_to_show.items():
            cat = tool_info["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((tool_id, tool_info))
        
        for cat, tools in by_category.items():
            print(f"\n📁 {self.categories.get(cat, cat.upper())}")
            print("-" * 40)
            for tool_id, tool_info in tools:
                print(f"  {tool_id:<20} - {tool_info['name']}")
                print(f"  {' ' * 20}   {tool_info['description']}")
        
        print(f"\nTotal: {len(tools_to_show)} ferramentas")
        print("\nUso: bioinfo_manager.py run <tool_id> [args...]")
    
    def list_categories(self) -> None:
        """Lista categorias disponíveis."""
        print("CATEGORIAS DISPONÍVEIS:")
        print("=" * 30)
        for cat_id, cat_name in self.categories.items():
            count = len([t for t in self.tools.values() if t["category"] == cat_id])
            print(f"  {cat_id:<20} - {cat_name} ({count} ferramentas)")
    
    def run_tool(self, tool_id: str, args: List[str]) -> int:
        """Executa uma ferramenta específica."""
        if tool_id not in self.tools:
            print(f"Erro: Ferramenta '{tool_id}' não encontrada")
            print("Use 'bioinfo_manager.py list' para ver ferramentas disponíveis")
            return 1
        
        tool_info = self.tools[tool_id]
        script_path = Path(__file__).parent / tool_info["script"]
        
        if not script_path.exists():
            print(f"Erro: Script não encontrado: {script_path}")
            return 1
        
        # Executar script
        cmd = [sys.executable, str(script_path)] + args
        
        print(f"Executando: {tool_info['name']}")
        print(f"Comando: {' '.join(cmd)}")
        print("-" * 50)
        
        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            print("\nExecução interrompida pelo usuário")
            return 130
        except Exception as e:
            print(f"Erro ao executar ferramenta: {e}")
            return 1
    
    def show_tool_help(self, tool_id: str) -> int:
        """Mostra ajuda de uma ferramenta específica."""
        if tool_id not in self.tools:
            print(f"Erro: Ferramenta '{tool_id}' não encontrada")
            return 1
        
        return self.run_tool(tool_id, ["--help"])
    
    def create_config(self, config_path: str) -> None:
        """Cria arquivo de configuração."""
        config = {
            "default_paths": {
                "fastq_dir": "",
                "fasta_dir": "",
                "output_dir": "",
                "bactopia_results": ""
            },
            "default_settings": {
                "cpu_cores": 4,
                "memory_gb": 8,
                "use_docker": True
            },
            "species_presets": {
                "Klebsiella pneumoniae": {"genome_size": 5500000},
                "Acinetobacter baumannii": {"genome_size": 4000000},
                "Escherichia coli": {"genome_size": 5000000}
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Arquivo de configuração criado: {config_path}")
    
    def setup_environment(self) -> None:
        """Configura ambiente inicial."""
        print("CONFIGURAÇÃO DO AMBIENTE BIOINFORMÁTICA")
        print("=" * 50)
        
        # Verificar Python
        python_version = sys.version_info
        print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Verificar dependências
        dependencies = {
            "biopython": "Bio",
            "pandas": "pandas", 
            "tkinter": "tkinter"
        }
        
        print("\nVerificando dependências:")
        missing_deps = []
        
        for dep_name, import_name in dependencies.items():
            try:
                __import__(import_name)
                print(f"✓ {dep_name}")
            except ImportError:
                print(f"✗ {dep_name} (faltando)")
                missing_deps.append(dep_name)
        
        if missing_deps:
            print(f"\nDependências faltando: {', '.join(missing_deps)}")
            print("Instale com:")
            if "biopython" in missing_deps:
                print("  pip install biopython")
            if "pandas" in missing_deps:
                print("  pip install pandas")
            if "tkinter" in missing_deps:
                print("  sudo apt install python3-tk  # Ubuntu/Debian")
        else:
            print("\n✓ Todas as dependências estão instaladas!")
        
        # Verificar ferramentas externas
        print("\nVerificando ferramentas externas:")
        external_tools = ["nextflow", "docker"]
        
        for tool in external_tools:
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✓ {tool}")
                else:
                    print(f"✗ {tool} (não funciona)")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"✗ {tool} (não encontrado)")
        
        # Criar diretórios padrão
        print("\nCriando estrutura de diretórios:")
        dirs_to_create = [
            "data/fastq",
            "data/fasta", 
            "data/assemblies",
            "results/bactopia",
            "results/qc",
            "scripts/custom",
            "configs"
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"✓ {dir_path}/")
        
        # Criar configuração padrão
        config_path = "configs/bioinfo_config.json"
        if not Path(config_path).exists():
            self.create_config(config_path)
        
        print("\n✓ Ambiente configurado com sucesso!")

def main():
    """Função principal."""
    manager = BioinfoToolsManager()
    
    parser = argparse.ArgumentParser(
        description="Gerenciador de Ferramentas de Bioinformática",
        epilog="""
Exemplos de uso:
  %(prog)s list                           # Lista todas as ferramentas
  %(prog)s list --category file_management # Lista ferramentas por categoria
  %(prog)s categories                     # Lista categorias disponíveis  
  %(prog)s run fastq_renamer --help       # Mostra ajuda de uma ferramenta
  %(prog)s run fastq_renamer /path/data   # Executa ferramenta
  %(prog)s setup                          # Configura ambiente inicial
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando list
    list_parser = subparsers.add_parser("list", help="Lista ferramentas disponíveis")
    list_parser.add_argument("--category", help="Filtrar por categoria")
    
    # Comando categories  
    subparsers.add_parser("categories", help="Lista categorias disponíveis")
    
    # Comando run
    run_parser = subparsers.add_parser("run", help="Executa uma ferramenta")
    run_parser.add_argument("tool_id", help="ID da ferramenta")
    run_parser.add_argument("tool_args", nargs="*", help="Argumentos para a ferramenta")
    
    # Comando help
    help_parser = subparsers.add_parser("help", help="Mostra ajuda de uma ferramenta")
    help_parser.add_argument("tool_id", help="ID da ferramenta")
    
    # Comando setup
    subparsers.add_parser("setup", help="Configura ambiente inicial")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == "list":
        manager.list_tools(args.category)
        return 0
    
    elif args.command == "categories":
        manager.list_categories()
        return 0
    
    elif args.command == "run":
        return manager.run_tool(args.tool_id, args.tool_args)
    
    elif args.command == "help":
        return manager.show_tool_help(args.tool_id)
    
    elif args.command == "setup":
        manager.setup_environment()
        return 0
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
