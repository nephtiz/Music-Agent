<p align="center">
  <a href="https://github.com/nephtiz/Audio-Steganography-Discord-Bot">
    <img src= "https://i.imgur.com/y0zsgQl.gif"
      alt="agent"
      width="175"
      height="175"
      decoding="async"
      fetchpriority="high"
    />
  </a>
</p>

# <p align="center">Audio Steganography Discord Bot</p>

<div align="center">

A Discord bot that conceals secret text messages within WAV audio files using LSB steganography. Seamlessly integrated with Discord, allowing message embedding and extraction directly through the platform.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/python-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-blue.svg)](https://discordpy.readthedocs.io/en/stable/)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Project Structure](#-project-structure) • [Security Considerations](#-security-considerations) • [Contributing](#-contributing)

</div>

## 🌟 Features

- **Discord Integration:**
  - Encrypt messages using slash command (`/encrypt`)
  - Decrypt messages via context menu (right-click on message)
  - Full support for both server channels and direct messages via user install
- **Security Features:**
  - Optional password protection for sensitive messages
  - Customizable user exceptions to bypass password requirements
  - Unique binary signature verification
- **Robust Audio Processing:**
  - Automatic audio resampling for format consistency
  - Supports looping audio if needed
  - Preserves audio quality while maintaining message integrity
- **Error Handling:**
  - Comprehensive input validation
  - User-friendly error messages
  - Graceful handling of common issues (unsupported formats, DM restrictions, etc.)

## 🚀 Installation

### Prerequisites

- Python
- Discord Bot Token
- Basic understanding of Discord bot deployment

### Setup Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/nephtiz/Audio-Steganography-Discord-Bot.git
   cd Audio-Steganography-Discord-Bot
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Rename `.env.example` to `.env` and Update the following variables:
   ```env
   TOKEN=your_discord_bot_token
   UPDATES=channel_id_for_updates
   SIGNATURE=your_binary_signature
   ```

   **Note:** The SIGNATURE must be a binary string (only '0's and '1's). While our test example uses 16 bits, you can choose any fixed length for your implementation.

## 💻 Usage

### Starting the Bot

```bash
python main.py
```
Upon successful startup, you'll see "Logged in and Ready!" in the terminal.

### Commands

1. **Encrypt Message:**
   ```
   /encrypt [input(required):] [audio(optional):] [password(optional):] [exceptions(optional):]
   ```
   - `input`: Text to hide
   - `audio`: WAV file to embed the message in (default.wav is used if none is provided)
   - `password`: Optional protection (users need this to decrypt)
   - `exceptions`: Users who can decrypt without password

2. **Decrypt Message:**
   - Right-click on a message containing an audio file
   - Select "Decrypt Message" from the context menu
   - Enter password if required

**Note:** Currently, the bot uses LSB steganography to directly hide messages in audio files. While the commands are named "encrypt" and "decrypt" for simplicity, true encryption will possibly be added in a future update.

## 📁 Project Structure

```
project/
├── audio/
│   ├── __init__.py
│   └── processing.py
├── bot/
│   ├── __init__.py
│   └── commands.py
├── steganography/
│   ├── __init__.py
│   └── lsb.py
├── main.py
├── default.wav
├── .env.example
├── requirements.txt
└── README.md
```

## 🔒 Security Considerations

While the current implementation provides basic security through LSB steganography and password protection, users should be aware of the following:

- LSB steganography is not encryption - it only hides data
- Messages can be detected by analyzing bit patterns
- Consider implementing additional encryption for sensitive data

### Planned Enhancements

- AES encryption layer for message content
- Improved password hashing
- Additional security features to protect against unauthorized access and reverse engineering

## 🤝 Contributing

Contributions are welcome! Fork the repo and open a Pull Request with your changes.

### Guidelines

- Write clear, descriptive PR titles
- Test your changes thoroughly
- Update documentation as needed
- Ensure compatibility with existing features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/nephtiz/Audio-Steganography-Discord-Bot/blob/main/LICENSE) file for details.

<p align="center">✦・―――――――・✦</p>
