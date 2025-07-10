#!/usr/bin/env python3
"""
MultiFASTA Generator with Source Tracking
Author: Felipe Lei
Description: Creates multiFASTA files with automatic source tracking by incorporating 
             the filename into each contig header for sample origin identification.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple
import gzip
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MultiFastaGenerator:
    """Generate MultiFASTA files with source tracking capabilities."""
    
    def __init__(self, prefix_format: str = "{filename}_contig{num}_{original}"):
        """
        Initialize the generator with a specific header format.
        
        Args:
            prefix_format: Format string for the new headers
        """
        self.prefix_format = prefix_format
        self.processed_files = 0
        self.total_contigs = 0
    
    def read_fasta(self, filepath: Path) -> List[Tuple[str, str]]:
        """
        Read a FASTA file and return list of (header, sequence) tuples.
        
        Args:
            filepath: Path to the FASTA file
            
        Returns:
            List of tuples containing (header, sequence)
        """
        sequences = []
        current_header = None
        current_seq = []
        
        # Handle gzipped files
        if filepath.suffix == '.gz':
            open_func = gzip.open
            mode = 'rt'
        else:
            open_func = open
            mode = 'r'
        
        try:
            with open_func(filepath, mode) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('>'):
                        if current_header:
                            sequences.append((current_header, ''.join(current_seq)))
                        current_header = line[1:]  # Remove '>'
                        current_seq = []
                    else:
                        current_seq.append(line)
                
                # Don't forget the last sequence
                if current_header:
                    sequences.append((current_header, ''.join(current_seq)))
                    
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return []
        
        return sequences
    
    def process_single_file(self, filepath: Path, custom_prefix: str = None) -> str:
        """
        Process a single FASTA file and add source tracking to headers.
        
        Args:
            filepath: Path to the FASTA file
            custom_prefix: Custom prefix to use instead of filename
            
        Returns:
            Processed FASTA content as string
        """
        sequences = self.read_fasta(filepath)
        if not sequences:
            return ""
        
        # Get prefix from filename or use custom prefix
        if custom_prefix:
            prefix = custom_prefix
        else:
            prefix = filepath.stem.replace('.fasta', '').replace('.fa', '').replace('.fna', '')
        
        processed_lines = []
        contig_num = 1
        
        for header, sequence in sequences:
            # Create new header with source tracking
            new_header = self.prefix_format.format(
                filename=prefix,
                num=contig_num,
                original=header
            )
            
            processed_lines.append(f">{new_header}")
            
            # Add sequence in chunks of 80 characters (standard FASTA width)
            for i in range(0, len(sequence), 80):
                processed_lines.append(sequence[i:i+80])
            
            contig_num += 1
            self.total_contigs += 1
        
        self.processed_files += 1
        logger.info(f"Processed {filepath.name}: {len(sequences)} contigs")
        
        return '\n'.join(processed_lines)
    
    def process_batch(self, filepaths: List[Path], merge: bool = False) -> dict:
        """
        Process multiple FASTA files.
        
        Args:
            filepaths: List of paths to FASTA files
            merge: If True, merge all files into one; if False, keep separate
            
        Returns:
            Dictionary with filenames as keys and processed content as values
        """
        results = {}
        merged_content = []
        
        for filepath in filepaths:
            processed = self.process_single_file(filepath)
            if processed:
                if merge:
                    merged_content.append(processed)
                else:
                    output_name = f"{filepath.stem}_tracked.fasta"
                    results[output_name] = processed
        
        if merge:
            results['merged_multifasta.fasta'] = '\n'.join(merged_content)
        
        return results
    
    def save_results(self, results: dict, output_dir: Path):
        """
        Save processed FASTA files to disk.
        
        Args:
            results: Dictionary of filename -> content
            output_dir: Directory to save files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in results.items():
            output_path = output_dir / filename
            with open(output_path, 'w') as f:
                f.write(content)
            logger.info(f"Saved: {output_path}")
    
    def print_summary(self):
        """Print processing summary."""
        print(f"\n=== Processing Summary ===")
        print(f"Files processed: {self.processed_files}")
        print(f"Total contigs: {self.total_contigs}")
        print(f"Average contigs per file: {self.total_contigs/self.processed_files:.1f}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate MultiFASTA files with automatic source tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python multifasta_generator.py -i sample.fasta -o output/
  
  # Process multiple files and merge
  python multifasta_generator.py -i *.fasta -o output/ --merge
  
  # Process with custom prefix
  python multifasta_generator.py -i sample.fasta -o output/ --prefix MyProject
  
  # Custom header format
  python multifasta_generator.py -i sample.fasta -o output/ \\
    --format "{filename}|contig_{num}|{original}"
        """
    )
    
    parser.add_argument('-i', '--input', nargs='+', required=True,
                        help='Input FASTA file(s)')
    parser.add_argument('-o', '--output', default='.',
                        help='Output directory (default: current directory)')
    parser.add_argument('--merge', action='store_true',
                        help='Merge all input files into one MultiFASTA')
    parser.add_argument('--prefix', type=str,
                        help='Custom prefix to use instead of filename')
    parser.add_argument('--format', type=str,
                        default="{filename}_contig{num}_{original}",
                        help='Header format string (default: {filename}_contig{num}_{original})')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert input files to Path objects
    input_files = []
    for pattern in args.input:
        paths = list(Path().glob(pattern))
        if not paths:
            # If glob doesn't match, treat as literal path
            path = Path(pattern)
            if path.exists():
                paths = [path]
            else:
                logger.error(f"File not found: {pattern}")
                sys.exit(1)
        input_files.extend(paths)
    
    if not input_files:
        logger.error("No input files found")
        sys.exit(1)
    
    # Create generator and process files
    generator = MultiFastaGenerator(prefix_format=args.format)
    
    if len(input_files) == 1 and not args.merge:
        # Single file processing
        content = generator.process_single_file(input_files[0], args.prefix)
        if content:
            output_name = f"{input_files[0].stem}_tracked.fasta"
            generator.save_results({output_name: content}, Path(args.output))
    else:
        # Batch processing
        results = generator.process_batch(input_files, merge=args.merge)
        generator.save_results(results, Path(args.output))
    
    generator.print_summary()


if __name__ == "__main__":
    main()
