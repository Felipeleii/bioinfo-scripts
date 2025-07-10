#!usrbinenv python3

Bactopia Prepare - Data preparation tool for Bactopia pipeline
Author Felipe Lei
Description Prepares FASTQ files and generates necessary configuration files
             for running the Bactopia bacterial genome analysis pipeline.


import argparse
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Tuple
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BactopiaPrepare
    Prepare data and configuration files for Bactopia pipeline.
    
    def __init__(self, project_name str, fastq_dir Path)
        
        Initialize Bactopia preparation.
        
        Args
            project_name Name of the project
            fastq_dir Directory containing FASTQ files
        
        self.project_name = project_name
        self.fastq_dir = fastq_dir
        self.samples = []
        self.paired_pattern = re.compile(r'(.+)(_R[12]_[12].R[12]).(fastqfq)(.gz)$')
        
    def scan_fastq_directory(self) - List[Dict[str, str]]
        
        Scan directory for FASTQ files and identify pairs.
        
        Returns
            List of sample dictionaries
        
        fastq_files = []
        
        # Find all FASTQ files
        for pattern in ['.fastq', '.fastq.gz', '.fq', '.fq.gz']
            fastq_files.extend(self.fastq_dir.glob(pattern))
        
        # Group paired-end files
        paired_files = {}
        single_files = []
        
        for file in sorted(fastq_files)
            match = self.paired_pattern.match(file.name)
            if match
                sample_name = match.group(1)
                read_num = match.group(2)
                
                if sample_name not in paired_files
                    paired_files[sample_name] = {}
                
                if '1' in read_num
                    paired_files[sample_name]['R1'] = file
                elif '2' in read_num
                    paired_files[sample_name]['R2'] = file
            else
                single_files.append(file)
        
        # Create sample list
        samples = []
        
        # Add paired-end samples
        for sample_name, reads in paired_files.items()
            if 'R1' in reads and 'R2' in reads
                samples.append({
                    'sample' sample_name,
                    'runtype' 'paired-end',
                    'r1' str(reads['R1'].absolute()),
                    'r2' str(reads['R2'].absolute()),
                    'extra' ''
                })
            else
                # Unpaired file from what should be paired
                for read_file in reads.values()
                    samples.append({
                        'sample' sample_name,
                        'runtype' 'single-end',
                        'r1' str(read_file.absolute()),
                        'r2' '',
                        'extra' ''
                    })
        
        # Add single-end samples
        for file in single_files
            sample_name = file.stem.replace('.fastq', '').replace('.fq', '')
            samples.append({
                'sample' sample_name,
                'runtype' 'single-end',
                'r1' str(file.absolute()),
                'r2' '',
                'extra' ''
            })
        
        self.samples = samples
        logger.info(fFound {len(samples)} samples ({len([s for s in samples if s['runtype'] == 'paired-end'])} paired-end, 
                   f{len([s for s in samples if s['runtype'] == 'single-end'])} single-end))
        
        return samples
    
    def create_sample_sheet(self, output_path Path = None) - Path
        
        Create Bactopia sample sheet (FOFN - File of File Names).
        
        Args
            output_path Path to save the sample sheet
            
        Returns
            Path to the created sample sheet
        
        if output_path is None
            output_path = Path(f{self.project_name}_samples.txt)
        
        with open(output_path, 'w', newline='') as f
            writer = csv.DictWriter(f, fieldnames=['sample', 'runtype', 'r1', 'r2', 'extra'], 
                                  delimiter='t')
            writer.writeheader()
            writer.writerows(self.samples)
        
        logger.info(fCreated sample sheet {output_path})
        return output_path
    
    def create_config_file(self, params Dict[str, any]) - Path
        
        Create Bactopia configuration file.
        
        Args
            params Dictionary of Bactopia parameters
            
        Returns
            Path to the created config file
        
        config = {
            'project_name' self.project_name,
            'created' datetime.now().isoformat(),
            'samples' len(self.samples),
            'parameters' params,
            'workflow_params' {
                'max_cpus' params.get('cpus', 8),
                'max_memory' params.get('memory', '32.GB'),
                'outdir' f{self.project_name}_results
            }
        }
        
        config_path = Path(f{self.project_name}_config.json)
        with open(config_path, 'w') as f
            json.dump(config, f, indent=2)
        
        logger.info(fCreated configuration file {config_path})
        return config_path
    
    def generate_run_script(self, params Dict[str, any]) - Path
        
        Generate a shell script to run Bactopia.
        
        Args
            params Dictionary of Bactopia parameters
            
        Returns
            Path to the created script
        
        script_path = Path(frun_{self.project_name}_bactopia.sh)
        
        with open(script_path, 'w') as f
            f.write(#!binbashn)
            f.write(f# Bactopia run script for project {self.project_name}n)
            f.write(f# Generated {datetime.now().isoformat()}nn)
            
            f.write(# Check if Bactopia is availablen)
            f.write(if ! command -v bactopia & devnull; thenn)
            f.write(    echo 'Error Bactopia is not installed or not in PATH'n)
            f.write(    exit 1n)
            f.write(finn)
            
            f.write(f# Create output directoryn)
            f.write(fmkdir -p {self.project_name}_resultsnn)
            
            f.write(# Run Bactopian)
            f.write(bactopia n)
            f.write(f    --samples {self.project_name}_samples.txt n)
            f.write(f    --outdir {self.project_name}_results n)
            f.write(f    --max_cpus {params.get('cpus', 8)} n)
            f.write(f    --max_memory {params.get('memory', '32.GB')} n)
            
            # Add optional parameters
            if params.get('genome')
                f.write(f    --genome {params['genome']} n)
            
            if params.get('species')
                f.write(f    --species '{params['species']}' n)
            
            # Add workflow options
            workflows = []
            if params.get('qc', True)
                workflows.append('qc')
            if params.get('assembly', True)
                workflows.append('assembly')
            if params.get('annotation', True)
                workflows.append('annotation')
            if params.get('mlst', True)
                workflows.append('mlst')
            if params.get('amr', True)
                workflows.append('amr')
            
            if workflows
                f.write(f    --workflows {','.join(workflows)} n)
            
            f.write(    --conda-auto-installnn)
            
            f.write(# Check exit statusn)
            f.write(if [ $ -eq 0 ]; thenn)
            f.write(f    echo 'Bactopia completed successfully! Results in {self.project_name}_results'n)
            f.write(elsen)
            f.write(    echo 'Bactopia failed. Check the logs for details.'n)
            f.write(    exit 1n)
            f.write(fin)
        
        # Make script executable
        script_path.chmod(0o755)
        
        logger.info(fCreated run script {script_path})
        return script_path
    
    def validate_samples(self) - List[str]
        
        Validate sample files and check for common issues.
        
        Returns
            List of warning messages
        
        warnings = []
        
        for sample in self.samples
            # Check if files exist
            if not Path(sample['r1']).exists()
                warnings.append(fFile not found {sample['r1']})
            
            if sample['r2'] and not Path(sample['r2']).exists()
                warnings.append(fFile not found {sample['r2']})
            
            # Check file sizes
            r1_size = Path(sample['r1']).stat().st_size if Path(sample['r1']).exists() else 0
            if r1_size == 0
                warnings.append(fEmpty file {sample['r1']})
            
            # Check for mismatched pairs
            if sample['runtype'] == 'paired-end'
                r2_size = Path(sample['r2']).stat().st_size if Path(sample['r2']).exists() else 0
                if abs(r1_size - r2_size)  max(r1_size, r2_size, 1)  0.1
                    warnings.append(fPaired files have significantly different sizes {sample['sample']})
        
        return warnings


def main()
    Main function to handle command line interface.
    parser = argparse.ArgumentParser(
        description=Prepare data for Bactopia pipeline,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=
Examples
  # Basic usage
  python bactopia_prepare.py -n MyProject -d pathtofastq
  
  # With reference genome
  python bactopia_prepare.py -n MyProject -d pathtofastq -g reference.fasta
  
  # Specify species and workflows
  python bactopia_prepare.py -n MyProject -d pathtofastq 
    --species Escherichia coli --workflows qc,assembly,annotation
        
    )
    
    parser.add_argument('-n', '--name', required=True,
                        help='Project name')
    parser.add_argument('-d', '--directory', required=True,
                        help='Directory containing FASTQ files')
    parser.add_argument('-g', '--genome', 
                        help='Reference genome (optional)')
    parser.add_argument('-s', '--species',
                        help='Species name for species-specific datasets')
    parser.add_argument('--cpus', type=int, default=8,
                        help='Maximum CPUs to use (default 8)')
    parser.add_argument('--memory', default='32.GB',
                        help='Maximum memory to use (default 32.GB)')
    parser.add_argument('--workflows', default='qc,assembly,annotation,mlst,amr',
                        help='Comma-separated list of workflows to run')
    parser.add_argument('--validate', action='store_true',
                        help='Validate samples and show warnings')
    parser.add_argument('-o', '--output-dir', default='.',
                        help='Output directory for configuration files')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    fastq_dir = Path(args.directory)
    output_dir = Path(args.output_dir)
    
    if not fastq_dir.exists()
        logger.error(fDirectory not found {fastq_dir})
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize preparer
    preparer = BactopiaPrepare(args.name, fastq_dir)
    
    # Scan for FASTQ files
    samples = preparer.scan_fastq_directory()
    
    if not samples
        logger.error(No FASTQ files found in the specified directory)
        sys.exit(1)
    
    # Validate if requested
    if args.validate
        warnings = preparer.validate_samples()
        if warnings
            logger.warning(Validation warnings)
            for warning in warnings
                logger.warning(f  - {warning})
    
    # Parse workflows
    workflows = args.workflows.split(',')
    params = {
        'cpus' args.cpus,
        'memory' args.memory,
        'qc' 'qc' in workflows,
        'assembly' 'assembly' in workflows,
        'annotation' 'annotation' in workflows,
        'mlst' 'mlst' in workflows,
        'amr' 'amr' in workflows
    }
    
    if args.genome
        params['genome'] = args.genome
    if args.species
        params['species'] = args.species
    
    # Create output files
    sample_sheet = preparer.create_sample_sheet(output_dir  f{args.name}_samples.txt)
    config_file = preparer.create_config_file(params)
    run_script = preparer.generate_run_script(params)
    
    # Print summary
    print(fn=== Bactopia Preparation Complete ===)
    print(fProject {args.name})
    print(fSamples found {len(samples)})
    print(fSample sheet {sample_sheet})
    print(fConfig file {config_file})
    print(fRun script {run_script})
    print(fnTo run Bactopia, execute)
    print(f  bash {run_script})


if __name__ == __main__
    main()
