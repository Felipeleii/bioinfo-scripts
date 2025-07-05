#!/usr/bin/env python3
"""
Separador de Contigs - Versão Otimizada
Separa contigs de um arquivo multi-FASTA em arquivos individuais por isolado.

Autor: Felipe Lei
Versão: 2.0
Data: 2025-06-22

Dependências: biopython
Instalação: pip install biopython
"""

import os
import sys
import argparse
import logging
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Pattern
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

def setup_logging(verbose: bool = False) -> None:
    """Configura o sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def validate_input_file(file_path: str) -> Path:
    """Valida se o arquivo de entrada existe e é acessível."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    if not path.is_file():
        raise ValueError(f"O caminho não é um arquivo: {file_path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Arquivo está vazio: {file_path}")
    return path

def get_regex_patterns() -> Dict[str, Pattern]:
    """Define padrões regex para diferentes tipos de identificadores."""
    patterns = {
        'standard': re.compile(r"(S\d+_\d+|N\d+_\d+|T\d+_\d+)"),
        'extended': re.compile(r"([A-Z]+\d+_\d+)"),
        'simple': re.compile(r"([A-Z]\d+)"),
        'custom': re.compile(r"(isolado[_\-]?\d+|sample[_\-]?\d+)", re.IGNORECASE),
        'generic': re.compile(r"([A-Za-z]+\d+)")
    }
    return patterns

def extract_isolate_id(description: str, patterns: Dict[str, Pattern], custom_pattern: Optional[str] = None) -> Optional[str]:
    """
    Extrai o ID do isolado da descrição do contig.
    
    Args:
        description: Descrição do contig
        patterns: Dicionário com padrões regex
        custom_pattern: Padrão customizado opcional
    
    Returns:
        ID do isolado ou None se não encontrado
    """
    # Tentar padrão customizado primeiro
    if custom_pattern:
        try:
            custom_regex = re.compile(custom_pattern)
            match = custom_regex.search(description)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        except re.error as e:
            logging.warning(f"Padrão regex inválido '{custom_pattern}': {e}")
    
    # Tentar padrões predefinidos
    for pattern_name, pattern in patterns.items():
        match = pattern.search(description)
        if match:
            logging.debug(f"Padrão '{pattern_name}' encontrou: {match.group(1)}")
            return match.group(1)
    
    return None

def analyze_fasta_file(fasta_path: Path, patterns: Dict[str, Pattern], custom_pattern: Optional[str] = None) -> Dict:
    """
    Analisa o arquivo FASTA e retorna estatísticas.
    
    Returns:
        Dicionário com estatísticas do arquivo
    """
    stats = {
        'total_sequences': 0,
        'identified_isolates': defaultdict(int),
        'unidentified_sequences': 0,
        'sequence_lengths': [],
        'isolate_counts': Counter()
    }
    
    try:
        for record in SeqIO.parse(fasta_path, "fasta"):
            stats['total_sequences'] += 1
            stats['sequence_lengths'].append(len(record.seq))
            
            isolate_id = extract_isolate_id(record.description, patterns, custom_pattern)
            
            if isolate_id:
                stats['identified_isolates'][isolate_id] += 1
                stats['isolate_counts'][isolate_id] += 1
            else:
                stats['unidentified_sequences'] += 1
                logging.debug(f"Sequência não identificada: {record.description}")
    
    except Exception as e:
        logging.error(f"Erro ao analisar arquivo FASTA: {e}")
        raise
    
    return stats

