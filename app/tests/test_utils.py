"""
Tests para las utilidades de SQUIT.

Este módulo contiene tests para las funciones auxiliares
y utilidades del sistema.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parent.parent))

from squit_client.utils import (
    filter_important_errors,
    format_number,
    suppress_warnings,
    truncate_text,
    validate_file_path,
)


class TestFormatting:
    """Tests para funciones de formateo."""

    def test_format_number(self):
        """Test formateo de números."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
        assert format_number(0) == "0"

    def test_truncate_text_short(self):
        """Test truncado de texto corto."""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"

    def test_truncate_text_long(self):
        """Test truncado de texto largo."""
        text = "This is a very long text that should be truncated"
        result = truncate_text(text, 20)
        assert result == "This is a very lo..."
        assert len(result) == 20

    def test_truncate_text_exact_length(self):
        """Test truncado con longitud exacta."""
        text = "Exactly twenty chars"  # 20 caracteres
        result = truncate_text(text, 20)
        assert result == text


class TestFileValidation:
    """Tests para validación de archivos."""

    def test_validate_file_path_existing_dir(self):
        """Test validación con directorio existente."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            result = validate_file_path(file_path)
            assert result is True

    def test_validate_file_path_new_dir(self):
        """Test validación creando nuevo directorio."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "new_dir", "test.txt")
            result = validate_file_path(file_path)
            assert result is True
            assert os.path.exists(os.path.dirname(file_path))

    @patch("os.makedirs")
    def test_validate_file_path_permission_error(self, mock_makedirs):
        """Test error de permisos."""
        mock_makedirs.side_effect = PermissionError("Permission denied")

        result = validate_file_path("/invalid/path/file.txt")
        assert result is False


class TestErrorFiltering:
    """Tests para filtrado de errores."""

    def test_filter_important_errors_empty(self):
        """Test filtrado con contenido vacío."""
        result = filter_important_errors("")
        assert result == []

    def test_filter_important_errors_with_excluded(self):
        """Test filtrado excluyendo patrones específicos."""
        stderr_content = """
        Important error message
        ALTS creds ignored. Not running on GCP
        Another important error
        BigQuery Storage module not found
        Critical error here
        """

        result = filter_important_errors(stderr_content)

        # Solo deben quedar los errores importantes
        assert len(result) == 3
        assert any("Important error message" in line for line in result)
        assert any("Another important error" in line for line in result)
        assert any("Critical error here" in line for line in result)

        # Los patrones excluidos no deben estar
        assert not any("ALTS creds ignored" in line for line in result)
        assert not any("BigQuery Storage module" in line for line in result)

    def test_filter_important_errors_no_exclusions(self):
        """Test filtrado sin patrones a excluir."""
        stderr_content = "Error 1\nError 2\nError 3"
        result = filter_important_errors(stderr_content)

        assert len(result) == 3
        assert "Error 1" in result
        assert "Error 2" in result
        assert "Error 3" in result


class TestWarningsSuppression:
    """Tests para supresión de warnings."""

    @patch("warnings.filterwarnings")
    @patch.dict("os.environ", {}, clear=True)
    def test_suppress_warnings(self, mock_filterwarnings):
        """Test configuración de supresión de warnings."""
        suppress_warnings()

        # Verificar que se configuraron los filtros
        assert mock_filterwarnings.called

        # Verificar variables de entorno
        assert os.environ.get("GRPC_VERBOSITY") == "ERROR"
        assert os.environ.get("GLOG_minloglevel") == "3"
        assert os.environ.get("GRPC_TRACE") == ""
