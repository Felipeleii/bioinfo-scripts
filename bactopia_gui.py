#!/usr/bin/env python3
"""
GUI Bactopia - Versão Otimizada
Interface gráfica para preparar metadata e executar Bactopia.

Autor: Felipe Lei
Versão: 2.0
Data: 2025-06-22

Dependências: tkinter, pandas
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import pandas as pd

class BactopiaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bactopia Pipeline GUI v2.0")
        self.root.geometry("1000x700")
        
        # Variáveis
        self.fastq_dir = tk.StringVar()
        self.output_metadata = tk.StringVar()
        self.output_results = tk.StringVar()
        self.species = tk.StringVar(value="Klebsiella pneumoniae")
        self.genome_size = tk.StringVar(value="5500000")
        self.recursive_search = tk.BooleanVar(value=False)
        self.auto_run_bactopia = tk.BooleanVar(value=False)
        self.use_docker = tk.BooleanVar(value=True)
        self.cpu_cores = tk.StringVar(value="4")
        self.memory_gb = tk.StringVar(value="8")
        
        # Lista de espécies comuns
        self.species_list = [
            "Klebsiella pneumoniae",
            "Acinetobacter baumannii",
            "Escherichia coli",
            "Staphylococcus aureus",
            "Pseudomonas aeruginosa",
            "Enterococcus faecium",
            "Enterococcus faecalis",
            "Salmonella enterica",
            "Listeria monocytogenes",
            "Mycobacterium tuberculosis"
        ]
        
        # Genomas de referência aproximados (bp)
        self.genome_sizes = {
            "Klebsiella pneumoniae": "5500000",
            "Acinetobacter baumannii": "4000000", 
            "Escherichia coli": "5000000",
            "Staphylococcus aureus": "2800000",
            "Pseudomonas aeruginosa": "6300000",
            "Enterococcus faecium": "2700000",
            "Enterococcus faecalis": "3200000",
            "Salmonella enterica": "4800000",
            "Listeria monocytogenes": "3000000",
            "Mycobacterium tuberculosis": "4400000"
        }
        
        self.samples_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do usuário."""
        # Notebook para abas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Configuração
        self.setup_config_tab(notebook)
        
        # Aba 2: Amostras
        self.setup_samples_tab(notebook)
        
        # Aba 3: Execução
        self.setup_execution_tab(notebook)
        
        # Aba 4: Log
        self.setup_log_tab(notebook)
        
    def setup_config_tab(self, notebook):
        """Configura a aba de configuração."""
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuração")
        
        # Frame principal com scroll
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Seção: Diretórios
        dirs_group = ttk.LabelFrame(scrollable_frame, text="Diretórios", padding=10)
        dirs_group.pack(fill=tk.X, padx=5, pady=5)
        
        # Diretório FASTQ
        ttk.Label(dirs_group, text="Diretório FASTQ:").pack(anchor=tk.W)
        fastq_frame = ttk.Frame(dirs_group)
        fastq_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(fastq_frame, textvariable=self.fastq_dir, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(fastq_frame, text="Procurar", command=self.select_fastq_dir).pack(side=tk.RIGHT, padx=(5,0))
        
        # Saída metadata
        ttk.Label(dirs_group, text="Arquivo metadata.txt (saída):").pack(anchor=tk.W, pady=(10,0))
        metadata_frame = ttk.Frame(dirs_group)
        metadata_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(metadata_frame, textvariable=self.output_metadata, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(metadata_frame, text="Salvar como", command=self.select_metadata_output).pack(side=tk.RIGHT, padx=(5,0))
        
        # Diretório resultados Bactopia
        ttk.Label(dirs_group, text="Diretório resultados Bactopia:").pack(anchor=tk.W, pady=(10,0))
        results_frame = ttk.Frame(dirs_group)
        results_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(results_frame, textvariable=self.output_results, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(results_frame, text="Procurar", command=self.select_results_dir).pack(side=tk.RIGHT, padx=(5,0))
        
        # Seção: Configurações da análise
        analysis_group = ttk.LabelFrame(scrollable_frame, text="Configurações da Análise", padding=10)
        analysis_group.pack(fill=tk.X, padx=5, pady=5)
        
        # Espécie
        ttk.Label(analysis_group, text="Espécie:").pack(anchor=tk.W)
        species_combo = ttk.Combobox(analysis_group, textvariable=self.species, values=self.species_list, width=50)
        species_combo.pack(fill=tk.X, pady=2)
        species_combo.bind('<<ComboboxSelected>>', self.on_species_selected)
        
        # Tamanho do genoma
        ttk.Label(analysis_group, text="Tamanho do genoma (bp):").pack(anchor=tk.W, pady=(10,0))
        ttk.Entry(analysis_group, textvariable=self.genome_size, width=20).pack(anchor=tk.W, pady=2)
        
        # Opções
        options_group = ttk.LabelFrame(scrollable_frame, text="Opções", padding=10)
        options_group.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Checkbutton(options_group, text="Busca recursiva em subdiretórios", variable=self.recursive_search).pack(anchor=tk.W)
        ttk.Checkbutton(options_group, text="Executar Bactopia automaticamente após gerar metadata", variable=self.auto_run_bactopia).pack(anchor=tk.W)
        ttk.Checkbutton(options_group, text="Usar Docker (recomendado)", variable=self.use_docker).pack(anchor=tk.W)
        
        # Recursos computacionais
        resources_group = ttk.LabelFrame(scrollable_frame, text="Recursos Computacionais", padding=10)
        resources_group.pack(fill=tk.X, padx=5, pady=5)
        
        cpu_frame = ttk.Frame(resources_group)
        cpu_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cpu_frame, text="CPUs:").pack(side=tk.LEFT)
        ttk.Entry(cpu_frame, textvariable=self.cpu_cores, width=10).pack(side=tk.LEFT, padx=(5,0))
        
        ttk.Label(cpu_frame, text="Memória (GB):").pack(side=tk.LEFT, padx=(20,0))
        ttk.Entry(cpu_frame, textvariable=self.memory_gb, width=10).pack(side=tk.LEFT, padx=(5,0))
        
        # Botões de ação
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(buttons_frame, text="Escanear Arquivos FASTQ", command=self.scan_fastq_files).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(buttons_frame, text="Gerar Metadata", command=self.generate_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Limpar Formulário", command=self.clear_form).pack(side=tk.RIGHT)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_samples_tab(self, notebook):
        """Configura a aba de amostras."""
        samples_frame = ttk.Frame(notebook)
        notebook.add(samples_frame, text="Amostras")
        
        # Treeview para mostrar amostras
        tree_frame = ttk.Frame(samples_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("sample", "fastq_1", "fastq_2", "genome_size", "status")
        self.samples_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.samples_tree.heading("sample", text="Amostra")
        self.samples_tree.heading("fastq_1", text="FASTQ R1")
        self.samples_tree.heading("fastq_2", text="FASTQ R2")
        self.samples_tree.heading("genome_size", text="Tamanho Genoma")
        self.samples_tree.heading("status", text="Status")
        
        self.samples_tree.column("sample", width=150)
        self.samples_tree.column("fastq_1", width=200)
        self.samples_tree.column("fastq_2", width=200)
        self.samples_tree.column("genome_size", width=120)
        self.samples_tree.column("status", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.samples_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.samples_tree.xview)
        self.samples_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.samples_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Botões para gerenciar amostras
        samples_buttons_frame = ttk.Frame(samples_frame)
        samples_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(samples_buttons_frame, text="Adicionar Amostra", command=self.add_sample_manually).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(samples_buttons_frame, text="Editar Selecionada", command=self.edit_selected_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(samples_buttons_frame, text="Remover Selecionada", command=self.remove_selected_sample).pack(side=tk.LEFT, padx=5)
        ttk.Button(samples_buttons_frame, text="Exportar CSV", command=self.export_samples_csv).pack(side=tk.RIGHT)
        
    def setup_execution_tab(self, notebook):
        """Configura a aba de execução."""
        exec_frame = ttk.Frame(notebook)
        notebook.add(exec_frame, text="Execução")
        
        # Área de comando
        command_group = ttk.LabelFrame(exec_frame, text="Comando Bactopia", padding=10)
        command_group.pack(fill=tk.X, padx=10, pady=10)
        
        self.command_text = scrolledtext.ScrolledText(command_group, height=8, wrap=tk.WORD)
        self.command_text.pack(fill=tk.X, pady=5)
        
        # Botões de execução
        exec_buttons_frame = ttk.Frame(exec_frame)
        exec_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(exec_buttons_frame, text="Gerar Comando", command=self.generate_bactopia_command).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(exec_buttons_frame, text="Executar Bactopia", command=self.run_bactopia).pack(side=tk.LEFT, padx=5)
        ttk.Button(exec_buttons_frame, text="Parar Execução", command=self.stop_execution).pack(side=tk.LEFT, padx=5)
        
        # Barra de progresso
        progress_group = ttk.LabelFrame(exec_frame, text="Progresso", padding=10)
        progress_group.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_var = tk.StringVar(value="Pronto para executar")
        ttk.Label(progress_group, textvariable=self.progress_var).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_group, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
    def setup_log_tab(self, notebook):
        """Configura a aba de log."""
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Log")
        
        # Área de log
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Botões do log
        log_buttons_frame = ttk.Frame(log_frame)
        log_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_buttons_frame, text="Limpar Log", command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_buttons_frame, text="Salvar Log", command=self.save_log).pack(side=tk.RIGHT)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Adiciona mensagem ao log."""
        timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def on_species_selected(self, event=None):
        """Atualiza tamanho do genoma quando espécie é selecionada."""
        species = self.species.get()
        if species in self.genome_sizes:
            self.genome_size.set(self.genome_sizes[species])
            
    def select_fastq_dir(self):
        """Seleciona diretório contendo arquivos FASTQ."""
        directory = filedialog.askdirectory(title="Selecionar diretório com arquivos FASTQ")
        if directory:
            self.fastq_dir.set(directory)
            self.log_message(f"Diretório FASTQ selecionado: {directory}")
            
    def select_metadata_output(self):
        """Seleciona arquivo de saída para metadata."""
        filename = filedialog.asksaveasfilename(
            title="Salvar metadata.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.output_metadata.set(filename)
            
    def select_results_dir(self):
        """Seleciona diretório para resultados do Bactopia."""
        directory = filedialog.askdirectory(title="Selecionar diretório para resultados")
        if directory:
            self.output_results.set(directory)
            
    def detect_paired_files(self, fastq_dir: Path) -> List[Dict]:
        """Detecta arquivos FASTQ paired-end e single-end."""
        samples = []
        fastq_files = []
        
        # Padrões para busca
        patterns = ["*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq"]
        
        for pattern in patterns:
            if self.recursive_search.get():
                fastq_files.extend(fastq_dir.rglob(pattern))
            else:
                fastq_files.extend(fastq_dir.glob(pattern))
        
        # Agrupar por nome base (sem _R1/_R2, _1/_2, etc.)
        paired_files = {}
        single_files = []
        
        for file_path in fastq_files:
            filename = file_path.name
            
            # Padrões para paired-end
            paired_patterns = [
                (r'(.+)_R1(_\d+)?\.f(ast)?q(\.gz)?$', r'(.+)_R2(_\d+)?\.f(ast)?q(\.gz)?$'),
                (r'(.+)_1\.f(ast)?q(\.gz)?$', r'(.+)_2\.f(ast)?q(\.gz)?$'),
                (r'(.+)\.R1\.f(ast)?q(\.gz)?$', r'(.+)\.R2\.f(ast)?q(\.gz)?$')
            ]
            
            is_paired = False
            for r1_pattern, r2_pattern in paired_patterns:
                r1_match = re.match(r1_pattern, filename, re.IGNORECASE)
                if r1_match:
                    base_name = r1_match.group(1)
                    # Procurar arquivo R2 correspondente
                    r2_file = None
                    for other_file in fastq_files:
                        r2_match = re.match(r2_pattern, other_file.name, re.IGNORECASE)
                        if r2_match and r2_match.group(1) == base_name:
                            r2_file = other_file
                            break
                    
                    if r2_file:
                        paired_files[base_name] = {
                            'sample': base_name,
                            'fastq_1': str(file_path),
                            'fastq_2': str(r2_file),
                            'genome_size': self.genome_size.get(),
                            'status': 'Paired-end'
                        }
                        is_paired = True
                        break
            
            if not is_paired:
                # Verificar se não é um arquivo R2 já processado
                is_r2 = any(re.match(pattern[1], filename, re.IGNORECASE) for pattern in paired_patterns)
                if not is_r2:
                    single_files.append({
                        'sample': Path(filename).stem.split('.')[0],
                        'fastq_1': str(file_path),
                        'fastq_2': '',
                        'genome_size': self.genome_size.get(),
                        'status': 'Single-end'
                    })
        
        # Combinar resultados
        samples.extend(paired_files.values())
        samples.extend(single_files)
        
        return samples
    
    def scan_fastq_files(self):
        """Escaneia arquivos FASTQ no diretório selecionado."""
        if not self.fastq_dir.get():
            messagebox.showerror("Erro", "Selecione um diretório FASTQ primeiro")
            return
            
        fastq_path = Path(self.fastq_dir.get())
        if not fastq_path.exists():
            messagebox.showerror("Erro", "Diretório FASTQ não existe")
            return
            
        self.log_message("Escaneando arquivos FASTQ...")
        
        try:
            samples = self.detect_paired_files(fastq_path)
            
            # Limpar tabela atual
            for item in self.samples_tree.get_children():
                self.samples_tree.delete(item)
            
            # Adicionar amostras à tabela
            self.samples_data = samples
            for sample in samples:
                self.samples_tree.insert("", "end", values=(
                    sample['sample'],
                    Path(sample['fastq_1']).name,
                    Path(sample['fastq_2']).name if sample['fastq_2'] else '',
                    sample['genome_size'],
                    sample['status']
                ))
            
            self.log_message(f"Encontradas {len(samples)} amostras")
            
        except Exception as e:
            self.log_message(f"Erro ao escanear arquivos: {e}", "ERROR")
            messagebox.showerror("Erro", f"Erro ao escanear arquivos:\n{e}")
    
    def add_sample_manually(self):
        """Adiciona amostra manualmente."""
        self.edit_sample_dialog()
    
    def edit_selected_sample(self):
        """Edita amostra selecionada."""
        selected = self.samples_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma amostra para editar")
            return
        
        item = selected[0]
        values = self.samples_tree.item(item, 'values')
        
        # Encontrar amostra nos dados
        sample_data = None
        for sample in self.samples_data:
            if sample['sample'] == values[0]:
                sample_data = sample
                break
        
        if sample_data:
            self.edit_sample_dialog(sample_data, item)
    
    def edit_sample_dialog(self, sample_data=None, tree_item=None):
        """Dialog para editar/adicionar amostra."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Amostra" if sample_data else "Adicionar Amostra")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Variáveis
        sample_name = tk.StringVar(value=sample_data['sample'] if sample_data else '')
        fastq1_path = tk.StringVar(value=sample_data['fastq_1'] if sample_data else '')
        fastq2_path = tk.StringVar(value=sample_data['fastq_2'] if sample_data else '')
        genome_size_var = tk.StringVar(value=sample_data['genome_size'] if sample_data else self.genome_size.get())
        
        # Layout
        ttk.Label(dialog, text="Nome da Amostra:").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=sample_name, width=50).pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(dialog, text="FASTQ R1:").pack(anchor=tk.W, padx=10, pady=(10,5))
        fastq1_frame = ttk.Frame(dialog)
        fastq1_frame.pack(fill=tk.X, padx=10, pady=2)
        ttk.Entry(fastq1_frame, textvariable=fastq1_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(fastq1_frame, text="...", width=3, 
                  command=lambda: self.select_fastq_file(fastq1_path)).pack(side=tk.RIGHT, padx=(5,0))
        
        ttk.Label(dialog, text="FASTQ R2 (opcional):").pack(anchor=tk.W, padx=10, pady=(10,5))
        fastq2_frame = ttk.Frame(dialog)
        fastq2_frame.pack(fill=tk.X, padx=10, pady=2)
        ttk.Entry(fastq2_frame, textvariable=fastq2_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(fastq2_frame, text="...", width=3,
                  command=lambda: self.select_fastq_file(fastq2_path)).pack(side=tk.RIGHT, padx=(5,0))
        
        ttk.Label(dialog, text="Tamanho do Genoma (bp):").pack(anchor=tk.W, padx=10, pady=(10,5))
        ttk.Entry(dialog, textvariable=genome_size_var, width=20).pack(anchor=tk.W, padx=10, pady=2)
        
        # Botões
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=20)
        
        def save_sample():
            if not sample_name.get() or not fastq1_path.get():
                messagebox.showerror("Erro", "Nome da amostra e FASTQ R1 são obrigatórios")
                return
            
            new_sample = {
                'sample': sample_name.get(),
                'fastq_1': fastq1_path.get(),
                'fastq_2': fastq2_path.get(),
                'genome_size': genome_size_var.get(),
                'status': 'Paired-end' if fastq2_path.get() else 'Single-end'
            }
            
            if tree_item:
                # Atualizar amostra existente
                self.samples_tree.item(tree_item, values=(
                    new_sample['sample'],
                    Path(new_sample['fastq_1']).name,
                    Path(new_sample['fastq_2']).name if new_sample['fastq_2'] else '',
                    new_sample['genome_size'],
                    new_sample['status']
                ))
                
                # Atualizar dados
                for i, sample in enumerate(self.samples_data):
                    if sample['sample'] == sample_data['sample']:
                        self.samples_data[i] = new_sample
                        break
            else:
                # Adicionar nova amostra
                self.samples_tree.insert("", "end", values=(
                    new_sample['sample'],
                    Path(new_sample['fastq_1']).name,
                    Path(new_sample['fastq_2']).name if new_sample['fastq_2'] else '',
                    new_sample['genome_size'],
                    new_sample['status']
                ))
                self.samples_data.append(new_sample)
            
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="Salvar", command=save_sample).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def select_fastq_file(self, var):
        """Seleciona arquivo FASTQ."""
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo FASTQ",
            filetypes=[
                ("FASTQ files", "*.fastq.gz *.fq.gz *.fastq *.fq"),
                ("All files", "*.*")
            ]
        )
        if filename:
            var.set(filename)
    
    def remove_selected_sample(self):
        """Remove amostra selecionada."""
        selected = self.samples_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma amostra para remover")
            return
        
        if messagebox.askyesno("Confirmar", "Remover amostra selecionada?"):
            item = selected[0]
            values = self.samples_tree.item(item, 'values')
            
            # Remover dos dados
            self.samples_data = [s for s in self.samples_data if s['sample'] != values[0]]
            
            # Remover da árvore
            self.samples_tree.delete(item)
    
    def export_samples_csv(self):
        """Exporta amostras para CSV."""
        if not self.samples_data:
            messagebox.showwarning("Aviso", "Nenhuma amostra para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exportar amostras",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.samples_data)
                df.to_csv(filename, index=False)
                self.log_message(f"Amostras exportadas para: {filename}")
                messagebox.showinfo("Sucesso", "Amostras exportadas com sucesso!")
            except Exception as e:
                self.log_message(f"Erro ao exportar: {e}", "ERROR")
                messagebox.showerror("Erro", f"Erro ao exportar:\n{e}")
    
    def generate_metadata(self):
        """Gera arquivo metadata.txt para Bactopia."""
        if not self.samples_data:
            messagebox.showerror("Erro", "Nenhuma amostra encontrada. Execute 'Escanear Arquivos FASTQ' primeiro.")
            return
        
        if not self.output_metadata.get():
            messagebox.showerror("Erro", "Selecione o arquivo de saída para metadata.txt")
            return
        
        try:
            metadata_lines = ["sample\tfastq_1\tfastq_2\tgenome_size"]
            
            for sample in self.samples_data:
                line = f"{sample['sample']}\t{sample['fastq_1']}\t{sample['fastq_2']}\t{sample['genome_size']}"
                metadata_lines.append(line)
            
            with open(self.output_metadata.get(), 'w') as f:
                f.write('\n'.join(metadata_lines))
            
            self.log_message(f"Metadata gerado: {self.output_metadata.get()}")
            messagebox.showinfo("Sucesso", "Arquivo metadata.txt gerado com sucesso!")
            
            # Executar Bactopia automaticamente se solicitado
            if self.auto_run_bactopia.get():
                self.run_bactopia()
                
        except Exception as e:
            self.log_message(f"Erro ao gerar metadata: {e}", "ERROR")
            messagebox.showerror("Erro", f"Erro ao gerar metadata:\n{e}")
    
    def generate_bactopia_command(self):
        """Gera comando Bactopia."""
        if not self.output_metadata.get():
            messagebox.showerror("Erro", "Gere o arquivo metadata.txt primeiro")
            return
        
        if not self.output_results.get():
            messagebox.showerror("Erro", "Selecione o diretório de resultados")
            return
        
        # Comando base
        if self.use_docker.get():
            cmd = ["nextflow", "run", "bactopia/bactopia"]
        else:
            cmd = ["nextflow", "run", "bactopia/bactopia"]
        
        # Parâmetros
        cmd.extend([
            "--samples", self.output_metadata.get(),
            "--outdir", self.output_results.get(),
            "--species", f'"{self.species.get()}"'
        ])
        
        # Recursos computacionais
        if self.cpu_cores.get():
            cmd.extend(["--cpus", self.cpu_cores.get()])
        
        if self.memory_gb.get():
            cmd.extend(["--max_memory", f"{self.memory_gb.get()}.GB"])
        
        # Docker/Singularity
        if self.use_docker.get():
            cmd.append("-profile docker")
        
        # Mostrar comando
        command_str = " ".join(cmd)
        self.command_text.delete(1.0, tk.END)
        self.command_text.insert(1.0, command_str)
        
        self.log_message("Comando Bactopia gerado")
    
    def run_bactopia(self):
        """Executa Bactopia em thread separada."""
        if not self.command_text.get(1.0, tk.END).strip():
            self.generate_bactopia_command()
        
        command = self.command_text.get(1.0, tk.END).strip()
        if not command:
            messagebox.showerror("Erro", "Comando Bactopia não foi gerado")
            return
        
        # Confirmar execução
        if not messagebox.askyesno("Confirmar", "Executar Bactopia?\n\nEste processo pode demorar várias horas."):
            return
        
        # Iniciar execução em thread
        self.progress_var.set("Executando Bactopia...")
        self.progress_bar.start()
        
        def run_command():
            try:
                self.log_message("Iniciando execução do Bactopia...")
                self.log_message(f"Comando: {command}")
                
                # Executar comando
                process = subprocess.Popen(
                    command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=Path(self.output_results.get()).parent
                )
                
                # Ler saída em tempo real
                for line in process.stdout:
                    self.root.after(0, lambda l=line: self.log_message(l.strip()))
                
                process.wait()
                
                if process.returncode == 0:
                    self.root.after(0, lambda: self.log_message("Bactopia executado com sucesso!", "SUCCESS"))
                    self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Bactopia executado com sucesso!"))
                else:
                    self.root.after(0, lambda: self.log_message(f"Bactopia falhou com código {process.returncode}", "ERROR"))
                    self.root.after(0, lambda: messagebox.showerror("Erro", f"Bactopia falhou com código {process.returncode}"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Erro na execução: {e}", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro na execução:\n{e}"))
            
            finally:
                self.root.after(0, self.stop_execution)
        
        # Iniciar thread
        self.execution_thread = threading.Thread(target=run_command, daemon=True)
        self.execution_thread.start()
    
    def stop_execution(self):
        """Para a execução e reseta interface."""
        self.progress_bar.stop()
        self.progress_var.set("Pronto para executar")
    
    def clear_form(self):
        """Limpa formulário."""
        self.fastq_dir.set("")
        self.output_metadata.set("")
        self.output_results.set("")
        self.samples_data = []
        
        # Limpar tabela
        for item in self.samples_tree.get_children():
            self.samples_tree.delete(item)
        
        # Limpar comando
        self.command_text.delete(1.0, tk.END)
        
        self.log_message("Formulário limpo")
    
    def clear_log(self):
        """Limpa o log."""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Salva o log em arquivo."""
        filename = filedialog.asksaveasfilename(
            title="Salvar log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"Log salvo em: {filename}")
                messagebox.showinfo("Sucesso", "Log salvo com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar log:\n{e}")

def main():
    """Função principal."""
    # Verificar dependências
    try:
        import pandas as pd
    except ImportError:
        print("Erro: pandas não está instalado!")
        print("Instale com: pip install pandas")
        sys.exit(1)
    
    # Verificar tkinter
    try:
        import tkinter as tk
    except ImportError:
        print("Erro: tkinter não está disponível!")
        print("No Ubuntu/Debian: sudo apt install python3-tk")
        sys.exit(1)
    
    # Criar e executar GUI
    root = tk.Tk()
    app = BactopiaGUI(root)
    
    # Configurar fechamento
    def on_closing():
        if hasattr(app, 'execution_thread') and app.execution_thread.is_alive():
            if messagebox.askokcancel("Fechar", "Execução em andamento. Deseja realmente fechar?"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Iniciar aplicação
    root.mainloop()

if __name__ == "__main__":
    main()
