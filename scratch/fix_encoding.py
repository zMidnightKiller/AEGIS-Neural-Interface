import os
import re

def fix_mojibake(text):
    # Comprehensive replacement list for double-encoded UTF-8
    replacements = {
        # Specific word patterns
        'AUTÃƒâ€ NOMO': 'AUTÔNOMO',
        'EVOLUÃƒâ€¡ÃƒÆ’O': 'EVOLUÇÃO',
        'CRÃƒÂ TICA': 'CRÍTICA',
        'MÃƒÂ‰DIA': 'MÉDIA',
        'concluÃƒÂ­das': 'concluídas',
        'Ã°Å¸â€ Â´': '🔴',
        'Ã°Å¸â€ Âµ': '🔵',
        'Ã°Å¸Å¸Â': '🟠',
        'Ã°Å¸Å¸Â¡': '🟡',
        'Ã°Å¸Å¸Â¢': '🟢',
        'Ã°Å¸â€ Â': '🔴',
        'Ã¢â€°Â¥': '≥',
        
        # Emojis & Symbols
        'Ã¢â‚¬â€': '—',
        'Ã¢Å¡Â¡': '⚡',
        'Ã¢Å“â€¦': '✅',
        'Ã¢Å¡Âª': '⚪',
        'Ã¢Â Å’': '❌',
        'Ã¢Ë†Å¾': '∞',
        'Ã°Å¸Å’â‚¬': '🌀',
        'Ã°Å¸Å?â€ ': '🏆',
        'Ã¢â€ â€™': '→',
        'Ã¢â€ â€œ': '↓',
        'Ã¢â€ Â': '↑',
        'Ã‚Â§': '§',
        
        # Portuguese Accents
        'ÃƒÂ§': 'ç',
        'ÃƒÂ£': 'ã',
        'ÃƒÂµ': 'õ',
        'ÃƒÂ©': 'é',
        'ÃƒÂ³': 'ó',
        'ÃƒÂº': 'ú',
        'ÃƒÂ­': 'í',
        'ÃƒÂ¡': 'á',
        'ÃƒÂª': 'ê',
        'ÃƒÂ´': 'ô',
        'ÃƒÂ¢': 'â',
    }
    
    for old in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(old, replacements[old])
        
    # Final cleanup for remaining mojibake sequences
    text = text.replace('ÃƒÂ ', 'í')
    text = text.replace('Ã¢â€ â€œ', '↓')
    
    return text

def fix_file(path):
    if not os.path.exists(path):
        return
    print(f"Fixing {path}...")
    try:
        with open(path, 'rb') as f:
            content = f.read()
        
        text = content.decode('utf-8', errors='ignore')
        fixed = fix_mojibake(text)
        
        # Clean up double headers and excessive newlines
        fixed = re.sub(r'# PRD —  AEGIS AI: Product Requirements Document\s+# PRD —  AEGIS AI: Product Requirements Document', '# PRD —  AEGIS AI: Product Requirements Document', fixed)
        fixed = re.sub(r'\n{3,}', '\n\n', fixed)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)
    except Exception as e:
        print(f"Error fixing {path}: {e}")

if __name__ == "__main__":
    files = ['PRD.md', 'progress.txt', 'friction-log.md', 'README.md', 'AGENTE.md', 'prompt.md']
    for f in files:
        fix_file(f)
    print("Repair complete.")
