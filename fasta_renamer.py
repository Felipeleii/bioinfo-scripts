#!/usr/bin/env python3
"""
Renomeador de arquivos FASTA - Versão Otimizada
Renomeia arquivos .fasta mantendo apenas o primeiro campo antes do underscore.

Autor: Felipe Lei
Versão: 2.0
Data: 2025-06-22
"""

import os
import sys
import argparse
import logging
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict

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

def get_fasta_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Obtém lista de arquivos FASTA no diretório."""
    extensions = ["*.fasta", "*.fa", "*.fas", "*.fna"]
    files = []
    
    for ext in extensions:
        pattern = f"**/{ext}" if recursive else ext
        files.extend(directory.glob(pattern))
    
    if not files:
        logging.warning(f"Nenhum arquivo FASTA encontrado em {directory}")
    else:
        logging.info(f"Encontrados {len(files)} arquivos FASTA")
    
    return files

def generate_new_fasta_name(
    original_name: str, 
    pattern: str = "first_only",
    custom_suffix: str = ""
) -> str:
    """
    Gera novo nome para arquivo FASTA baseado no padrão especificado.
    
    Args:
        original_name: Nome original do arquivo
        pattern: Padrão de renomeação
        custom_suffix: Sufixo customizado
    
    Returns:
        Novo nome do arquivo
    """
    # Extrair extensão
    path_obj = Path(original_name)
    extension = path_obj.suffix
    base_name = path_obj.stem
    
    parts = base_name.split("_")
    
    if len(parts) < 1:
        logging.warning(f"Arquivo {original_name} não segue padrão esperado")
        return original_name
    
    if pattern == "first_only":
        new_name = f"{parts[0]}{custom_suffix}{extension}"
    elif pattern == "first_two":
        if len(parts) >= 2:
            new_name = f"{parts[0]}_{parts[1]}{custom_suffix}{extension}"
        else:
            new_name = f"{parts[0]}{custom_suffix}{extension}"
    elif pattern == "species_format":
        # Para formatos como "HSP1_001_Klebsiella pneumoniae.fasta"
        if len(parts) >= 2:
            new_name = f"{parts[0]}_{parts[1]}{custom_suffix}{extension}"
        else:
            new_name = f"{parts[0]}{custom_suffix}{extension}"
    else:
        new_name = f"{parts[0]}{custom_suffix}{extension}"
    
    return new_name

def check_conflicts(files: List[Path], pattern: str, custom_suffix: str = "") -> Dict[str, List[str]]:
    """
    Verifica conflitos de nomes antes de renomear.
    
    Returns:
        Dicionário com conflitos encontrados
    """
    new_names = {}
    conflicts = {"duplicates": [], "existing": []}
    
    for file_path in files:
        new_name = generate_new_fasta_name(file_path.name, pattern, custom_suffix)
        new_path = file_path.parent / new_name
        
        # Verificar duplicatas
        if new_name in new_names:
            conflicts["duplicates"].append(f"{new_name}: {new_names[new_name]} e {file_path.name}")
        else:
            new_names[new_name] = file_path.name
        
        # Verificar arquivos existentes
        if new_path.exists() and new_path != file_path:
            conflicts["existing"].append(f"{new_name} já existe")
    
    return conflicts

def rename_file_safe(
    old_path: Path, 
    new_path: Path, 
    dry_run: bool = False,
    force: bool = False
) -> bool:
    """
    Renomeia arquivo de forma segura, verificando conflitos.
    
    Args:
        old_path: Caminho original
        new_path: Novo caminho
        dry_run: Se True, apenas simula a operação
        force: Sobrescrever arquivos existentes
    
    Returns:
        True se a operação foi bem-sucedida
    """
    if new_path.exists() and new_path != old_path:
        if not force:
            logging.error(f"Arquivo de destino já existe: {new_path.name}")
            return False
        else:
            logging.warning(f"Sobrescrevendo arquivo existente: {new_path.name}")
    
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

def create_backup(files: List[Path], backup_dir: Path) -> bool:
    """Cria backup dos arquivos originais."""
    try:
        backup_dir.mkdir(exist_ok=True)
        for file_path in files:
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
        logging.info(f"Backup criado em: {backup_dir}")
        return True
    except Exception as e:
        logging.error(f"Erro ao criar backup: {e}")
        return False

def renomear_fasta_pasta(
    pasta: str,
    pattern: str = "first_only",
    custom_suffix: str = "",
    recursive: bool = False,
    dry_run: bool = False,
    backup: bool = False,
    force: bool = False
) -> Tuple[int, int]:
    """
    Renomeia arquivos FASTA em uma pasta.
    
    Args:
        pasta: Caminho da pasta
        pattern: Padrão de renomeação
        custom_suffix: Sufixo customizado
        recursive: Busca recursiva em subpastas
        dry_run: Apenas simula as operações
        backup: Cria backup dos arquivos originais
        force: Sobrescrever arquivos existentes
    
    Returns:
        Tupla (sucessos, erros)
    """
    try:
        directory = validate_directory(pasta)
    except (FileNotFoundError, NotADirectoryError) as e:
        logging.error(e)
        return 0, 1
    
    fasta_files = get_fasta_files(directory, recursive)
    
    if not fasta_files:
        return 0, 0
    
    # Verificar conflitos
    conflicts = check_conflicts(fasta_files, pattern, custom_suffix)
    
    if conflicts["duplicates"]:
        logging.error("Conflitos de nomes detectados:")
        for conflict in conflicts["duplicates"]:
            logging.error(f"  - {conflict}")
        if not force:
            logging.error("Use --force para ignorar conflitos")
            return 0, len(fasta_files)
    
    if conflicts["existing"]:
        logging.warning("Arquivos existentes que serão sobrescritos:")
        for conflict in conflicts["existing"]:
            logging.warning(f"  - {conflict}")
        if not force and not dry_run:
            logging.error("Use --force para sobrescrever arquivos existentes")
            return 0, len(fasta_files)
    
    # Criar backup se solicitado
    if backup and not dry_run:
        backup_dir = directory / "backup_fasta_originals"
        if not create_backup(fasta_files, backup_dir):
            logging.error("Falha ao criar backup. Abortando...")
            return 0, len(fasta_files)
    
    sucessos = 0
    erros = 0
    
    for file_path in fasta_files:
        new_name = generate_new_fasta_name(file_path.name, pattern, custom_suffix)
        new_path = file_path.parent / new_name
        
        if rename_file_safe(file_path, new_path, dry_run, force):
            sucessos += 1
        else:
            erros += 1
    
    return sucessos, erros

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Renomeador inteligente de arquivos FASTA",
        epilog="""
