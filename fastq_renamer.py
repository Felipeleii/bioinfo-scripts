#!/usr/bin/env python3
"""
Renomeador de arquivos FASTQ - Versão Otimizada
Renomeia arquivos .fastq.gz mantendo apenas o primeiro e último campo separados por underscore.

Autor: Felipe Lei
Versão: 2.0
Data: 2025-06-22
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional

def setup_logging(verbose: bool = False) -> None:
    """Configura o sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def validate_directory(directory: str) -> Path:
    """Valida se o diretório existe e é acessível."""
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {directory}")
    if not path.is_dir():
        raise NotADirectoryError(f"O caminho não é um diretório: {directory}")
    return path

def get_fastq_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Obtém lista de arquivos FASTQ no diretório."""
    pattern = "**/*.fastq.gz" if recursive else "*.fastq.gz"
    files = list(directory.glob(pattern))
    
    if not files:
        logging.warning(f"Nenhum arquivo .fastq.gz encontrado em {directory}")
    else:
        logging.info(f"Encontrados {len(files)} arquivos .fastq.gz")
    
    return files

def generate_new_name(original_name: str, pattern: str = "first_last") -> str:
    """
    Gera novo nome baseado no padrão especificado.
    
    Args:
        original_name: Nome original do arquivo
        pattern: Padrão de renomeação ('first_last', 'first_only', 'custom')
    
    Returns:
        Novo nome do arquivo
    """
    # Remove extensão .fastq.gz
    base_name = original_name.replace('.fastq.gz', '')
    parts = base_name.split("_")
    
    if len(parts) < 2:
        logging.warning(f"Arquivo {original_name} não segue padrão esperado")
        return original_name
    
    if pattern == "first_last":
        new_name = f"{parts[0]}_{parts[-1]}.fastq.gz"
    elif pattern == "first_only":
        new_name = f"{parts[0]}.fastq.gz"
    else:
        # Padrão customizado pode ser implementado aqui
        new_name = f"{parts[0]}_{parts[-1]}.fastq.gz"
    
    return new_name

def rename_file_safe(old_path: Path, new_path: Path, dry_run: bool = False) -> bool:
    """
    Renomeia arquivo de forma segura, verificando conflitos.
    
    Args:
        old_path: Caminho original
        new_path: Novo caminho
        dry_run: Se True, apenas simula a operação
    
    Returns:
        True se a operação foi bem-sucedida
    """
    if new_path.exists():
        logging.error(f"Arquivo de destino já existe: {new_path.name}")
        return False
    
    if dry_run:
        logging.info(f"[DRY RUN] {old_path.name} → {new_path.name}")
        return True
    
    try:
        old_path.rename(new_path)
        logging.info(f"Renomeado: {old_path.name} → {new_path.name}")
        return True
    except Exception as e:
        logging.error(f"Erro ao renomear {old_path.name}: {e}")
        return False

def renomear_fastq_pasta(
    pasta: str, 
    pattern: str = "first_last", 
    recursive: bool = False,
    dry_run: bool = False,
    backup: bool = False
) -> Tuple[int, int]:
    """
    Renomeia arquivos FASTQ em uma pasta.
    
    Args:
        pasta: Caminho da pasta
        pattern: Padrão de renomeação
        recursive: Busca recursiva em subpastas
        dry_run: Apenas simula as operações
        backup: Cria backup dos nomes originais
    
    Returns:
        Tupla (sucessos, erros)
    """
    try:
        directory = validate_directory(pasta)
    except (FileNotFoundError, NotADirectoryError) as e:
        logging.error(e)
        return 0, 1
    
    fastq_files = get_fastq_files(directory, recursive)
    
    if not fastq_files:
        return 0, 0
    
    # Criar backup dos nomes originais se solicitado
    if backup and not dry_run:
        backup_file = directory / "backup_original_names.txt"
        with open(backup_file, 'w') as f:
            f.write("# Backup dos nomes originais\n")
            f.write("# Data: " + str(logging.Formatter().formatTime(logging.LogRecord(
                '', '', '', '', '', '', '', ''))) + "\n")
            for file_path in fastq_files:
                f.write(f"{file_path.name}\n")
        logging.info(f"Backup criado: {backup_file}")
    
    sucessos = 0
    erros = 0
    
    for file_path in fastq_files:
        new_name = generate_new_name(file_path.name, pattern)
        new_path = file_path.parent / new_name
        
        if rename_file_safe(file_path, new_path, dry_run):
            sucessos += 1
        else:
            erros += 1
    
    return sucessos, erros

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Renomeia arquivos FASTQ de forma inteligente",
        epilog="""
Exemplos de uso:
  %(prog)s /caminho/para/pasta
  %(prog)s /caminho/para/pasta --pattern first_only --recursive
  %(prog)s /caminho/para/pasta --dry-run --verbose
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "pasta", 
        help="Caminho da pasta contendo arquivos FASTQ"
    )
    parser.add_argument(
        "--pattern", 
        choices=["first_last", "first_only"],
        default="first_last",
        help="Padrão de renomeação (padrão: first_last)"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Busca recursiva em subpastas"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Apenas simula as operações sem executar"
    )
    parser.add_argument(
        "--backup", "-b",
        action="store_true",
        help="Cria backup dos nomes originais"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Saída detalhada"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if args.dry_run:
        logging.info("MODO DRY RUN - Nenhuma alteração será feita")
    
    sucessos, erros = renomear_fastq_pasta(
        args.pasta,
        args.pattern,
        args.recursive,
        args.dry_run,
        args.backup
    )
    
    # Resumo final
    logging.info("=" * 50)
    logging.info(f"RESUMO: {sucessos} sucessos, {erros} erros")
    
    if erros > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
