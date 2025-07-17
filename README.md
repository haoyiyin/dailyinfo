# 🚀 DailyInfo - AI-Powered News Monitoring System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-driven intelligent news collection, analysis, and push system designed to provide precise news information services for specific industries. The system integrates multiple news sources, uses AI intelligent evaluation to filter high-quality content, and automatically pushes it to collaboration platforms like Feishu.

## ✨ Key Features

### 📰 Multi-Source News Collection
- **RSS Sources**: A lots of professional RSS feeds covering authoritative institutions and industry media
- **MediaStack**: Global news API with health category support (optional)
- **News API**: English headline news with category filtering support (optional)

### 🤖 AI-Powered Analysis
- **Dual AI Protection**: Gemini (primary) + OpenRouter (backup) ensuring service stability
- **Intelligent Evaluation**: 10-point scoring based on industry relevance and content quality
- **Content Optimization**: AI automatic optimization and translation of news content
- **Retry Mechanism**: Multiple retries for each AI service, automatic fallback on failure

### 🔄 Smart Processing
- **Deduplication Algorithm**: Automatically identify and merge duplicate news based on title similarity
- **Content Enhancement**: Use FireCrawl to retrieve complete web content
- **Quality Control**: Automatically filter low-quality news to ensure valuable content delivery

### 📱 Multi-Platform Push
- **Feishu Integration**: Automatically push to Feishu group chats or bots
- **Anti-Duplication**: No duplicate news push within 24 hours
- **Formatting**: Structured message format including title, content, and original link

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  News Collection │    │   AI Analysis   │    │ Content Delivery│
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • RSS Feeds     │───▶│ • Gemini Eval   │───▶│ • Feishu Push   │
│ • MediaStack    │    │ • OpenRouter    │    │ • Deduplication │
│ • News API      │    │ • Content Opt   │    │ • Format Output │
│ • FireCrawl     │    │ • Translation   │    │ • Error Handle  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Requirements

- **Python**: 3.8 or higher
- **System**: Linux/macOS/Windows
- **Memory**: 2GB+ recommended
- **Network**: Access to external API services required

### Local Deployment

1. **Clone Repository**
```bash
git clone https://github.com/haoyiyin/dailyinfo.git
cd dailyinfo
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configuration Setup**
```bash
cp config.yaml.template config.yaml
cp rss_feeds.yaml.template rss_feeds.yaml
# Edit configuration files and fill in your API keys
```

4. **Run Program**
```bash
python main.py run
```

## ⚙️ Configuration

### Required Configuration

| Configuration | Description | How to Obtain |
|---------------|-------------|---------------|
| `webhook_url` | Feishu Bot Webhook URL | Feishu Group → Settings → Bots |
| `firecrawl_api_key` | FireCrawl API Key | [FireCrawl Website](https://firecrawl.dev) |
| `gemini_api_keys` | Gemini API Key List | [Google AI Studio](https://aistudio.google.com) |
| `openrouter_api_keys` | OpenRouter API Key List | [OpenRouter Website](https://openrouter.ai) |

### Optional Configuration

| Configuration | Description | Default |
|---------------|-------------|---------|
| `mediastack.api_key` | MediaStack API Key | Optional |
| `newsapi.api_key` | News API Key | Optional |
| `min_relevance_score` | Minimum Relevance Score | 8.0 |
| `max_send_limit` | Maximum Push Count | 10 |
| `time_window_hours` | News Time Window (hours) | 24 |

### API Key Acquisition

1. **Gemini API**: [Google AI Studio](https://aistudio.google.com) → Get API Key
2. **OpenRouter API**: [OpenRouter Website](https://openrouter.ai) → Register → API Keys
3. **FireCrawl API**: [FireCrawl Website](https://firecrawl.dev) → Register → API Keys
4. **MediaStack API**: [MediaStack Website](https://mediastack.com) → Free Registration (Optional)
5. **News API**: [NewsAPI Website](https://newsapi.org) → Free Registration (Optional)

### Industry Customization

This project is configured for the renewable energy industry by default. You can customize it as needed:

1. **Modify AI Evaluation Prompts**: Edit `ai_settings.prompts.evaluation_prompt` in `config.yaml`
2. **Update RSS Sources**: Edit `rss_feeds.yaml` to add RSS sources related to your industry
3. **Adjust Scoring Threshold**: Adjust the `min_relevance_score` parameter as needed

## 🔧 Usage

### Command Line Options

```bash
# Execute news processing task immediately
python main.py run

