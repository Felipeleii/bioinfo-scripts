<h1 align="center">🧬 bioinfo-scripts</h1>
<p align="center">Useful scripts for Bioinformatics - Bacterial Illumina WGS Analysis and Pipelines</p>

---

## 📁 Bioinformatics Scripts

This repository contains useful scripts for data analysis in bioinformatics, including:
    
- 🔄 Scripts of renaming files FASTQ and FASTA
- 🧪 Formulas for MIC Interpretation (EUCAST)  
- 🌐 Automatic script converter for use in HTML
- 📊 Pipeline for viewing and organizing reports

---

## 🔗 Scripts Download for Data Management/Preparation for Analysis

<p align="center">
  👉 <a href="https://felipeleii.github.io/bioinfo-scripts/">https://felipeleii.github.io/bioinfo-scripts/</a>
</p>

---

## 📚 Useful Links

### 🔍 Tools and Guides

- [SRA Run Selector](https://www.ncbi.nlm.nih.gov/Traces/study/)  
- [Free Online JSON Formatter](https://www.freeformatter.com/json-escape.html#before-output)  
- [Convert List to CSV (Column to Comma)](https://capitalizemytitle.com/tools/column-to-comma-separated-list/)  
- [Remove Line Breaks Tool](https://www.textfixer.com/tools/remove-line-breaks.php)  
- [rTS Wiki – OS Management Tips](https://rtech.support/)  
- [Unix-command-summary](https://github.com/GunzIvan28/Unix-command-summary)
- [fasteR: Fast Lane Guide to Learning R!](https://github.com/matloff/fasteR)
- [Conda Cheatsheet](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html)
- [OpenWetWare: SOPs and Protocols for biology & biological engineering](https://openwetware.org/wiki/Protocols)
- [Stock Solution Calculator](https://goldbio.com/stock-solution-calculator)
- [LabHacks Lab.hacks Your Personal Lab Assistant - Mobile App](https://labhacks.net/)
- [Compare EUROPE: Laboratory Operating Procedures (LOPs) or Standard Operating Procedures (SOPs)](https://www.compare-europe.eu/library/protocols-and-sops.)
-[ShareBiology Buffers and Solutions Preparation Guides](https://sharebiology.com/)
---

## 🧬 Pipelines WGS - Bacterial AMR

- [AbritAMR](https://github.com/MDU-PHL/abritamr)
- [Grenepipe (Wiki)](https://github.com/moiexpositoalonsolab/grenepipe/wiki)  
- [rMAP](https://github.com/GunzIvan28/rMAP)
- [TORMES](https://github.com/nmquijada/tormes?tab=readme-ov-file#output)
- [BACANNOT](https://github.com/fmalmeida/bacannot)
- [Nullarbor - Pipeline to generate complete public health microbiology reports from sequenced isolates](https://github.com/tseemann/nullarbor)
- [PHoeNIx: A short-read pipeline for healthcare-associated and antimicrobial resistant pathogens](https://github.com/CDCgov/phoenix?tab=readme-ov-file)
- [GeneMates – Horizontal gene co-transfer in R](https://github.com/wanyuac/GeneMates?tab=readme-ov-file#majorOutput)  
- [ARETE – Antimicrobial Resistance: Emergence, Transmission, and Ecology](https://github.com/beiko-lab/arete)
- [PRAWNS: Pan-genome representation of whole genomes tool](https://github.com/KiranJavkar/PRAWNS)
- [Center for Genomic Epidemiology](https://genomicepidemiology.org/services/)
- [Kaptive - Klebsiella pneumoniae and Acinetobacter baumannii surface polysaccharide loci reports](https://github.com/klebgenomics/Kaptive)
- [Kleborate:screening genome assemblies of Klebsiella pneumoniae and the Klebsiella pneumoniae species complex (KpSC)](https://github.com/klebgenomics/Kleborate)

  ## Web-based platforms for AMR analysis and reporting:
- [Proksee: in-depth characterization and visualization of bacterial genomes](https://proksee.ca/)
- [BV-BRC: BACTERIAL AND VIRAL BIOINFORMATICS RESOURCE CENTER](https://www.bv-brc.org/)
- [Galaxy@Sciensano - Curated Pathogens Pipelines with pretty reports](https://galaxy.sciensano.be/)
- [Galaxy Europe](https://usegalaxy.eu/)
- [Galaxy US](https://usegalaxy.org/)
- [Mapchart: Create custom maps](https://mapchart.net/)
- [RAWGraphs: Easy data-visualization and plots](https://app.rawgraphs.io/)

  ## Useful Databases links
- [Bowtie, HISAT, Kraken/Braken, Centrifuge DB's](https://benlangmead.github.io/aws-indexes/k2)
- [BLDB: Beta-Lactamase DataBase](http://www.bldb.eu/)
- [Bacterial Taxonomy Database LPSN - List of Prokaryotic names with Standing in Nomenclature](https://lpsn.dsmz.de/)
- [INTEGRALL:The Integron Database](http://integrall.bio.ua.pt/?links)


# 📁 Scripts de Bioinformática - Renomeação e Ambientes Conda

## 🐍 renomear_fastq_pasta(pasta)
```python
import os
import re

def renomear_fastq_pasta(pasta):
    for nome_arquivo in os.listdir(pasta):
        if nome_arquivo.endswith('.fastq.gz'):
            partes = nome_arquivo.split("_")
            novo_nome = f"{partes[0]}_{partes[-1]}"
            os.rename(os.path.join(pasta, nome_arquivo), os.path.join(pasta, novo_nome))
```

### ✅ O que faz:
Renomeia arquivos `.fastq.gz`, mantendo apenas o **primeiro** e o **último** bloco do nome separados por underline (`_`).

### 🔄 Exemplo:
| Antes             | Depois           |
|------------------|------------------|
| N1_010_1.fastq.gz | N1_1.fastq.gz    |
| S2_078_2.fastq.gz | S2_2.fastq.gz    |

---

## 🐚 Script Bash: Restaurar ambiente Conda do TORMES
```bash
#!/bin/bash

echo "[INFO] Removendo ambiente antigo tormes-1.3.0 (se existir)..."
conda deactivate
conda env remove -n tormes-1.3.0 -y

echo "[INFO] Restaurando ambiente TORMES a partir do backup..."
conda env create -f tormes-1.3.0_backup.yml

echo "[INFO] Ambiente TORMES restaurado com sucesso!"
echo "Use: conda activate tormes-1.3.0"
```

### ✅ O que faz:
1. Desativa o ambiente Conda atual.
2. Remove o ambiente `tormes-1.3.0`, se existir.
3. Restaura a partir do arquivo `tormes-1.3.0_backup.yml`.

---

## 🐳 Dockerfile: Ambiente Conda para TORMES
```dockerfile
FROM continuumio/miniconda3:4.10.3

COPY tormes-1.3.0_backup.yml /tmp/tormes-1.3.0_backup.yml
RUN conda env create -f /tmp/tormes-1.3.0_backup.yml
SHELL ["/bin/bash", "-c"]
RUN echo "conda activate tormes-1.3.0" >> ~/.bashrc
ENV PATH /opt/conda/envs/tormes-1.3.0/bin:$PATH
ENTRYPOINT ["/bin/bash"]
```

### ✅ O que faz:
Cria uma imagem Docker com o ambiente `tormes-1.3.0` restaurado e ativado.

---

## 🐍 renomear_fasta_pasta(pasta)
```python
import os

def renomear_fasta_pasta(pasta):
    for nome_arquivo in os.listdir(pasta):
        if nome_arquivo.endswith('.fasta'):
            partes = nome_arquivo.split("_")
            novo_nome = f"{partes[0]}.fasta"
            caminho_antigo = os.path.join(pasta, nome_arquivo)
            caminho_novo = os.path.join(pasta, novo_nome)
            if os.path.exists(caminho_novo):
                print(f"[Aviso] Arquivo {caminho_novo} já existe! Pulando {nome_arquivo}.")
            else:
                os.rename(caminho_antigo, caminho_novo)
                print(f"{nome_arquivo} renomeado para {novo_nome}")
```

### ✅ O que faz:
Renomeia arquivos `.fasta`, mantendo **apenas o primeiro campo** antes do `_` como nome do arquivo.

### 🔄 Exemplo:
| Antes                                     | Depois         |
|-------------------------------------------|----------------|
| HSP1_001_Klebsiella pneumoniae.fasta      | HSP1.fasta     |
| HGPE_045_Acinetobacter baumannii.fasta    | HGPE.fasta     |

---

## 🧬 separar_contigs_por_isolado(fasta_path, output_dir)
```python
from Bio import SeqIO
from collections import defaultdict
import os
import re

def separar_contigs_por_isolado(fasta_path, output_dir):
    isolados = defaultdict(list)
    for record in SeqIO.parse(fasta_path, "fasta"):
        match = re.search(r"(S\d+_\d+|N\d+_\d+|T\d+_\d+)", record.description)
        if match:
            isolados[match.group()].append(record)

    os.makedirs(output_dir, exist_ok=True)
    for isolado, contigs in isolados.items():
        with open(os.path.join(output_dir, f"{isolado}.fasta"), "w") as out_f:
            SeqIO.write(contigs, out_f, "fasta")
```

### ✅ O que faz:
Separa contigs de um arquivo multi-FASTA em arquivos separados para cada isolado com identificador do tipo `S10_005`, `N3_007`, etc.

### 🔄 Exemplo:
#### Entrada:
```
>... S10_005 ...
>... S10_005 ...
>... N3_007 ...
```
#### Saída:
- `S10_005.fasta` com 2 contigs
- `N3_007.fasta` com 1 contig

