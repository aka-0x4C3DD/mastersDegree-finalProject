<div align="center">
  
# ClinicalGPT Medical Assistant

<i>A sophisticated medical assistant application that combines large language models with trusted medical sources to provide accurate medical information and analysis.</i>

[![Python Version](https://img.shields.io/badge/python-3.12+-brightgreen.svg)](#prerequisites)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](#prerequisites)
[![License](https://img.shields.io/github/license/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)](LICENSE)
[![Issues](https://img.shields.io/github/issues/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)](../../issues)
[![Last Commit](https://img.shields.io/github/last-commit/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)](../../commits)
[![Code Size](https://img.shields.io/github/languages/code-size/aka-0x4C3DD/mastersDegree-finalProject.svg)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#-key-components)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](#-key-components)
[![Documentation](https://img.shields.io/badge/docs-up%20to%20date-brightgreen.svg)](#-api-reference)
[![Flask](https://img.shields.io/badge/flask-3.0+-blue.svg)](#prerequisites)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97-models%20on%20hub-yellow)](#-acknowledgments)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-contributing)

</div>

## 📑 Table of Contents

- [ClinicalGPT Medical Assistant](#clinicalgpt-medical-assistant)
  - [📑 Table of Contents](#-table-of-contents)
- [ClinicalGPT Medical Assistant](#clinicalgpt-medical-assistant-1)
  - [🌟 Features](#-features)
  - [🛠️ System Architecture](#️-system-architecture)
  - [🚀 Quick Start](#-quick-start)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Using the Application](#using-the-application)
  - [🔧 Configuration](#-configuration)
    - [Environment Variables](#environment-variables)
    - [Trusted Domains](#trusted-domains)
  - [🎯 Key Components](#-key-components)
    - [Server (`server/`)](#server-server)
    - [Utils (`utils/`)](#utils-utils)
  - [📝 API Reference](#-api-reference)
    - [Endpoints](#endpoints)
    - [Sample Request](#sample-request)
  - [🔐 Security](#-security)
  - [🤝 Contributing](#-contributing)
  - [📜 License](#-license)
  - [🙏 Acknowledgments](#-acknowledgments)

<div align="center">
  
# ClinicalGPT Medical Assistant

<i>A sophisticated medical assistant application that combines large language models with trusted medical sources to provide accurate medical information and analysis.</i>

![Python Version](https://img.shields.io/badge/python-3.12+-brightgreen.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)
![License](https://img.shields.io/github/license/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)
![Issues](https://img.shields.io/github/issues/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/aka-0x4C3DD/mastersDegree-finalProject?style=flat-square)
[![Code Size](https://img.shields.io/github/languages/code-size/aka-0x4C3DD/mastersDegree-finalProject.svg)]()
<img src="https://img.shields.io/badge/python-3.10-blue.svg">

</div>

<div align="center">
  
## 🌟 Features
</div>

- **Intelligent Medical Queries**: Get accurate responses to medical questions using state-of-the-art language models
- **Web Search Integration**: Automatic search and validation from trusted medical sources
- **File Analysis**: Process medical documents including:
  - Text files (.txt)
  - CSV data files
  - JSON documents
  - Medical images 
  - PDF documents 
- **Modern Web Interface**: Responsive design with real-time feedback
- **History Management**: Track and review past queries and analyses
- **Multi-Device Support**: Intelligent hardware acceleration on:
  - NVIDIA GPUs (CUDA)
  - Apple Silicon (MPS)
  - Intel NPUs
  - CPU fallback

<div align="center">
  
## 🛠️ System Architecture
</div>

```mermaid
graph TB
    subgraph Client Layer
        WUI[Web Interface]
    end

    subgraph Application Layer
        FS[Flask Server]
        RC[Request Controller]
        CM[Context Manager]
    end

    subgraph Model Layer
        LLM[Language Model]
        TOK[Tokenizer]
        INF[Inference Engine]
    end

    subgraph External Services
        WS[Web Scraper]
        MC[Mayo Clinic API]
        NIH[NIH Database]
        CDC[CDC Resources]
    end

    Client Layer --> Application Layer
    Application Layer --> Model Layer
    Application Layer --> External Services
```

<div align="center">
  
## 🚀 Quick Start
</div>

### Prerequisites

- Python 3.8 or higher
- PyTorch compatible hardware (GPU recommended)
- Internet connection for web search features

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd mastersDegree-finalProject
```

2. Run the setup script:
```bash
run.bat
```

The script will:
- Create a virtual environment
- Install dependencies
- Configure PyTorch for your hardware
- Start the server
- Open the web interface in your default browser

### Using the Application

Access the web interface at http://localhost:5000 in your browser. The interface will open automatically when using run.bat.

<div align="center">
  
## 🔧 Configuration
</div>

### Environment Variables

- `FLASK_DEBUG`: Enable/disable debug mode
- `PORT`: Server port (default: 5000)
- `MODEL_PATH`: Path to the model (default: HPAI-BSC/Llama3.1-Aloe-Beta-8B)
- `USE_INTEL_NPU`: Enable Intel NPU acceleration

### Trusted Domains

Edit `config.ini` to modify the list of trusted medical sources.

<div align="center">
  
## 🎯 Key Components
</div>

### Server (`server/`)
- Flask-based REST API
- Model management and inference
- File processing and analysis
- Web search integration

### Utils (`utils/`)
- Web scraping functionality
- File processing utilities
- Medical term detection
- Text analysis tools

<div align="center">
  
## 📝 API Reference
</div>

### Endpoints

- `GET /api/health`: Server health check
- `POST /api/query`: Process medical queries
- `POST /api/process-file`: Analyze medical files
- `GET /api/device-info`: Hardware acceleration info
- `GET /api/info`: API capabilities and status

### Sample Request

```json
POST /api/query
{
    "query": "What are the symptoms of type 2 diabetes?",
    "search_web": true
}
```

<div align="center">
  
## 🔐 Security
</div>

- Content validation and sanitization
- Trusted domain verification
- Input length restrictions
- Error handling and logging

<div align="center">
  
## 🤝 Contributing
</div>

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

<div align="center">
  
## 📜 License
</div>

This project is licensed under the CCv1 License - see the [LICENSE](LICENSE) file for details.

<div align="center">
  
## 🙏 Acknowledgments
</div>

- Hugging Face for model hosting
- Trusted medical sources (NIH, CDC, Mayo Clinic, etc.)
- Open-source medical research community

<!-- ## 📞 Support

For support and questions:
- Create an issue in the repository
- Check existing documentation
- Review closed issues for solutions

## 🔄 Updates and Maintenance

- Regular model updates
- Security patches
- Feature additions
- Bug fixes -->

<div align="center">
    made with ❤️ by SUMAN & GEET
</div>
