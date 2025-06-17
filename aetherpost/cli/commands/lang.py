"""Language and localization commands."""

import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import os

console = Console()
lang_app = typer.Typer()


@lang_app.command()
def list():
    """List available languages."""
    
    console.print(Panel(
        "[bold blue]🌍 Available Languages[/bold blue]",
        border_style="blue"
    ))
    
    from ...core.i18n import get_available_languages, get_language_info, CURRENT_LANGUAGE
    
    available_langs = get_available_languages()
    lang_info = get_language_info()
    
    lang_table = Table(title="Supported Languages")
    lang_table.add_column("Code", style="cyan")
    lang_table.add_column("Language", style="white")
    lang_table.add_column("Status", style="green")
    
    for lang_code in available_langs:
        lang_name = lang_info.get(lang_code, lang_code.upper())
        status = "✅ Current" if lang_code == CURRENT_LANGUAGE else "Available"
        lang_table.add_row(lang_code, lang_name, status)
    
    console.print(lang_table)
    
    console.print(f"\n[bold]Current language:[/bold] {CURRENT_LANGUAGE}")
    console.print("\n[bold]Usage:[/bold]")
    console.print("• [cyan]aetherpost lang set <code>[/cyan] - Set language")
    console.print("• [cyan]export AUTOPROMO_LANG=ja[/cyan] - Set via environment variable")
    console.print("• [cyan]aetherpost lang status[/cyan] - Show current language info")


@lang_app.command()
def set(
    language: str = typer.Argument(..., help="Language code (e.g., en, ja, es)")
):
    """Set the current language."""
    
    from ...core.i18n import get_available_languages, get_language_info, set_language
    
    available_langs = get_available_languages()
    
    if language not in available_langs:
        console.print(f"❌ [red]Language '{language}' not available[/red]")
        console.print(f"Available languages: {', '.join(available_langs)}")
        return
    
    # Update environment variable for current session
    os.environ["AUTOPROMO_LANG"] = language
    set_language(language)
    
    lang_info = get_language_info()
    lang_name = lang_info.get(language, language.upper())
    
    console.print(f"✅ [green]Language set to: {lang_name} ({language})[/green]")
    
    # Suggest permanent setup
    console.print("\n[bold]To make this permanent:[/bold]")
    console.print(f"• Add to your shell profile: [cyan]export AUTOPROMO_LANG={language}[/cyan]")
    console.print(f"• Or add to .env file: [cyan]AUTOPROMO_LANG={language}[/cyan]")


@lang_app.command()
def status():
    """Show current language status and configuration."""
    
    console.print(Panel(
        "[bold green]🌍 Language Status[/bold green]",
        border_style="green"
    ))
    
    from ...core.i18n import CURRENT_LANGUAGE, get_language_info, get_available_languages
    
    # Current language info
    lang_info = get_language_info()
    current_name = lang_info.get(CURRENT_LANGUAGE, CURRENT_LANGUAGE.upper())
    
    status_table = Table(title="Language Configuration")
    status_table.add_column("Setting", style="cyan")
    status_table.add_column("Value", style="white")
    
    status_table.add_row("Current Language", f"{current_name} ({CURRENT_LANGUAGE})")
    status_table.add_row("Environment Variable", os.getenv("AUTOPROMO_LANG", "Not set"))
    status_table.add_row("Available Languages", str(len(get_available_languages())))
    
    console.print(status_table)
    
    # Test translation
    console.print("\n[bold]Translation Test:[/bold]")
    from ...core.i18n import _
    
    test_messages = [
        _("welcome_title"),
        _("campaign_created"),
        _("next_steps")
    ]
    
    for msg in test_messages:
        console.print(f"• {msg}")


@lang_app.command()
def demo():
    """Demonstrate AetherPost in different languages."""
    
    console.print(Panel(
        "[bold purple]🎭 Language Demo[/bold purple]",
        border_style="purple"
    ))
    
    from ...core.i18n import get_available_languages, get_language_info, load_translations
    
    available_langs = get_available_languages()
    lang_info = get_language_info()
    
    # Show welcome message in all languages
    for lang_code in available_langs:
        lang_name = lang_info.get(lang_code, lang_code.upper())
        translations = load_translations(lang_code)
        
        welcome_title = translations.get("welcome_title", "Welcome to AetherPost!")
        
        console.print(f"\n[bold cyan]{lang_name} ({lang_code}):[/bold cyan]")
        console.print(f"  {welcome_title}")


@lang_app.command()
def translate(
    key: str = typer.Argument(..., help="Translation key to look up"),
    language: str = typer.Option(None, "--lang", help="Specific language (default: current)"),
):
    """Look up a specific translation key."""
    
    from ...core.i18n import _, CURRENT_LANGUAGE, get_available_languages
    
    target_lang = language or CURRENT_LANGUAGE
    
    if language and language not in get_available_languages():
        console.print(f"❌ [red]Language '{language}' not available[/red]")
        return
    
    translation = _(key, language=target_lang)
    
    console.print(f"[bold]Key:[/bold] {key}")
    console.print(f"[bold]Language:[/bold] {target_lang}")
    console.print(f"[bold]Translation:[/bold] {translation}")
    
    if translation == key:
        console.print("[yellow]⚠️ No translation found (showing key)[/yellow]")


