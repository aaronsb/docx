#!/bin/bash
# setup_config.sh
# Interactive configuration script for the PDF Manipulator tool

# Text formatting
BOLD="\033[1m"
GREEN="\033[32m"
BLUE="\033[34m"
CYAN="\033[36m"
RESET="\033[0m"

# Configuration paths
USER_CONFIG_DIR="$HOME/.config/pdf_manipulator"
CONFIG_FILE="$USER_CONFIG_DIR/config.yaml"

# Create config directories if they don't exist
mkdir -p "$USER_CONFIG_DIR"

# Welcome message
clear
echo -e "${BOLD}${BLUE}PDF Manipulator Configuration Wizard${RESET}"
echo -e "${CYAN}This script will help you set up your PDF Manipulator configuration.${RESET}"
echo "It will create a configuration file at: $CONFIG_FILE"
echo ""

# Check if config already exists
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${BOLD}Existing configuration detected.${RESET}"
    read -p "Do you want to (r)econfigure, (e)dit current config, or (q)uit? [r/e/q]: " choice
    case "$choice" in
        r|R) ;;  # Continue with new config
        e|E) 
            # Open in preferred editor
            if [ -n "$EDITOR" ]; then
                $EDITOR "$CONFIG_FILE"
            elif command -v nano &> /dev/null; then
                nano "$CONFIG_FILE"
            elif command -v vim &> /dev/null; then
                vim "$CONFIG_FILE"
            else
                echo "No editor found. Please edit $CONFIG_FILE manually."
            fi
            echo -e "${GREEN}Configuration updated. Use 'docaitool' to process documents.${RESET}"
            exit 0
            ;;
        *) 
            echo "Exiting without changes."
            exit 0
            ;;
    esac
fi

# Helper function for multi-line input with a default value
multi_line_input() {
    local prompt="$1"
    local default="$2"
    local variable_name="$3"
    
    echo -e "${BOLD}$prompt${RESET}"
    if [ -n "$default" ]; then
        echo -e "Default: $default"
        echo -e "Press Enter to use default or type a new value."
    fi
    
    # Store the old IFS
    OLDIFS=$IFS
    # Set IFS to empty to preserve whitespace
    IFS=''
    
    # Display the prompt and read input
    read -p "> " input
    
    # Restore IFS
    IFS=$OLDIFS
    
    # Use default if input is empty
    if [ -z "$input" ]; then
        eval "$variable_name=\"$default\""
    else
        eval "$variable_name=\"$input\""
    fi
}

# Simple input with default
input_with_default() {
    local prompt="$1"
    local default="$2"
    local variable_name="$3"
    
    if [ -n "$default" ]; then
        read -p "${BOLD}$prompt${RESET} [$default]: " input
        if [ -z "$input" ]; then
            eval "$variable_name=\"$default\""
        else
            eval "$variable_name=\"$input\""
        fi
    else
        read -p "${BOLD}$prompt${RESET}: " input
        eval "$variable_name=\"$input\""
    fi
}

# Yes/no prompt
yes_no_prompt() {
    local prompt="$1"
    local default="$2"
    local variable_name="$3"
    
    local yn_prompt
    if [ "$default" = "y" ]; then
        yn_prompt="[Y/n]"
    else
        yn_prompt="[y/N]"
    fi
    
    while true; do
        read -p "${BOLD}$prompt${RESET} $yn_prompt: " yn
        case $yn in
            [Yy]*) eval "$variable_name=true"; break ;;
            [Nn]*) eval "$variable_name=false"; break ;;
            "") 
                if [ "$default" = "y" ]; then
                    eval "$variable_name=true"
                else
                    eval "$variable_name=false"
                fi
                break
                ;;
            *) echo "Please answer yes or no." ;;
        esac
    done
}

# Function to detect Ollama
detect_ollama() {
    # Check if Ollama is installed and reachable
    if curl -s --head --fail "http://localhost:11434/api/tags" > /dev/null 2>&1; then
        echo "Ollama detected at http://localhost:11434"
        DEFAULT_BACKEND="ollama"
        return 0
    else
        return 1
    fi
}

# Function to detect llama.cpp
detect_llama_cpp() {
    # Check for common locations of llama.cpp builds
    for location in \
        "$HOME/llama.cpp" \
        "$HOME/Projects/llama.cpp" \
        "$HOME/Projects/ai/llama.cpp" \
        "$HOME/Projects/ai/llama/llama.cpp" \
        "/usr/local/src/llama.cpp" 
    do
        if [ -f "$location/main" ] || [ -f "$location/server" ]; then
            echo "Potential llama.cpp installation found at: $location"
            LLAMA_CPP_PATH="$location"
            if [ -f "$location/server" ]; then
                echo "llama.cpp server detected!"
                DEFAULT_BACKEND="llama_cpp_http"
            else
                DEFAULT_BACKEND="llama_cpp"
            fi
            return 0
        fi
    done
    return 1
}

# General settings
echo -e "\n${BOLD}${BLUE}General Settings${RESET}"
input_with_default "Default output directory" "output" OUTPUT_DIR

# Rendering settings
echo -e "\n${BOLD}${BLUE}Rendering Settings${RESET}"
input_with_default "Resolution in DPI" "300" DPI
yes_no_prompt "Include alpha channel (transparency)" "n" ALPHA
input_with_default "Zoom factor" "1.0" ZOOM

# OCR settings
echo -e "\n${BOLD}${BLUE}OCR Settings${RESET}"
input_with_default "OCR language" "eng" OCR_LANG

