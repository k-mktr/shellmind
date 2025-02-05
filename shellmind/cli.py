"""
ShellMind CLI Interface
"""
import argparse
import os
import subprocess
from pathlib import Path
from configparser import ConfigParser
from .ai_handler import generate_command
from .utils import get_os_type

HISTORY_FILE = Path.home() / ".config" / "shellmind" / "history.log"

def main():
    # Load config
    config = ConfigParser()
    config.read(os.path.expanduser('~/.config/shellmind/config.ini'))
    default_base_url = config.get('default', 'base_url', fallback=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'))
    default_model = config.get('default', 'model', fallback='gpt-4o-mini')
    default_system_type = config.get('default', 'system_type', fallback=None)
    
    parser = argparse.ArgumentParser(
        description="ShellMind - AI-powered terminal assistant",
        epilog="Example: shellmind -a 'How to update Fedora system?'",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-a', '--ask', help="Natural language query about terminal commands")
    parser.add_argument('-e', '--explain', action='store_true', help="Show detailed command explanations")
    parser.add_argument('-m', '--model', default=default_model, help="Model to use (default: from config or gpt-4o-mini)")
    parser.add_argument('-b', '--base-url', default=default_base_url,
                        help="""API base URL (default: OpenAI) - use http://localhost:11434/v1 for Ollama
Examples:
  - OpenAI: https://api.openai.com/v1
  - Ollama: http://localhost:11434/v1""")
    parser.add_argument('-k', '--api-key', default=os.getenv('OPENAI_API_KEY', None),
                        help="API key (default: from OPENAI_API_KEY env var)")
    parser.add_argument('-i', '--interactive', action='store_true', help="Start interactive mode")
    parser.add_argument('-x', '--execute', action='store_true', help="Execute the generated command (with confirmation)")
    parser.add_argument('-H', '--history', action='store_true', help="Show command history")
    
    args = parser.parse_args()
    
    # Show history if requested
    if args.history:
        show_history()
        return
    
    # Validate API key first
    if args.base_url == 'https://api.openai.com/v1' and not args.api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Get system context
    os_type = default_system_type if default_system_type else get_os_type()
    
    if args.interactive:
        start_interactive_mode(os_type, args)
    elif args.ask:
        response = generate_command(
            query=args.ask,
            os_type=os_type,
            explain=args.explain,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key
        )
        
        # Display results
        command = response.get('command', 'No command generated')
        explanation = response.get('explanation', [])
        warning = response.get('warning', '')
        
        print(f"\nCommand: {command}")
        if explanation:
            print("\nExplanation:")
            for line in explanation:
                print(f"  - {line}")
        if warning:
            print(f"\n⚠️  Warning: {warning}")
        print()
        
        # Execute the command if requested
        if args.execute:
            execute_command(command, warning)
        
        # Save to history
        save_to_history(args.ask, command)
    else:
        parser.print_help()

def save_to_history(query: str, command: str):
    """Save the query and command to the history file."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "a") as f:
        f.write(f"Query: {query}\nCommand: {command}\n\n")

def show_history():
    """Display the command history."""
    if not HISTORY_FILE.exists():
        print("No history found.")
        return
    
    with open(HISTORY_FILE, "r") as f:
        content = f.read()
        if not content.strip():
            print("No history found.")
            return
        
        print(f"\nCommand History:\n")
        print(f.read())

def execute_command(command: str, warning: str = None):
    """Execute the generated command with safety checks."""
    if warning:
        print(f"\n⚠️  Warning: {warning}")
        confirmation = input("Are you sure you want to execute this command? (y/n): ").strip().lower()
        if confirmation != 'y':
            print("Command execution canceled.")
            return
    
    print(f"\nExecuting: {command}")
    try:
        # Execute the command and stream output directly to the terminal
        subprocess.call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed with exit code {e.returncode}")
        diagnose_error(command, str(e))
    except Exception as e:
        print(f"❌ Error executing command: {str(e)}")

def diagnose_error(command: str, error_output: str):
    """Diagnose and suggest fixes for command errors."""
    print("\nDiagnosing error...")
    try:
        response = generate_command(
            query=f"The command '{command}' failed with this error: {error_output}. What went wrong and how can I fix it?",
            os_type=get_os_type(),
            explain=True
        )
        
        print(f"\nDiagnosis: {response['command']}")
        if response['explanation']:
            print("\nExplanation:")
            for line in response['explanation']:
                print(f"  - {line}")
        if response['warning']:
            print(f"\n⚠️  Warning: {response['warning']}")
    except Exception as e:
        print(f"❌ Error during diagnosis: {str(e)}")

def start_interactive_mode(os_type: str, args):
    """Start interactive mode for continuous queries."""
    print("ShellMind Interactive Mode (type 'exit' or 'quit' to end)")
    while True:
        try:
            query = input("\n> ")
            if query.lower() in ('exit', 'quit'):
                break
            if not query.strip():
                print("❌ Error: Query cannot be empty")
                continue
            
            response = generate_command(
                query=query,
                os_type=os_type,
                explain=args.explain,
                model=args.model,
                base_url=args.base_url,
                api_key=args.api_key
            )
            
            print(f"\nCommand: {response['command']}")
            if response['explanation']:
                print("\nExplanation:")
                for line in response['explanation']:
                    print(f"  - {line}")
            if response['warning']:
                print(f"\n⚠️  Warning: {response['warning']}")
            
            # Execute the command if in interactive mode with --execute
            if args.execute:
                execute_command(response['command'], response['warning'])
            
            # Save to history
            save_to_history(query, response['command'])
        except KeyboardInterrupt:
            print("\nExiting interactive mode...")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
