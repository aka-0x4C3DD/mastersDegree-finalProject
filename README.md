# ClinicalGPT Medical Assistant

A sophisticated medical assistant application that combines large language models with trusted medical sources to provide accurate medical information and analysis.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)

## 🌟 Features

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

## 🛠️ System Architecture

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

## 🚀 Quick Start

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

## 🔧 Configuration

### Environment Variables

- `FLASK_DEBUG`: Enable/disable debug mode
- `PORT`: Server port (default: 5000)
- `MODEL_PATH`: Path to the model (default: HPAI-BSC/Llama3.1-Aloe-Beta-8B)
- `USE_INTEL_NPU`: Enable Intel NPU acceleration

### Trusted Domains

Edit `config.ini` to modify the list of trusted medical sources.

## 🎯 Key Components

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

## 📝 API Reference

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

## 🔐 Security

- Content validation and sanitization
- Trusted domain verification
- Input length restrictions
- Error handling and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Hugging Face for model hosting
- Trusted medical sources (NIH, CDC, Mayo Clinic, etc.)
- Open-source medical research community

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check existing documentation
- Review closed issues for solutions

## 🔄 Updates and Maintenance

- Regular model updates
- Security patches
- Feature additions
- Bug fixes