Padrões de renomeação:
  first_only     : Mantém apenas o primeiro campo (HSP1_001_species.fasta → HSP1.fasta)
  first_two      : Mantém os dois primeiros campos (HSP1_001_species.fasta → HSP1_001.fasta)
  species_format : Mantém formato para espécies (HSP1_001_species.fasta → HSP1_001.fasta)

Exemplos de uso:
  %(prog)s /caminho/para/pasta
  %(prog)s /caminho/para/pasta --pattern first_two --recursive
  %(prog)s /caminho/para/pasta --custom-suffix "_processed" --backup
  %(prog)s /caminho/para/pasta --dry-run --verbose
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "pasta", 
        help="Caminho da pasta contendo arquivos FASTA"
    )
    parser.add_argument(
        "--pattern", 
        choices=["first_only", "first_two", "species_format"],
        default="first_only",
        help="Padrão de renomeação (padrão: first_only)"
    )
    parser.add_argument(
        "--custom-suffix",
        default="",
        help="Sufixo customizado para adicionar aos nomes"
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
        help="Cria backup dos arquivos originais"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Sobrescrever arquivos existentes e ignorar conflitos"
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
    
    sucessos, erros = renomear_fasta_pasta(
        args.pasta,
        args.pattern,
        args.custom_suffix,
        args.recursive,
        args.dry_run,
        args.backup,
        args.force
    )
    
    # Resumo final
    logging.info("=" * 50)
    logging.info(f"RESUMO: {sucessos} sucessos, {erros} erros")
    
    if erros > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
