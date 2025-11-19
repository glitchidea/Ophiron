# Ophiron SDK

Official SDK for developing plugins for the Ophiron platform.

## 🚀 Installation

```bash
cd sdk
sudo make install
```

This will install the `ophiron-sdk` command globally to `/usr/local/bin/`.

### Alternative Installation (without sudo)

```bash
cd sdk
make build
export PATH="$PATH:$(pwd)/bin"
```

Or manually copy the binary:

```bash
cd sdk
make build
mkdir -p ~/.local/bin
cp bin/ophiron-sdk ~/.local/bin/
export PATH="$PATH:$HOME/.local/bin"
```

## 📦 Usage

### Create a New Plugin

```bash
ophiron-sdk create \
  --name "my-plugin" \
  --author "Your Name" \
  --description "My awesome plugin" \
  --category "security" \
  --email "your@email.com" \
  --developer-github "https://github.com/yourusername" \
  --project-github "https://github.com/yourusername/my-plugin" \
  --version "1.0.0" \
  --os-support "linux,darwin,windows"
```

### Add Language Support

```bash
cd your-plugin-directory
ophiron-sdk add-language --lang de
```

### Validate Plugin

```bash
cd your-plugin-directory
ophiron-sdk validate
```

## 📚 Documentation

For detailed plugin development guide, see:

- 🇹🇷 [Turkish Guide](../MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.tr.md)
- 🇬🇧 [English Guide](../MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.en.md)
- 🇩🇪 [German Guide](../MD-Document/SDK/SDK_PLUGIN_DEVELOPMENT.de.md)

## 🔒 License

This SDK is proprietary software. The source code is closed source.

Only the compiled binary (`bin/ophiron-sdk`) is distributed.

## 📞 Contact

- **GitHub**: https://github.com/glitchidea
- **Email**: info@glitchidea.com
- **Web**: https://glitchidea.com

---

Developed by GlitchIdea Team



