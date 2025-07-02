#!/usr/bin/env python3
"""
2048 AI Game Launcher
Simple launcher script that checks dependencies and starts the AI-enhanced game
"""

import sys
import subprocess
import importlib.util

def check_dependency(module_name, package_name=None):
    """Check if a dependency is installed"""
    if package_name is None:
        package_name = module_name
    
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def install_dependency(package_name):
    """Install a dependency using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🎮 2048 AI Game Launcher")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Error: Python 3.6 or higher is required.")
        print("   Current version:", sys.version)
        input("Press Enter to exit...")
        return
    
    print("✓ Python version check passed")
    
    # Check dependencies
    dependencies = [
        ("PySide6", "PySide6>=6.5.0"),
        ("ollama", "ollama>=0.1.0"),
        ("requests", "requests>=2.31.0")
    ]
    
    missing_deps = []
    
    for module, package in dependencies:
        if check_dependency(module):
            print(f"✓ {module} is installed")
        else:
            print(f"❌ {module} is missing")
            missing_deps.append(package)
    
    # Install missing dependencies
    if missing_deps:
        print(f"\n📦 Installing missing dependencies...")
        
        for package in missing_deps:
            print(f"Installing {package}...")
            if install_dependency(package):
                print(f"✓ {package} installed successfully")
            else:
                print(f"❌ Failed to install {package}")
                print(f"   Please install manually: pip install {package}")
                input("Press Enter to exit...")
                return
    
    # Check Ollama availability
    try:
        import ollama
        # Try to list models to check if Ollama server is running
        try:
            models = ollama.list()
            if models and 'models' in models and len(models['models']) > 0:
                print("✓ Ollama server is running with models")
            else:
                print("⚠️  Ollama server is running but no models found")
                print("   You can still play in human mode")
                print("   To use AI features, install models like: ollama pull llama2")
        except Exception:
            print("⚠️  Ollama server not running or not accessible")
            print("   You can still play in human mode")
            print("   To use AI features, start Ollama server and install models")
    except ImportError:
        print("⚠️  Ollama module not available")
    
    print("\n🚀 Starting 2048 AI Game...")
    print("   - Use arrow keys or WASD to play manually")
    print("   - Click 'Start AI' to let AI play")
    print("   - View statistics to track your games")
    print("   - Press ESC to exit")
    
    try:
        # Import and run the game
        from ai_game import main as game_main
        game_main()
    except ImportError as e:
        print(f"❌ Error importing game: {e}")
        print("   Please make sure ai_game.py is in the same directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"❌ Error starting game: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 