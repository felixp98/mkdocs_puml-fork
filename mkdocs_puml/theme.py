import re
from pathlib import Path
import importlib.resources as resources
from mkdocs_puml.utils import sanitize_url

C4_REGEX = re.compile(r"(!include(?:.+)(?:[Cc]4)(?:.+).puml)")


class Theme:
    """Theme class helps integrate available themes into PlantUML code.

    Theme includes theme url after all C4 inclusions. It makes possible
    to provide custom styling to C4 code as well.

    Args:
        source (str): source type - "url", "local", or "packaged"
        url (str): repository of themes (for url source)
        themes_path (str): path to local themes directory (for local source)
    """

    def __init__(self, source: str = "url", url: str = None, config_file_dir: str|None = None):
        self.source = source
        self.url = sanitize_url(url)
        self.config_file_dir = config_file_dir

    def include(self, theme: str, diagram: str) -> str:
        """Includes theme to the beginning of PlantUML diagram

        Args:
            theme (str): theme name to include
            diagram (str): diagram into which to include

        Returns:
            str: PlantUML diagram with theme included
        """
        injected_diagram = diagram
        if self.source == "url":
            url = self._url_for(theme)
            injected_diagram = self._inject(f"!include {url}", diagram)
        elif self.source == "local":
            theme_content = self._get_local_theme_content(theme)
            if theme_content:
                injected_diagram = self._inject(theme_content, diagram)
        elif self.source == "packaged":
            theme_content = self._get_packaged_theme_content(theme)
            if theme_content:
                injected_diagram = self._inject(theme_content, diagram)
        return injected_diagram

    def _inject(self, inject_content: str, diagram: str) -> str:
        """Inject content into the diagram

        Args:
            inject_content (str): content to inject
            diagram (str): diagram into which to include

        Returns:
            str: diagram with content injected
        """
        diagram = diagram.strip()
        with_c4 = C4_REGEX.split(diagram)

        if len(with_c4) == 1:
            if diagram.startswith("@startuml"):
                head, _, tail = diagram.partition("\n")
            else:
                head, tail = None, diagram

            if head:
                return f"{head}\n{inject_content}\n{tail}"
            return f"{inject_content}\n{tail}"
        else:
            tail = with_c4[-1]
            with_c4[-1] = f"\n{inject_content}"
            with_c4.append(tail)
            return "".join(with_c4)

    def _get_local_theme_content(self, theme: str) -> str:
        """Get theme content from local file path
        
        Args:
            theme (str): name of the theme

        Returns:
            str: content of the theme
        """
        if not self.config_file_dir:
            return None
        
        theme_path = self._get_theme_path(theme)
        
        if theme_path.exists():
            return None

        try:
            return theme_path.read_text(encoding='utf-8')
        except Exception:
            return None

    def _get_packaged_theme_content(self, theme: str) -> str:
        """Get theme content from packaged themes

        Args:
            theme (str): name of the theme

        Returns:
            str: content of the theme
        """
        theme_file = f"themes/{theme}.puml"
        theme_path = resources.files("mkdocs_puml").joinpath(theme_file)
        if theme_path.exists():
            try:
                return theme_path.read_text(encoding='utf-8')
            except Exception:
                return None
        return None

    def _get_theme_path(self, theme: str) -> Path:
        """Get theme path
        
        Args:
            theme (str): name of the theme

        Returns:
            Path: theme path
        """
        theme_path = Path(theme)
        if theme_path.suffix != ".puml":
            theme_path = theme_path.with_suffix(".puml")
        if not theme_path.is_absolute():
            theme_path = Path(self.config_file_dir) / theme_path
        return theme_path

    def _url_for(self, theme: str) -> str:
        """Create full url for theme

        Args:
            theme (str): theme name

        Returns:
            str: full url for theme
        """
        return f"{self.url}{theme}.puml"
