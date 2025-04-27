# 🖥️ Bactopia Prepare GUI

A user-friendly graphical interface (GUI) to create the `metadata.txt` required by [Bactopia](https://bactopia.github.io/latest/), and optionally launch Bactopia automatically after preparing the samples.

---

## 📦 Features

- ✅ Select FASTQ files directory
- ✅ Auto-detect paired-end and single-end reads
- ✅ Set species (Klebsiella pneumoniae or Acinetobacter baumannii)
- ✅ Optional genome size per sample
- ✅ Recursive search option
- ✅ Auto-generate `metadata.txt` in the correct format
- ✅ Option to automatically run Bactopia (`nextflow run bactopia/bactopia`) after preparing
- ✅ User-friendly and intuitive interface
- ✅ Full support for Docker-based execution

---

## 🚀 Requirements

- Python 3.8+
- `tkinter` module installed  
  Install via: `sudo apt install python3-tk`
- Nextflow installed
- Docker installed and configured

---

## ⚙️ How to Use

1. Open the GUI.
2. Select the directory containing your `.fastq.gz` files.
3. Choose where to save the generated `metadata.txt`.
4. Select the species and genome size (if needed).
5. Generate the metadata.
6. Optionally, launch Bactopia automatically.

---

## 📥 Installation

Clone this repository:

```bash
git clone https://github.com/Felipeleii/bioinfo-scripts.git
