#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import csv
import re
import subprocess

DEFAULT_DIR = "/home/labalerta/Felipe/SRA_CNPQ"

class LocalPrepareGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bactopia Prepare Local (Completo)")

        self.fastq_dir = tk.StringVar()
        self.metadata_file = tk.StringVar()
        self.species = tk.StringVar(value="Klebsiella pneumoniae")
        self.genome_size = tk.StringVar(value="unknown")
        self.recursive = tk.BooleanVar(value=False)

        self.build_gui()

    def build_gui(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(side="left", fill="both", expand=True)

        tk.Label(frame, text="Pasta com FASTQs:").pack(anchor="w")
        tk.Entry(frame, textvariable=self.fastq_dir, width=50).pack(pady=5)
        tk.Button(frame, text="Escolher Pasta", command=self.choose_fastq_dir).pack(pady=5)

        tk.Label(frame, text="Salvar metadata.txt em:").pack(anchor="w", pady=(20,0))
        tk.Entry(frame, textvariable=self.metadata_file, width=50).pack(pady=5)
        tk.Button(frame, text="Escolher Arquivo", command=self.choose_metadata_file).pack(pady=5)

        tk.Label(frame, text="Espécie:", pady=(20)).pack(anchor="w")
        tk.Radiobutton(frame, text="Klebsiella pneumoniae", variable=self.species, value="Klebsiella pneumoniae").pack(anchor="w")
        tk.Radiobutton(frame, text="Acinetobacter baumannii", variable=self.species, value="Acinetobacter baumannii").pack(anchor="w")

        tk.Label(frame, text="Genome Size (opcional, bp):").pack(anchor="w", pady=(20,0))
        tk.Entry(frame, textvariable=self.genome_size, width=20).pack(pady=5)

        tk.Checkbutton(frame, text="Buscar arquivos recursivamente", variable=self.recursive).pack(anchor="w", pady=(10,0))

        tk.Button(frame, text="Gerar Metadata", command=self.run_prepare, bg="green", fg="white").pack(pady=(30,10))

    def choose_fastq_dir(self):
        path = filedialog.askdirectory(initialdir=DEFAULT_DIR, title="Selecione a pasta de FASTQ")
        if path:
            self.fastq_dir.set(path)

    def choose_metadata_file(self):
        file = filedialog.asksaveasfilename(initialdir=DEFAULT_DIR, title="Salvar metadata.txt",
                                            defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt")])
        if file:
            self.metadata_file.set(file)

    def run_prepare(self):
        fastq_dir = self.fastq_dir.get()
        metadata_file = self.metadata_file.get()
        species = self.species.get()
        genome_size = self.genome_size.get()
        recursive = self.recursive.get()

        if not fastq_dir or not metadata_file:
            messagebox.showerror("Erro", "Todos os campos devem ser preenchidos!")
            return

        # Buscar arquivos
        fastq_files = []
        if recursive:
            for root, _, files in os.walk(fastq_dir):
                for file in files:
                    if file.endswith(".fastq.gz"):
                        fastq_files.append(os.path.join(root, file))
        else:
            fastq_files = [os.path.join(fastq_dir, f) for f in os.listdir(fastq_dir) if f.endswith(".fastq.gz")]

        if not fastq_files:
            messagebox.showerror("Erro", "Nenhum arquivo FASTQ encontrado.")
            return

        # Mapear samples
        samples = {}
        for fpath in fastq_files:
            fname = os.path.basename(fpath)
            sample_base = re.split(r"_R?[12]|_[12]", fname)[0]
            if sample_base not in samples:
                samples[sample_base] = {"r1": "", "r2": "", "se": ""}
            if re.search(r"_R?1|_1", fname):
                samples[sample_base]["r1"] = fpath
            elif re.search(r"_R?2|_2", fname):
                samples[sample_base]["r2"] = fpath
            else:
                samples[sample_base]["se"] = fpath

        # Escrever metadata.txt
        headers = ["sample", "runtype", "genome_size", "species", "r1", "r2", "extra"]

        try:
            with open(metadata_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
                writer.writeheader()
                for sample, reads in samples.items():
                    if reads["r1"] and reads["r2"]:
                        runtype = "paired-end"
                    elif reads["se"]:
                        runtype = "single-end"
                    else:
                        continue

                    writer.writerow({
                        "sample": sample,
                        "runtype": runtype,
                        "genome_size": genome_size,
                        "species": species,
                        "r1": reads["r1"] or reads["se"],
                        "r2": reads["r2"],
                        "extra": ""
                    })

            messagebox.showinfo("Sucesso", f"Metadata gerado em:\n\n{metadata_file}")

            open_dir = messagebox.askyesno("Abrir Pasta", "Deseja abrir a pasta do metadata?")
            if open_dir:
                os.system(f'xdg-open "{os.path.dirname(metadata_file)}"')

            run_bactopia = messagebox.askyesno("Rodar Bactopia?", "Deseja iniciar o processamento com Bactopia agora?")
            if run_bactopia:
                self.run_bactopia(metadata_file)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar metadata:\n{e}")

    def run_bactopia(self, metadata_file):
        # Gerar outdir baseado no nome do metadata
        base_name = os.path.basename(metadata_file).replace(".txt", "").replace(".tsv", "")
        outdir = os.path.join(os.path.dirname(metadata_file), f"{base_name}_results")

        try:
            cmd = [
                "nextflow", "run", "bactopia/bactopia",
                "--samples", metadata_file,
                "--outdir", outdir,
                "-profile", "docker"
            ]
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Sucesso", f"Bactopia rodando!\nResultados em:\n{outdir}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao rodar Bactopia:\n{e}")

def main():
    root = tk.Tk()
    app = LocalPrepareGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