@lang_app.command()
def create(
    language: str = typer.Argument(..., help="Language code to create (e.g., fr, de, es)"),
    from_lang: str = typer.Option("en", "--from", help="Source language to copy from"),
):
    """Create a new language file based on an existing one."""
    
    from ...core.i18n import get_translations_dir, get_available_languages, get_language_info
    
    if language in get_available_languages():
        if not Confirm.ask(f"Language '{language}' already exists. Overwrite?"):
            console.print("Creation cancelled.")
            return
    
    if from_lang not in get_available_languages():
        console.print(f"❌ [red]Source language '{from_lang}' not found[/red]")
        return
    
    # Load source translations
    source_file = get_translations_dir() / f"{from_lang}.json"
    target_file = get_translations_dir() / f"{language}.json"
    
    try:
        import json
        import shutil
        
        # Copy source file to target
        shutil.copy2(source_file, target_file)
        
        lang_info = get_language_info()
        lang_name = lang_info.get(language, language.upper())
        
        console.print(f"✅ [green]Created {lang_name} ({language}) translation file[/green]")
        console.print(f"📄 File: {target_file}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Edit the translation file with appropriate translations")
        console.print("2. Test with: [cyan]aetherpost lang set {language}[/cyan]")
        console.print("3. Validate with: [cyan]aetherpost lang demo[/cyan]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to create language file: {e}[/red]")


@lang_app.command()
def validate(
    language: str = typer.Option(None, "--lang", help="Language to validate (default: all)")
):
    """Validate translation files for completeness."""
    
    console.print(Panel(
        "[bold yellow]🔍 Translation Validation[/bold yellow]",
        border_style="yellow"
    ))
    
    from ...core.i18n import get_available_languages, load_translations
    
    languages_to_check = [language] if language else get_available_languages()
    
    # Load English as reference
    en_translations = load_translations("en")
    en_keys = set(en_translations.keys())
    
    validation_table = Table(title="Translation Completeness")
    validation_table.add_column("Language", style="cyan")
    validation_table.add_column("Complete", style="green")
    validation_table.add_column("Missing", style="red")
    validation_table.add_column("Extra", style="yellow")
    validation_table.add_column("Status", style="white")
    
    for lang in languages_to_check:
        if lang == "en":
            continue  # Skip English (reference)
        
        translations = load_translations(lang)
        lang_keys = set(translations.keys())
        
        missing_keys = en_keys - lang_keys
        extra_keys = lang_keys - en_keys
        complete_keys = en_keys & lang_keys
        
        completion_rate = len(complete_keys) / len(en_keys) * 100 if en_keys else 100
        
        if completion_rate == 100 and not extra_keys:
            status = "✅ Perfect"
        elif completion_rate >= 90:
            status = "🟡 Good"
        elif completion_rate >= 70:
            status = "🟠 Needs work"
        else:
            status = "🔴 Incomplete"
        
        validation_table.add_row(
            lang,
            str(len(complete_keys)),
            str(len(missing_keys)),
            str(len(extra_keys)),
            status
        )
    
    console.print(validation_table)
    
    # Show detailed issues if validating single language
    if language and language != "en":
        translations = load_translations(language)
        lang_keys = set(translations.keys())
        
        missing_keys = en_keys - lang_keys
        extra_keys = lang_keys - en_keys
        
        if missing_keys:
            console.print(f"\n[bold red]Missing keys in {language}:[/bold red]")
            for key in sorted(missing_keys):
                console.print(f"  • {key}")
        
        if extra_keys:
            console.print(f"\n[bold yellow]Extra keys in {language}:[/bold yellow]")
            for key in sorted(extra_keys):
                console.print(f"  • {key}")
        
        if not missing_keys and not extra_keys:
            console.print(f"\n✅ [green]{language} translations are complete![/green]")


@lang_app.command()
def export(
    language: str = typer.Argument(..., help="Language to export"),
    format: str = typer.Option("json", "--format", help="Export format (json, csv, po)"),
    output: str = typer.Option(None, "--output", help="Output file path"),
):
    """Export translations in different formats."""
    
    from ...core.i18n import get_available_languages, load_translations
    
    if language not in get_available_languages():
        console.print(f"❌ [red]Language '{language}' not available[/red]")
        return
    
    translations = load_translations(language)
    
    if not output:
        output = f"autopromo-{language}.{format}"
    
    try:
        if format == "json":
            import json
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            with open(output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Key", "Translation"])
                for key, value in translations.items():
                    writer.writerow([key, value])
        
        elif format == "po":
            # Basic PO format export
            with open(output, 'w', encoding='utf-8') as f:
                f.write(f'# AetherPost translations for {language}\n')
                f.write(f'msgid ""\nmsgstr ""\n')
                f.write(f'"Language: {language}\\n"\n\n')
                
                for key, value in translations.items():
                    f.write(f'msgid "{key}"\n')
                    f.write(f'msgstr "{value}"\n\n')
        
        else:
            console.print(f"❌ [red]Unsupported format: {format}[/red]")
            return
        
        console.print(f"✅ [green]Exported {language} translations to: {output}[/green]")
    
    except Exception as e:
        console.print(f"❌ [red]Export failed: {e}[/red]")