def print_analysis_report(stats: Dict) -> None:
    """Imprime relatório de análise do arquivo."""
    logging.info("=" * 60)
    logging.info("RELATÓRIO DE ANÁLISE")
    logging.info("=" * 60)
    logging.info(f"Total de sequências: {stats['total_sequences']}")
    logging.info(f"Isolados identificados: {len(stats['identified_isolates'])}")
    logging.info(f"Sequências não identificadas: {stats['unidentified_sequences']}")
    
    if stats['sequence_lengths']:
        avg_length = sum(stats['sequence_lengths']) / len(stats['sequence_lengths'])
        logging.info(f"Tamanho médio das sequências: {avg_length:.0f} bp")
        logging.info(f"Sequência mais longa: {max(stats['sequence_lengths'])} bp")
        logging.info(f"Sequência mais curta: {min(stats['sequence_lengths'])} bp")
    
    if stats['isolate_counts']:
        logging.info("\nContigs por isolado:")
        for isolate, count in sorted(stats['isolate_counts'].items()):
            logging.info(f"  {isolate}: {count} contigs")
    
    logging.info("=" * 60)

def separar_contigs_por_isolado(
    fasta_path: str,
    output_dir: str,
    custom_pattern: Optional[str] = None,
    min_length: int = 0,
    max_length: Optional[int] = None,
    dry_run: bool = False,
    analyze_only: bool = False,
    output_format: str = "fasta"
) -> Dict:
    """
    Separa contigs de um arquivo multi-FASTA em arquivos individuais.
    
    Args:
        fasta_path: Caminho do arquivo FASTA de entrada
        output_dir: Diretório de saída
        custom_pattern: Padrão regex customizado
        min_length: Tamanho mínimo dos contigs
        max_length: Tamanho máximo dos contigs
        dry_run: Apenas simula as operações
        analyze_only: Apenas analisa o arquivo sem separar
        output_format: Formato de saída (fasta, genbank)
    
    Returns:
        Dicionário com estatísticas da operação
    """
    # Validar entrada
    input_path = validate_input_file(fasta_path)
    patterns = get_regex_patterns()
    
    # Analisar arquivo
    logging.info(f"Analisando arquivo: {input_path}")
    stats = analyze_fasta_file(input_path, patterns, custom_pattern)
    print_analysis_report(stats)
    
    if analyze_only:
        return stats
    
    # Preparar diretório de saída
    output_path = Path(output_dir)
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Diretório de saída: {output_path}")
    
    # Agrupar contigs por isolado
    isolados = defaultdict(list)
    filtered_sequences = 0
    
    for record in SeqIO.parse(input_path, "fasta"):
        # Aplicar filtros de tamanho
        seq_length = len(record.seq)
        if seq_length < min_length:
            filtered_sequences += 1
            continue
        if max_length and seq_length > max_length:
            filtered_sequences += 1
            continue
        
        isolate_id = extract_isolate_id(record.description, patterns, custom_pattern)
        
        if isolate_id:
            isolados[isolate_id].append(record)
        else:
            logging.warning(f"Contig não identificado: {record.id}")
    
    if filtered_sequences > 0:
        logging.info(f"Sequências filtradas por tamanho: {filtered_sequences}")
    
    # Escrever arquivos separados
    files_created = 0
    total_contigs_written = 0
    
    for isolado, contigs in isolados.items():
        if not contigs:
            continue
            
        # Definir nome do arquivo de saída
        if output_format.lower() == "genbank":
            output_file = output_path / f"{isolado}.gbk"
        else:
            output_file = output_path / f"{isolado}.fasta"
        
        if dry_run:
            logging.info(f"[DRY RUN] Criaria arquivo: {output_file} com {len(contigs)} contigs")
        else:
            try:
                with open(output_file, "w") as out_f:
                    SeqIO.write(contigs, out_f, output_format.lower())
                
                logging.info(f"Criado: {output_file} ({len(contigs)} contigs)")
                files_created += 1
                total_contigs_written += len(contigs)
                
            except Exception as e:
                logging.error(f"Erro ao criar arquivo {output_file}: {e}")
    
    # Atualizar estatísticas
    operation_stats = {
        'input_file': str(input_path),
        'output_directory': str(output_path),
        'total_input_sequences': stats['total_sequences'],
        'identified_isolates': len(isolados),
        'files_created': files_created,
        'total_contigs_written': total_contigs_written,
        'filtered_sequences': filtered_sequences,
        'unidentified_sequences': stats['unidentified_sequences']
    }
    
    return operation_stats

