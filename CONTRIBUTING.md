# 🤝 Guía de Contribución - SQUIT

¡Gracias por tu interés en contribuir a SQUIT! Este documento te guiará en el proceso.

---

## 🎯 Filosofía del Proyecto

**SQUIT** democratiza el acceso al conocimiento enterrado en código SQL legacy. Priorizamos:

1. **Accesibilidad**: Código comprensible para todos los niveles
2. **Documentación**: Código bien documentado y auto-explicativo  
3. **Performance**: Escalable a millones de objetos
4. **Type Safety**: Type hints en todo el código Python

---

## 🚀 Quick Start para Contribuir

### 1. Fork y Clonar

```bash
# Fork en GitHub, luego:
git clone https://github.com/grupodeacero/squit.git
cd squit
```

### 2. Setup del Entorno

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
cp .env.template .env
# Editar .env con tus credenciales
```

### 3. Crear Branch

```bash
git checkout -b feature/tu-feature
# o
git checkout -b fix/tu-bugfix
```

### 4. Hacer Cambios

Sigue las [convenciones de código](#-convenciones-de-código) de abajo.

### 5. Commit

```bash
git add .
git commit -m "feat: descripción corta del cambio"
```

Tipos de commit:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo (sin cambios de lógica)
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Mantenimiento

### 6. Push y Pull Request

```bash
git push origin feature/tu-feature
```

Luego abre un Pull Request en GitHub.

---

## 📋 Convenciones de Código

### Python Style

```python
def function_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Descripción breve de la función.
    
    Args:
        param1: Descripción del parámetro.
        param2: Descripción del parámetro.
        
    Returns:
        Descripción del valor de retorno.
        
    Example:
        >>> result = function_name("test", 42)
    """
    pass
```

**Reglas:**
- ✅ Type hints obligatorios
- ✅ Docstrings estilo Google en funciones públicas
- ✅ Black para formateo (max 100 chars)
- ✅ isort para imports
- ✅ Nombres descriptivos (snake_case)

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# NO usar print() en código de producción
# SÍ usar logging
logger.info("Mensaje informativo")
logger.error("Error: %s", error_message)
```

### Configuración

```python
# NO hardcodear valores
api_key = "hardcoded_key"  # ❌

# SÍ usar config o .env
api_key = os.getenv("GEMINI_API_KEY")  # ✅
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
python -m pytest

# Tests específicos
python -m pytest tests/test_memory.py

# Con coverage
python -m pytest --cov=app tests/
```

**Agregar tests para:**
- ✅ Nuevas funcionalidades
- ✅ Bugs corregidos  
- ✅ Edge cases

---

## 📚 Documentación

### Actualizar Docs

Si tu cambio afecta la funcionalidad:

1. Actualizar [docs/INDEX.md](docs/INDEX.md) si es necesario
2. Agregar ejemplos en [docs/usage/EXAMPLES.md](docs/usage/EXAMPLES.md)
3. Documentar en docstrings

### Crear Nueva Documentación

Coloca docs en la carpeta apropiada:
- `docs/setup/` - Configuración y pipeline
- `docs/usage/` - Guías de uso
- `docs/development/` - Arquitectura y desarrollo

---

## 🐛 Reportar Bugs

### Usar GitHub Issues

Incluye:
1. **Descripción** del bug
2. **Pasos para reproducir**
3. **Comportamiento esperado** vs **real**
4. **Environment** (OS, Python version, etc.)
5. **Logs** si están disponibles

### Template de Issue

```markdown
## Descripción
Breve descripción del bug

## Pasos para Reproducir
1. Ejecutar `python scripts/squit.py`
2. Hacer query "..."
3. Ver error

## Comportamiento Esperado
Debería devolver...

## Comportamiento Real
Devuelve error...

## Environment
- OS: macOS 14.0
- Python: 3.11.5
- SQUIT version: 2.1.0
```

---

## ✨ Proponer Features

### Usar GitHub Discussions

Antes de implementar features grandes:

1. Abre un Discussion en GitHub
2. Describe el problema que resuelve
3. Propón solución
4. Espera feedback de maintainers

### Criterios para Aceptación

- ✅ Resuelve problema real
- ✅ Mantiene filosofía del proyecto
- ✅ No rompe funcionalidad existente
- ✅ Está bien documentado
- ✅ Tiene tests

---

## 📋 Checklist antes de PR

- [ ] Código sigue convenciones del proyecto
- [ ] Type hints agregados
- [ ] Docstrings actualizados
- [ ] Tests agregados y pasando
- [ ] Documentación actualizada
- [ ] No hay credenciales hardcodeadas
- [ ] Commit messages son descriptivos

---

## 🔍 Code Review

### Qué Esperamos

- **Constructivo**: Feedback para mejorar, no criticar
- **Específico**: Señalar líneas concretas
- **Propositivo**: Sugerir alternativas

### Qué Revisamos

- ✅ Lógica y corrección
- ✅ Estilo y convenciones
- ✅ Performance
- ✅ Seguridad
- ✅ Documentación

---

## 🎓 Recursos

- **[Documentación](docs/INDEX.md)**: Índice completo
- **[Architecture](docs/development/SYSTEM_OVERVIEW.md)**: Arquitectura del sistema
- **[API Reference](docs/usage/API.md)**: Referencias de APIs
- **[Python Style Guide](https://google.github.io/styleguide/pyguide.html)**: Google Style Guide

---

## 📬 Contacto

- **Issues**: [GitHub Issues](https://github.com/grupodeacero/squit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/grupodeacero/squit/discussions)
- **Email**: ktouma@deacero.com

---

## 🙏 Reconocimientos

Todos los contributors serán agregados a [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

**¡Gracias por ayudar a democratizar el conocimiento legacy!** 🎯