# Try to detect Tesseract installation
TESSERACT_CMD=""
TESSDATA_DIR=""
if command -v tesseract &> /dev/null; then
    TESSERACT_CMD=$(command -v tesseract)
    echo "Tesseract detected at: $TESSERACT_CMD"
    
    # Try to find tessdata directory
    if [ -d "/usr/share/tesseract-ocr/4.00/tessdata" ]; then
        TESSDATA_DIR="/usr/share/tesseract-ocr/4.00/tessdata"
    elif [ -d "/usr/share/tessdata" ]; then
        TESSDATA_DIR="/usr/share/tessdata"
    elif [ -d "/usr/local/share/tessdata" ]; then
        TESSDATA_DIR="/usr/local/share/tessdata"
    fi
    
    if [ -n "$TESSDATA_DIR" ]; then
        echo "Tessdata directory detected at: $TESSDATA_DIR"
    fi
fi

# Let user override detected Tesseract settings
input_with_default "Tesseract executable" "$TESSERACT_CMD" TESSERACT_CMD
input_with_default "Tessdata directory" "$TESSDATA_DIR" TESSDATA_DIR

# AI backend settings
echo -e "\n${BOLD}${BLUE}AI Backend Settings${RESET}"

# Try to detect potential backends
DEFAULT_BACKEND="ollama"  # Default if nothing else detected

if ! detect_ollama; then
    detect_llama_cpp
fi

# Ask user which backend to use
echo "Available backends: ollama, llama_cpp, llama_cpp_http"
input_with_default "Default AI backend" "$DEFAULT_BACKEND" BACKEND

# Backend-specific settings
echo -e "\n${BOLD}${BLUE}Backend Configuration${RESET}"

# Ollama settings
echo -e "\n${CYAN}Ollama Settings${RESET}"
input_with_default "Ollama model" "llava:latest" OLLAMA_MODEL
input_with_default "Ollama API URL" "http://localhost:11434" OLLAMA_URL
input_with_default "Ollama timeout (seconds)" "120" OLLAMA_TIMEOUT

# Llama.cpp settings
echo -e "\n${CYAN}llama.cpp Settings${RESET}"
input_with_default "Model path (GGUF file)" "" LLAMA_MODEL_PATH
input_with_default "Context size (tokens)" "2048" LLAMA_CTX
input_with_default "GPU layers (-1 for all)" "-1" LLAMA_GPU_LAYERS

# Llama.cpp HTTP settings
echo -e "\n${CYAN}llama.cpp HTTP Server Settings${RESET}"
input_with_default "Server URL" "http://localhost:8080" LLAMA_HTTP_URL
input_with_default "Max tokens to predict" "2048" LLAMA_PREDICT
input_with_default "Temperature" "0.1" LLAMA_TEMP

# Processing settings
echo -e "\n${BOLD}${BLUE}Processing Settings${RESET}"
multi_line_input "Default prompt for image transcription" "Transcribe all text in this document image to markdown format. Preserve layout and formatting as best as possible." PROMPT
yes_no_prompt "Use OCR as fallback for AI" "y" OCR_FALLBACK

# Generate the config file
cat > "$CONFIG_FILE" << EOF
# PDF Manipulator Configuration
# Generated by setup script on $(date)

# General settings
general:
  output_dir: "$OUTPUT_DIR"
  
  # Logging configuration
  logging:
    level: "INFO"
    file: null

# PDF rendering settings
rendering:
  dpi: $DPI
  alpha: $ALPHA
  zoom: $ZOOM

# OCR settings
ocr:
  language: "$OCR_LANG"
  tessdata_dir: ${TESSDATA_DIR:+\"$TESSDATA_DIR\"}
  tesseract_cmd: ${TESSERACT_CMD:+\"$TESSERACT_CMD\"}

# AI intelligence configuration
intelligence:
  default_backend: "$BACKEND"
  
  # Configuration for different intelligence backends
  backends:
    # Ollama API backend
    ollama:
      model: "$OLLAMA_MODEL"
      base_url: "$OLLAMA_URL"
      timeout: $OLLAMA_TIMEOUT
    
    # Direct llama.cpp integration via Python bindings
    llama_cpp:
      model_path: ${LLAMA_MODEL_PATH:+\"$LLAMA_MODEL_PATH\"}
      n_ctx: $LLAMA_CTX
      n_gpu_layers: $LLAMA_GPU_LAYERS
    
    # llama.cpp HTTP server backend
    llama_cpp_http:
      base_url: "$LLAMA_HTTP_URL"
      model: null
      timeout: 120
      n_predict: $LLAMA_PREDICT
      temperature: $LLAMA_TEMP

# Document processing settings
processing:
  default_prompt: "$PROMPT"
  use_ocr_fallback: $OCR_FALLBACK
EOF

# Make script executable
chmod +x "$CONFIG_FILE"

echo -e "\n${GREEN}${BOLD}Configuration complete!${RESET}"
echo -e "Configuration file created at: ${CYAN}$CONFIG_FILE${RESET}"
echo -e "\n${BOLD}Quick Usage:${RESET}"
echo -e "  ${CYAN}docaitool process document.pdf output/${RESET}"
echo -e "  ${CYAN}docaitool transcribe image.png${RESET}"
echo -e "  ${CYAN}docaitool config --list${RESET} (to see available configurations)"
echo -e "  ${CYAN}docaitool intelligence --list${RESET} (to see available AI backends)"
echo -e "\n${BOLD}To change configuration:${RESET}"
echo -e "  ${CYAN}$(basename "$0")${RESET} or ${CYAN}docaitool config --user --editor${RESET}"
echo -e "\nHappy document processing!"