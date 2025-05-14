#!/bin/bash
# docaitool_wrapper.sh
# Wrapper script for PDF Manipulator with simplified command format

# Configuration paths
USER_CONFIG_DIR="$HOME/.config/pdf_manipulator"
CONFIG_FILE="$USER_CONFIG_DIR/config.yaml"
SETUP_SCRIPT="$(dirname "$0")/setup_config.sh"

# Text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
CYAN="\033[36m"
RESET="\033[0m"

# Function to print usage
print_usage() {
    echo -e "${BOLD}Usage:${RESET}"
    echo -e "  $(basename "$0") ${CYAN}<command>${RESET} ${CYAN}<input>${RESET} ${CYAN}[output]${RESET} ${CYAN}[options]${RESET}"
    echo ""
    echo -e "${BOLD}Commands:${RESET}"
    echo -e "  ${CYAN}process${RESET}    Process a PDF document (PDF -> PNG -> OCR/AI -> Markdown)"
    echo -e "  ${CYAN}render${RESET}     Render a PDF to PNG images"
    echo -e "  ${CYAN}ocr${RESET}        Extract text from an image using OCR"
    echo -e "  ${CYAN}transcribe${RESET} Transcribe an image using AI"
    echo -e "  ${CYAN}info${RESET}       Display information about a PDF"
    echo -e "  ${CYAN}config${RESET}     Configure the tool (runs setup wizard)"
    echo -e "  ${CYAN}ai${RESET}         List or manage AI backends"
    echo -e "  ${CYAN}help${RESET}       Show this help message"
    echo ""
    echo -e "${BOLD}Examples:${RESET}"
    echo -e "  $(basename "$0") process document.pdf output_dir"
    echo -e "  $(basename "$0") render document.pdf images_dir"
    echo -e "  $(basename "$0") ocr image.png"
    echo -e "  $(basename "$0") transcribe image.png"
    echo -e "  $(basename "$0") info document.pdf"
    echo -e "  $(basename "$0") config"
    echo -e "  $(basename "$0") ai"
    echo ""
    echo -e "Use '${CYAN}docaitool${RESET}' for advanced usage with more options."
}

# Check if we need to run the setup script
ensure_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${BOLD}No configuration found.${RESET}"
        echo "Running first-time setup..."
        
        if [ -f "$SETUP_SCRIPT" ]; then
            bash "$SETUP_SCRIPT"
        else
            echo -e "${RED}Error: Setup script not found at $SETUP_SCRIPT${RESET}"
            echo "Please run 'docaitool config --user' to create a configuration file."
            exit 1
        fi
    fi
}

# Not enough arguments
if [ $# -lt 1 ]; then
    print_usage
    exit 1
fi

# Parse command
COMMAND="$1"
shift

case "$COMMAND" in
    process)
        # Ensure we have input file
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: Missing input file${RESET}"
            echo "Usage: $(basename "$0") process <pdf_file> [output_dir]"
            exit 1
        fi
        
        # Get input file
        INPUT="$1"
        shift
        
        # Get output directory (optional)
        OUTPUT=""
        if [ $# -gt 0 ] && [[ ! "$1" == -* ]]; then
            OUTPUT="$1"
            shift
        fi
        
        # Ensure configuration exists
        ensure_config
        
        # Build docaitool command
        CMD="docaitool process \"$INPUT\""
        if [ -n "$OUTPUT" ]; then
            CMD="$CMD \"$OUTPUT\""
        fi
        
        # Add any remaining options
        if [ $# -gt 0 ]; then
            CMD="$CMD $*"
        fi
        
        # Execute the command
        eval "$CMD"
        ;;
        
    render)
        # Ensure we have input file
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: Missing input file${RESET}"
            echo "Usage: $(basename "$0") render <pdf_file> [output_dir]"
            exit 1
        fi
        
        # Get input file
        INPUT="$1"
        shift
        
        # Get output directory (optional)
        OUTPUT=""
        if [ $# -gt 0 ] && [[ ! "$1" == -* ]]; then
            OUTPUT="$1"
            shift
        fi
        
        # Ensure configuration exists
        ensure_config
        
        # Build docaitool command
        CMD="docaitool render \"$INPUT\""
        if [ -n "$OUTPUT" ]; then
            CMD="$CMD \"$OUTPUT\""
        fi
        
        # Add any remaining options
        if [ $# -gt 0 ]; then
            CMD="$CMD $*"
        fi
        
        # Execute the command
        eval "$CMD"
        ;;
        
    ocr)
        # Ensure we have input file
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: Missing input file${RESET}"
            echo "Usage: $(basename "$0") ocr <image_file> [output_file]"
            exit 1
        fi
        
        # Get input file
        INPUT="$1"
        shift
        
        # Get output file (optional)
        OUTPUT=""
        if [ $# -gt 0 ] && [[ ! "$1" == -* ]]; then
            OUTPUT="--output \"$1\""
            shift
        fi
        
        # Ensure configuration exists
        ensure_config
        
        # Build docaitool command
        CMD="docaitool ocr \"$INPUT\" $OUTPUT"
        
        # Add any remaining options
        if [ $# -gt 0 ]; then
            CMD="$CMD $*"
        fi
        
        # Execute the command
        eval "$CMD"
        ;;
        
    transcribe)
        # Ensure we have input file
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: Missing input file${RESET}"
            echo "Usage: $(basename "$0") transcribe <image_file> [output_file]"
            exit 1
        fi
        
        # Get input file
        INPUT="$1"
        shift
        
        # Get output file (optional)
        OUTPUT=""
        if [ $# -gt 0 ] && [[ ! "$1" == -* ]]; then
            OUTPUT="--output \"$1\""
            shift
        fi
        
        # Ensure configuration exists
        ensure_config
        
        # Build docaitool command
        CMD="docaitool transcribe \"$INPUT\" $OUTPUT"
        
        # Add any remaining options
        if [ $# -gt 0 ]; then
            CMD="$CMD $*"
        fi
        
        # Execute the command
        eval "$CMD"
        ;;
        
    info)
        # Ensure we have input file
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: Missing input file${RESET}"
            echo "Usage: $(basename "$0") info <pdf_file>"
            exit 1
        fi
        
        # Get input file
        INPUT="$1"
        shift
        
        # Build docaitool command
        CMD="docaitool info \"$INPUT\""
        
        # Add any remaining options
        if [ $# -gt 0 ]; then
            CMD="$CMD $*"
        fi
        
        # Execute the command
        eval "$CMD"
        ;;
        
    config)
        # Run the setup script
        if [ -f "$SETUP_SCRIPT" ]; then
            bash "$SETUP_SCRIPT"
        else
            echo -e "${RED}Warning: Setup script not found at $SETUP_SCRIPT${RESET}"
            echo "Running standard configuration command..."
            docaitool config --user --editor
        fi
        ;;
        
    ai)
        # List AI backends
        docaitool intelligence --list
        ;;
        
    help)
        print_usage
        ;;
        
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${RESET}"
        print_usage
        exit 1
        ;;
esac