# Start scheduled task mode (runs daily at 06:00)
python main.py schedule

# View system configuration status
python main.py status

# Display help information
python main.py help
```

### Scheduled Execution

#### Method 1: Built-in Scheduler (Recommended)
```bash
# Start scheduled task mode, runs automatically daily at 06:00
python main.py schedule
```

#### Method 2: System Cron
```bash
# Edit crontab
crontab -e

# Run daily at 6 AM
0 6 * * * cd /path/to/dailyinfo && python main.py run
```

### Monitoring and Debugging

```bash
# View system status
python main.py status

# Execute immediately for testing
python main.py run

# View runtime logs
tail -f logs/dailyinfo_*.log

# View sent messages
cat logs/sent_messages.json
```

## 📁 Project Structure

```
dailyinfo/
├── LICENSE                    # MIT License
├── README.md                  # Project Documentation
├── config.yaml.template      # Configuration Template
├── rss_feeds.yaml.template   # RSS Sources Template
├── main.py                   # Main Program Entry
├── requirements.txt          # Python Dependencies
├── logs/                     # Log Directory
└── utils/                    # Utility Modules
    ├── ai_analyzer.py        # AI Analyzer
    ├── config_manager.py     # Configuration Manager
    ├── feishu.py            # Feishu Push
    ├── mediastack_fetcher.py # MediaStack Fetcher
    ├── news_deduplicator.py  # News Deduplicator
    ├── news_processor.py     # News Processor
    ├── news_publisher.py     # News Publisher
    ├── newsapi_fetcher.py    # News API Fetcher
    ├── rss_fetcher.py        # RSS Fetcher
    ├── scheduler.py          # Task Scheduler
    ├── workflow_manager.py   # Workflow Manager
    └── zyte_client.py        # Zyte Client
```

## 🚀 Production Deployment

### Method 1: Integrated Commands (Recommended)

```bash
# Start background service
python main.py start

# Check service status
python main.py daemon status

# Stop service
python main.py stop

# Restart service
python main.py daemon restart

# View real-time logs
tail -f logs/daemon.log
```

### Method 2: Systemd Service (Linux Servers)

```bash
# 1. Edit service file
sudo cp dailyinfo.service /etc/systemd/system/
sudo nano /etc/systemd/system/dailyinfo.service
# Modify paths and user information

# 2. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable dailyinfo
sudo systemctl start dailyinfo

# 3. Check service status
sudo systemctl status dailyinfo

# 4. View logs
sudo journalctl -u dailyinfo -f
```

### Method 3: Screen/Tmux

```bash
# Using screen
screen -S dailyinfo
python main.py schedule
# Press Ctrl+A, D to detach

# Reconnect
screen -r dailyinfo

# Using tmux
tmux new-session -d -s dailyinfo 'python main.py schedule'
tmux attach-session -t dailyinfo

# Alternative: Use built-in daemon mode
python main.py schedule --daemon
```

### Monitoring and Debugging

```bash
# Check system status
python main.py status

# Run immediate test
python main.py run

# View running logs
tail -f logs/dailyinfo_*.log

# View sent messages
cat logs/sent_messages.json
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FireCrawl](https://firecrawl.dev) for web content extraction
- [Google Gemini](https://ai.google.dev) for AI analysis
- [OpenRouter](https://openrouter.ai) for AI service integration
- All RSS feed providers for news sources

## 📞 Support

If you encounter any issues or have questions, please:

1. Check the [Issues](https://github.com/haoyiyin/dailyinfo/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the issue

---

**⭐ If this project helps you, please give it a star!**
