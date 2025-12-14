# Metadata Extractor & Correlation Tool

## 🔍 Overview
The **Metadata Extractor & Correlation Tool** is a Python-based digital forensics utility designed to extract hidden metadata (EXIF data) from various file formats such as Images (JPEG, PNG) and Documents (PDF).

Beyond simple extraction, this tool features a **Correlation Engine** that analyzes the extracted data to find patterns—such as linking files created by the same camera device, modified by the same user, or captured at the same GPS location. This functionality is crucial for digital investigations and identifying the source of digital artifacts.

## ✨ Key Features
* **Multi-Format Support:** Extracts metadata from Images (`.jpg`, `.jpeg`, `.png`) and Documents (`.pdf`).
* **Deep Extraction:** Retrieves detailed attributes including:
    * **Device Info:** Camera Make, Model, Software/Firmware version.
    * **Timestamps:** Creation Date, Modification Date, Original Capture Time.
    * **GPS Coordinates:** Latitude, Longitude (if available).
    * **Author Info:** Creator tags in documents.
* **Correlation Logic:** Automatically compares metadata across multiple files to identify commonalities (e.g., "All these images were taken by an iPhone 13").
* **Bulk Processing:** Can process entire directories of files in one go.
* **Report Generation:** Exports findings into structured formats (CSV/TXT) for further analysis.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Libraries:**
    * `Pillow` (PIL): For image processing and EXIF extraction.
    * `PyPDF2`: For parsing PDF metadata.
    * `os`, `sys`: For file system navigation.
    * `csv`: For generating reports.

## ⚙️ How It Works
1.  **Input:** The user provides a file path or a folder directory containing the target files.
2.  **Extraction:** The tool iterates through each file, identifying its type, and uses the appropriate library to pull header and metadata information.
3.  **Normalization:** Raw data (tags) are converted into human-readable formats (e.g., converting GPS degrees to decimal coordinates).
4.  **Correlation:** The engine compares specific fields (like Camera Serial Number or Author Name) across the dataset to group related files.
5.  **Output:** A summary report is displayed or saved, highlighting the extracted data and any correlations found.

## 📦 Installation & Usage
1.  Clone this repository:
    ```bash
    git clone [https://github.com/SnehaNavakotii/Metadata-Forensics-Extractor.git](https://github.com/SnehaNavakotii/Metadata-Forensics-Extractor.git)
    ```
2.  Install dependencies:
    ```bash
    pip install Pillow PyPDF2
    ```
3.  Run the tool:
    ```bash
    python metadata_fina_pro.py
    ```

## ⚠️ Disclaimer
This tool is intended for **Educational Purposes and Digital Forensics Research**. The developer is not responsible for any misuse of this tool for unauthorized data collection.

---
**Developed by:** Sneha Latha Navakoti
**Role:** Cybersecurity Enthusiast & Python Developer