def print_operation_summary(stats: Dict) -> None:
    """Imprime resumo da operação."""
    logging.info("=" * 60)
    logging.info("RESUMO DA OPERAÇÃO")
    logging.info("=" * 60)
    logging.info(f"Arquivo de entrada: {stats['input_file']}")
    logging.info(f"Diretório de saída: {stats['output_directory']}")
    logging.info(f"Sequências de entrada: {stats['total_input_sequences']}")
    logging.info(f"Isolados identificados: {stats['identified_isolates']}")
    logging.info(f"Arquivos criados: {stats['files_created']}")
    logging.info(f"Contigs escritos: {stats['total_contigs_written']}")
    
    if stats['filtered_sequences'] > 0:
        logging.info(f"Sequências filtradas: {stats['filtered_sequences']}")
    
    if stats['unidentified_sequences'] > 0:
        logging.warning(f"Sequências não identificadas: {stats['unidentified_sequences']}")
    
    logging.info("=" * 60)

def validate_dependencies() -> bool:
    """Verifica se as dependências estão instaladas."""
    try:
        import Bio
        logging.debug(f"Biopython versão: {Bio.__version__}")
        return True
    except ImportError:
        logging.error("Biopython não está instalado!")
        logging.error("Instale com: pip install biopython")
        return False

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Separador inteligente de contigs multi-FASTA",
        epilog="""
Padrões de identificação suportados:
  - Standard: S10_005, N3_007, T15_002
  - Extended: HSP1_001, HGPE_045
  - Simple: S10, N3, T15
  - Custom: isolado1, sample_001
  - Generic: qualquer letra seguida de números

Filtros disponíveis:
  - Tamanho mínimo e máximo dos contigs
  - Padrões regex customizados

Formatos de saída:
  - FASTA (padrão)
  - GenBank

Exemplos de uso:
  %(prog)s input.fasta output_dir/
  %(prog)s input.fasta output_dir/ --custom-pattern "isolate_(\d+)"
  %(prog)s input.fasta output_dir/ --min-length 500 --max-length 10000
  %(prog)s input.fasta output_dir/ --analyze-only
  %(prog)s input.fasta output_dir/ --dry-run --verbose
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "fasta_path", 
        help="Caminho do arquivo FASTA multi-sequência"
    )
    parser.add_argument(
        "output_dir", 
        help="Diretório de saída para os arquivos separados"
    )
    parser.add_argument(
        "--custom-pattern",
        help="Padrão regex customizado para extrair ID do isolado"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=0,
        help="Tamanho mínimo dos contigs (padrão: 0)"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        help="Tamanho máximo dos contigs"
    )
    parser.add_argument(
        "--output-format",
        choices=["fasta", "genbank"],
        default="fasta",
        help="Formato de saída (padrão: fasta)"
    )
    parser.add_argument(
        "--analyze-only", "-a",
        action="store_true",
        help="Apenas analisa o arquivo sem separar contigs"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Apenas simula as operações sem executar"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Saída detalhada"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Verificar dependências
    if not validate_dependencies():
        sys.exit(1)
    
    if args.dry_run:
        logging.info("MODO DRY RUN - Nenhuma alteração será feita")
    
    if args.analyze_only:
        logging.info("MODO ANÁLISE - Apenas analisando arquivo")
    
    try:
        operation_stats = separar_contigs_por_isolado(
            args.fasta_path,
            args.output_dir,
            args.custom_pattern,
            args.min_length,
            args.max_length,
            args.dry_run,
            args.analyze_only,
            args.output_format
        )
        
        if not args.analyze_only:
            print_operation_summary(operation_stats)
        
        # Verificar se houve problemas
        if operation_stats.get('unidentified_sequences', 0) > 0:
            logging.warning("Algumas sequências não puderam ser identificadas")
            logging.warning("Considere usar --custom-pattern com um padrão específico")
        
        if operation_stats.get('files_created', 0) == 0 and not args.analyze_only:
            logging.error("Nenhum arquivo foi criado!")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Erro durante a execução: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
