# azimuth-core

A fully local, privacy-focused personal finance management application with AI-powered transaction categorization and financial insights. All data stays on your machine - no cloud services required.

## Features

- **CSV Transaction Import**: Upload bank statements from any bank
- **AI-Powered Chat**: Local LLM for financial advice and natural language queries
- **Smart Categorization**: Automatic transaction categorization with manual override
- **Financial Analytics**: Spending trends, category breakdowns, and insights
- **Complete Privacy**: All data processing happens locally
- **Portable**: Run from any folder, perfect for USB drives
- **One-Click Start**: Simple scripts to launch everything

## System Requirements

### Minimum Requirements
- **RAM**: 8GB (4GB for system, 4GB for AI model)
- **Storage**: 5GB free space
- **CPU**: Modern quad-core processor (Intel i5/AMD Ryzen 5 or equivalent)
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)

### Recommended Requirements
- **RAM**: 16GB (for smoother AI performance)
- **Storage**: 10GB free space
- **CPU**: 8-core processor
- **SSD**: For faster database operations

### Ports Configuration
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- Ollama AI: http://localhost:11434


## Privacy & Security

### Data Privacy
- All data processing happens locally
- No data sent to external services
- No internet connection required after setup
- Full control over your financial information

### Security Notes
- Database is not encrypted by default
- Consider encrypting the entire `data/` folder for sensitive information
- JWT tokens are stored in browser localStorage
- Change the default JWT secret key in production

## Migration from Cloud Version

If you're migrating from the cloud-based version:

1. Export your data from the cloud version
2. Install the local version
3. Import your exported data through the web interface
4. Verify all data transferred correctly

## Support

### Getting Help
1. Check this README for common solutions
2. Review error messages in terminal/command prompt
3. Check logs in `backend/logs/` folder
4. Create an issue on GitHub with error details

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Vue.js, FastAPI, and SQLite
- Local AI powered by Ollama and Llama models
- Inspired by the need for privacy-focused financial tools